import os
import re
import json
import time
import threading
import shutil
from queue import Queue
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import SCANVAULT_FOLDER, QUARANTINE_FOLDER
from Scanning.scanner_core import scan_file_for_realtime, force_scan_vaulted
from Scanning.quarantine import quarantine_file
from utils.logger import log_message, telemetry_inc
from utils.notify import notify_app, notify
from config import POST_RESTORE_RECHECK_DELAY


class ScanVaultProcessor:
    """Background processor for ScanVault files using FIFO scanning."""
    
    def __init__(self, monitor_page_ref=None):
        self.monitor_page = monitor_page_ref
        self.scan_queue = Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the background scanning thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        log_message("[SCANVAULT] Background processor started")
        
    def stop(self):
        """Stop the background scanning thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        log_message("[SCANVAULT] Background processor stopped")
        
    def enqueue_for_scan(self, vaulted_path: str, meta_path: str):
        """Add a vaulted file to the scan queue."""
        self.scan_queue.put((vaulted_path, meta_path))
        
    def _process_loop(self):
        """Main processing loop - scans vaulted files and routes them."""
        while self._running:
            try:
                # Get next file from queue (blocks with timeout)
                try:
                    vaulted_path, meta_path = self.scan_queue.get(timeout=1.0)
                except:
                    continue
                    
                if not os.path.exists(vaulted_path) or not os.path.exists(meta_path):
                    log_message(f"[SCANVAULT] File or metadata missing: {vaulted_path}")
                    continue
                    
                # Load metadata to get original path
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    original_path = metadata.get('original_path')
                    installer_mode = metadata.get('installer_mode', False)
                    if not original_path:
                        log_message(f"[SCANVAULT] No original path in metadata: {meta_path}")
                        continue
                except Exception as e:
                    log_message(f"[SCANVAULT] Failed to read metadata {meta_path}: {e}")
                    continue
                    
                # Scan the vaulted file
                log_message(f"[SCANVAULT] Scanning: {vaulted_path}")
                # Use forced scan to avoid INTERNAL exclusion regression
                result = force_scan_vaulted(vaulted_path)
                matched, rule, _, _ = result[:4]
                status = getattr(result, 'status', 'UNKNOWN')
                # If installer_mode, schedule delayed sweep of original path
                if installer_mode and original_path:
                    def delayed_sweep():
                        time.sleep(60)
                        try:
                            log_message(f"[SCANVAULT] Delayed sweep scan (installer): {original_path}")
                            sweep_result = scan_file_for_realtime(original_path)
                            matched2, rule2, file_path2, meta_path2 = sweep_result[:4]
                            if matched2 and meta_path2:
                                notify_app("Installer sweep threat detected!", f"RULE: {rule2}\nPath: {file_path2}", severity="critical", duration_ms=3200)
                                log_message(f"[SCANVAULT] Installer sweep threat quarantined: {file_path2}")
                        except Exception as e:
                            log_message(f"[SCANVAULT] Delayed sweep error: {e}")
                    threading.Thread(target=delayed_sweep, daemon=True).start()
                
                # Prepare history directory for metadata archive
                history_dir = os.path.join(SCANVAULT_FOLDER, "history")
                os.makedirs(history_dir, exist_ok=True)

                if matched:
                    # Malware detected - move to quarantine
                    try:
                        quarantine_path = quarantine_file(vaulted_path, matched_rules=[rule])
                        # Archive vault metadata into history with status
                        if os.path.exists(meta_path):
                            try:
                                with open(meta_path, 'r', encoding='utf-8') as f:
                                    meta = json.load(f)
                            except Exception:
                                meta = {}
                            meta.update({
                                'final_status': 'QUARANTINED',
                                'action_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'quarantine_path': quarantine_path,
                                'matched_rule': rule,
                            })
                            # Move to history directory
                            base = os.path.basename(meta_path)
                            history_meta = os.path.join(history_dir, base)
                            try:
                                with open(history_meta, 'w', encoding='utf-8') as f:
                                    json.dump(meta, f, indent=4)
                            except Exception as e:
                                log_message(f"[SCANVAULT] Failed to write history meta: {e}")
                            try:
                                os.remove(meta_path)
                            except Exception:
                                pass
                        log_message(f"[SCANVAULT] Threat quarantined: {vaulted_path} -> {quarantine_path}")
                        try:
                            notify_app("Threat quarantined", f"{os.path.basename(original_path)}\nRule: {rule}", severity="critical", duration_ms=3200)
                        except Exception:
                            pass
                        
                        # Update UI
                        if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                            quarantine_meta = quarantine_path + ".meta"
                            self.monitor_page.add_to_quarantine_listbox(original_path, quarantine_meta, [rule])
                        # Refresh vault UI (history now updated)
                        self._schedule_ui_update(lambda: getattr(self.monitor_page, 'refresh_scanvault_table', self.monitor_page.update_scanvault_listbox)())
                            
                    except Exception as e:
                        log_message(f"[SCANVAULT] Quarantine failed for {vaulted_path}: {e}")
                        
                elif status in ('CLEAN', 'SKIPPED_INTERNAL', 'SKIPPED_TEMP', 'SKIPPED_TEMP_ROOT', 'SKIPPED_TEMP_FILE'):
                    # File is clean - restore to original location
                    try:
                        # Compute pre-restore hash of the vaulted content
                        pre_hash = self._sha256_file(vaulted_path)
                        # Double-check: run one more scan right before restore to avoid races
                        recheck = force_scan_vaulted(vaulted_path)
                        if getattr(recheck, 'matched', False):
                            # If match now, treat like threat path
                            rule2 = recheck.rule
                            try:
                                quarantine_path = quarantine_file(vaulted_path, matched_rules=[rule2])
                                # Update history meta
                                if os.path.exists(meta_path):
                                    try:
                                        with open(meta_path, 'r', encoding='utf-8') as f:
                                            meta = json.load(f)
                                    except Exception:
                                        meta = {}
                                    meta.update({
                                        'final_status': 'QUARANTINED',
                                        'action_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'quarantine_path': quarantine_path,
                                        'matched_rule': rule2,
                                        'recheck_before_restore': True
                                    })
                                    base = os.path.basename(meta_path)
                                    history_meta = os.path.join(history_dir, base)
                                    with open(history_meta, 'w', encoding='utf-8') as f:
                                        json.dump(meta, f, indent=4)
                                    try:
                                        os.remove(meta_path)
                                    except Exception:
                                        pass
                                log_message(f"[SCANVAULT] Re-check caught threat, quarantined: {vaulted_path}")
                                try:
                                    notify_app("Threat quarantined", f"{os.path.basename(original_path)}\nRule: {rule2}", severity="critical", duration_ms=3200)
                                except Exception:
                                    pass
                            except Exception as qe2:
                                log_message(f"[SCANVAULT] Re-check quarantine failed: {qe2}")
                            # Skip normal restore path
                            continue
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)
                        
                        # Move back to original location and capture the real restored path
                        # Note: shutil.move returns the actual destination path. We use it to
                        # handle cases where the OS/filesystem resolves duplicates or performs
                        # slight normalization, ensuring our rechecks target the right file.
                        restored_path = shutil.move(vaulted_path, original_path)
                        
                        # Archive vault metadata with status
                        if os.path.exists(meta_path):
                            try:
                                with open(meta_path, 'r', encoding='utf-8') as f:
                                    meta = json.load(f)
                            except Exception:
                                meta = {}
                            meta.update({
                                'final_status': 'RESTORED',
                                'action_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'restored_path': restored_path,
                                'pre_restore_hash': pre_hash,
                                'recheck_before_restore': False
                            })
                            base = os.path.basename(meta_path)
                            history_meta = os.path.join(history_dir, base)
                            try:
                                with open(history_meta, 'w', encoding='utf-8') as f:
                                    json.dump(meta, f, indent=4)
                            except Exception as e:
                                log_message(f"[SCANVAULT] Failed to write history meta: {e}")
                            try:
                                os.remove(meta_path)
                            except Exception:
                                pass
                            
                        log_message(f"[SCANVAULT] Clean file restored: {vaulted_path} -> {restored_path}")
                        # Immediate recheck at the restored path (fast safety net)
                        try:
                            self._immediate_post_restore_recheck(restored_path, pre_hash)
                        except Exception:
                            pass
                        # Friendly toast on clean restore
                        try:
                            notify_app("Clean file restored", os.path.basename(restored_path), severity="success", duration_ms=4200)
                        except Exception:
                            pass
                        # Schedule multiple second-chance rechecks to catch delayed content flips
                        try:
                            self._schedule_multi_post_restore_rechecks(restored_path, pre_hash)
                        except Exception:
                            pass
                        
                        # Refresh vault UI (history now updated)
                        self._schedule_ui_update(lambda: getattr(self.monitor_page, 'refresh_scanvault_table', self.monitor_page.update_scanvault_listbox)())
                        
                    except Exception as e:
                        log_message(f"[SCANVAULT] Restore failed for {vaulted_path}: {e}")
                        
                else:
                    # Scan error - leave in vault for manual review
                    log_message(f"[SCANVAULT] Scan error ({status}), leaving in vault: {vaulted_path}")
                    
            except Exception as e:
                log_message(f"[SCANVAULT] Processing error: {e}")
                time.sleep(1)
                
    def _schedule_ui_update(self, update_func):
        """Schedule a UI update in the main thread."""
        if self.monitor_page and hasattr(self.monitor_page, 'root'):
            try:
                self.monitor_page.root.after(0, update_func)
            except:
                pass
    
    def _schedule_post_restore_recheck(self, original_path: str, delay: int = POST_RESTORE_RECHECK_DELAY, pre_hash: str | None = None):
        def _worker():
            try:
                time.sleep(delay)
                if not os.path.exists(original_path):
                    # Try sibling sweep for duplicate style names like " (1)"
                    matched_via_sibling = self._sibling_sweep_and_scan(original_path, pre_hash)
                    if matched_via_sibling:
                        return
                    telemetry_inc('recheck_missing_post_restore')
                    return
                # Re-scan the original file in place (non-intrusive)
                # Hash guard: quarantine if content changed since pre-restore
                if pre_hash:
                    now_hash = self._sha256_file(original_path)
                    if now_hash and now_hash != pre_hash:
                        try:
                            quarantine_path = quarantine_file(original_path, matched_rules=['HASH_GUARD_CHANGE'])
                            log_message(f"[SCANVAULT] Hash guard quarantined (delayed): {original_path}")
                            try:
                                notify_app("Hash Guard quarantined", os.path.basename(original_path), severity="critical", duration_ms=3200)
                            except Exception:
                                pass
                            telemetry_inc('hash_guard_quarantined_on_change')
                            if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                                try:
                                    self.monitor_page.add_to_quarantine_listbox(original_path, quarantine_path + '.meta', ['HASH_GUARD_CHANGE'])
                                except Exception:
                                    pass
                            return
                        except Exception as qe:
                            log_message(f"[SCANVAULT] Hash guard quarantine failed (delayed): {qe}")
                            telemetry_inc('hash_guard_error')
                result = scan_file_for_realtime(original_path)
                matched, rule, quarantined_path, meta_path = result[:4]
                if matched:
                    log_message(f"[SCANVAULT] Post-restore recheck matched, quarantined: {original_path}")
                    telemetry_inc('recheck_match_post_restore')
                    # Update UI if available
                    if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                        try:
                            self.monitor_page.add_to_quarantine_listbox(quarantined_path, meta_path, [rule])
                        except Exception:
                            pass
                else:
                    telemetry_inc('recheck_clean_post_restore')
            except Exception as e:
                log_message(f"[SCANVAULT] Post-restore recheck error for {original_path}: {e}")
                telemetry_inc('recheck_error_post_restore')
        threading.Thread(target=_worker, daemon=True).start()

    def _immediate_post_restore_recheck(self, restored_path: str, pre_hash: str | None = None):
        """Run a quick, immediate re-scan on the restored file path.

        Adds a tiny stabilization loop to avoid scanning while the file is still
        being finalized by external processes. If a match is found, the function
        relies on scan_file_for_realtime to quarantine the file.
        """
        try:
            # Quick stabilization: wait until size stops changing or 3 attempts
            if not os.path.exists(restored_path):
                # Try sibling sweep for duplicate-named variants
                matched_via_sibling = self._sibling_sweep_and_scan(restored_path, pre_hash)
                if not matched_via_sibling:
                    telemetry_inc('recheck_immediate_missing_post_restore')
                return
            last_size = -1
            delay = 0.15
            for _ in range(6):  # up to ~1.2s total wait
                try:
                    sz = os.path.getsize(restored_path)
                except OSError:
                    sz = -1
                if sz == last_size and sz > 0:
                    break
                last_size = sz
                time.sleep(delay)
                delay = min(delay * 1.6, 0.6)

            # Hash guard: if content changed vs pre-restore, quarantine immediately
            if pre_hash:
                now_hash = self._sha256_file(restored_path)
                if now_hash and now_hash != pre_hash:
                    try:
                        quarantine_path = quarantine_file(restored_path, matched_rules=['HASH_GUARD_CHANGE'])
                        log_message(f"[SCANVAULT] Hash guard quarantined (immediate): {restored_path}")
                        try:
                            notify_app("Hash Guard quarantined", os.path.basename(restored_path), severity="critical", duration_ms=3200)
                        except Exception:
                            pass
                        telemetry_inc('hash_guard_quarantined_on_change')
                        if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                            try:
                                self.monitor_page.add_to_quarantine_listbox(quarantine_path, quarantine_path + '.meta', ['HASH_GUARD_CHANGE'])
                            except Exception:
                                pass
                        return
                    except Exception as qe:
                        log_message(f"[SCANVAULT] Hash guard quarantine failed (immediate): {qe}")
                        telemetry_inc('hash_guard_error')

            result = scan_file_for_realtime(restored_path)
            matched, rule, quarantined_path, meta_path = result[:4]
            if matched:
                log_message(f"[SCANVAULT] Immediate post-restore recheck matched, quarantined: {restored_path}")
                telemetry_inc('recheck_immediate_match_post_restore')
                try:
                    notify_app("Threat quarantined", os.path.basename(restored_path), severity="critical", duration_ms=3200)
                except Exception:
                    pass
                if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                    try:
                        self.monitor_page.add_to_quarantine_listbox(quarantined_path, meta_path, [rule])
                    except Exception:
                        pass
            else:
                telemetry_inc('recheck_immediate_clean_post_restore')
        except Exception as e:
            log_message(f"[SCANVAULT] Immediate post-restore recheck error for {restored_path}: {e}")
            telemetry_inc('recheck_immediate_error_post_restore')

    def _schedule_multi_post_restore_rechecks(self, path: str, pre_hash: str | None = None):
        """Schedule multiple delayed rechecks for better coverage.

        We trigger rechecks roughly at 1s, 4s, and 10s to catch late writes
        or background modifications.
        """
        for d in (1, POST_RESTORE_RECHECK_DELAY, max(POST_RESTORE_RECHECK_DELAY * 2 + 2, 10)):
            try:
                self._schedule_post_restore_recheck(path, delay=d, pre_hash=pre_hash)
                telemetry_inc('recheck_scheduled_post_restore')
            except Exception:
                pass

    def _sibling_sweep_and_scan(self, target_path: str, pre_hash: str | None = None) -> bool:
        """Look for duplicate-named siblings like 'name (1).ext' and scan them.

        Returns True if any sibling resulted in a quarantine match, or if a clean
        scan was performed (still useful). False if nothing was scanned.
        """
        try:
            directory = os.path.dirname(target_path)
            if not directory or not os.path.isdir(directory):
                return False
            base = os.path.basename(target_path)
            name, ext = os.path.splitext(base)
            # Build a regex that matches 'name.ext' and 'name (N).ext'
            # Escape name to avoid regex surprises
            name_escaped = re.escape(name)
            pattern = re.compile(rf"^{name_escaped}( \(\d+\))?{re.escape(ext)}$", re.IGNORECASE)
            candidates = [os.path.join(directory, f) for f in os.listdir(directory) if pattern.match(f)]
            if not candidates:
                return False
            any_scanned = False
            for path in candidates:
                if not os.path.isfile(path):
                    continue
                any_scanned = True
                # Hash guard first
                if pre_hash:
                    now_hash = self._sha256_file(path)
                    if now_hash and now_hash != pre_hash:
                        try:
                            quarantine_path = quarantine_file(path, matched_rules=['HASH_GUARD_CHANGE'])
                            log_message(f"[SCANVAULT] Sibling sweep hash-guard quarantined: {path}")
                            try:
                                notify_app("Hash Guard quarantined", os.path.basename(path), severity="critical", duration_ms=3200)
                            except Exception:
                                pass
                            telemetry_inc('hash_guard_quarantined_on_change')
                            if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                                try:
                                    self.monitor_page.add_to_quarantine_listbox(quarantine_path, quarantine_path + '.meta', ['HASH_GUARD_CHANGE'])
                                except Exception:
                                    pass
                            return True
                        except Exception as qe:
                            log_message(f"[SCANVAULT] Hash guard quarantine failed (sibling): {qe}")
                            telemetry_inc('hash_guard_error')
                result = scan_file_for_realtime(path)
                matched, rule, quarantined_path, meta_path = result[:4]
                if matched:
                    log_message(f"[SCANVAULT] Sibling sweep matched, quarantined: {path}")
                    telemetry_inc('recheck_sibling_sweep_match_post_restore')
                    if self.monitor_page and hasattr(self.monitor_page, 'add_to_quarantine_listbox'):
                        try:
                            self.monitor_page.add_to_quarantine_listbox(quarantined_path, meta_path, [rule])
                        except Exception:
                            pass
                    return True
            if any_scanned:
                telemetry_inc('recheck_sibling_sweep_clean_post_restore')
            return False
        except Exception as e:
            log_message(f"[SCANVAULT] Sibling sweep error for {target_path}: {e}")
            telemetry_inc('recheck_sibling_sweep_error_post_restore')
            return False

    # Utilities
    def _sha256_file(self, path: str) -> str | None:
        try:
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None
                
    def get_queue_size(self) -> int:
        """Get current queue size for monitoring."""
        return self.scan_queue.qsize()


# Global processor instance
_vault_processor: Optional[ScanVaultProcessor] = None

def get_vault_processor() -> ScanVaultProcessor:
    """Get or create the global vault processor."""
    global _vault_processor
    if _vault_processor is None:
        _vault_processor = ScanVaultProcessor()
    return _vault_processor

def start_vault_processor(monitor_page_ref=None):
    """Start the vault processor with monitor page reference."""
    processor = get_vault_processor()
    if monitor_page_ref:
        processor.monitor_page = monitor_page_ref
    processor.start()
    
def stop_vault_processor():
    """Stop the vault processor."""
    global _vault_processor
    if _vault_processor:
        _vault_processor.stop()