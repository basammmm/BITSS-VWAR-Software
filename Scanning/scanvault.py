import os
import shutil
import json
import hashlib
import time
from typing import Tuple
from datetime import datetime

from config import SCANVAULT_FOLDER
from utils.logger import log_message, telemetry_inc
from utils.installation_mode import get_installation_mode


_recent_signatures: dict[str, float] = {}
_SIGNATURE_TTL = 15.0  # seconds window to treat repeated captures as duplicates

def _first64k_hash(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            chunk = f.read(65536)
        h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return "0" * 16

def _make_signature(path: str) -> str:
    """Generate a richer signature to distinguish rapid repeat downloads.

    Components:
      - file size
      - high resolution mtime (ns if available)
      - first 64KB content hash (prefix)
      - stable path hash (lowercased absolute path)
    """
    try:
        st = os.stat(path)
        size = st.st_size
        # Use nanosecond mtime if available for better granularity
        mtime_ns = getattr(st, 'st_mtime_ns', int(st.st_mtime * 1e9))
    except Exception:
        size = -1
        mtime_ns = 0
    path_norm = os.path.abspath(path).replace("\\", "/").lower()
    path_hash = hashlib.sha256(path_norm.encode()).hexdigest()[:12]
    head_hash = _first64k_hash(path)
    raw = f"{size}|{mtime_ns}|{head_hash}|{path_hash}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]

def vault_capture_file(file_path: str, event: str | None = None) -> Tuple[str, str]:
    """
    Move a new/changed file into the ScanVault folder and write a .meta file.

    Returns (vaulted_path, meta_path).
    Raises RuntimeError on failure.
    """
    if not os.path.exists(file_path):
        raise RuntimeError(f"File no longer exists: {file_path}")
    
    # Check installation mode - skip if installer file
    install_mode = get_installation_mode()
    if install_mode.should_skip_file(file_path):
        raise RuntimeError(f"Skipped by installation mode: {file_path}")

    os.makedirs(SCANVAULT_FOLDER, exist_ok=True)

    try:
        # Dedupe check using enhanced signature
        sig = _make_signature(file_path)
        now = time.time()
        # Purge expired signatures
        expired = [k for k, t in _recent_signatures.items() if now - t > _SIGNATURE_TTL]
        for k in expired:
            _recent_signatures.pop(k, None)
        if sig in _recent_signatures:
            # Instead of silent suppression, create a visible history meta entry
            os.makedirs(SCANVAULT_FOLDER, exist_ok=True)
            history_dir = os.path.join(SCANVAULT_FOLDER, 'history')
            os.makedirs(history_dir, exist_ok=True)
            timestamp_raw = datetime.now()
            timestamp_human = timestamp_raw.strftime("%Y-%m-%d %H:%M:%S")
            base_name = os.path.basename(file_path)
            meta_stub = f"duplicate__{sig[:12]}__{timestamp_raw.strftime('%Y%m%d%H%M%S')}.meta"
            history_meta = os.path.join(history_dir, meta_stub)
            try:
                meta = {
                    "original_path": os.path.abspath(file_path).replace('\\', '/'),
                    "timestamp": timestamp_human,
                    "final_status": "DUPLICATE_SUPPRESSED",
                    "signature": sig,
                    "file_name": base_name,
                    "event": event or "created"
                }
                with open(history_meta, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, indent=4)
                log_message(f"[SCANVAULT] Duplicate suppressed (visible) sig={sig} path={file_path}")
                try:
                    telemetry_inc("duplicate_suppressed")
                except Exception:
                    pass
            except Exception as de:
                log_message(f"[SCANVAULT] Failed to write duplicate meta: {de}")
            raise RuntimeError(f"Duplicate capture suppressed for signature {sig}")

        file_name = os.path.basename(file_path)
        timestamp_raw = datetime.now()
        timestamp_file = timestamp_raw.strftime("%Y%m%d%H%M%S")
        timestamp_human = timestamp_raw.strftime("%Y-%m-%d %H:%M:%S")
        # Normalize path before hashing for stability across dev/EXE
        normalized_path_for_hash = os.path.abspath(file_path).replace("\\", "/")
        path_hash = hashlib.sha256(normalized_path_for_hash.encode()).hexdigest()[:16]

        vaulted_filename = f"{file_name}__{timestamp_file}__{path_hash}.vaulted"
        vaulted_path = os.path.join(SCANVAULT_FOLDER, vaulted_filename)

        # Extended retry logic with backoff to handle transient locks (WinError 32)
        attempts = 10
        delay = 0.15
        last_err = None
        for attempt in range(1, attempts + 1):
            if not os.path.exists(file_path):
                time.sleep(0.1)
                continue
            try:
                shutil.move(file_path, vaulted_path)
                last_err = None
                break
            except Exception as e:
                last_err = e
                time.sleep(delay)
                delay = min(delay * 1.5, 1.2)
        if last_err is not None:
            raise RuntimeError(f"Move failed after {attempts} attempts: {last_err}")

        if os.path.exists(vaulted_path):
            meta_path = vaulted_path + ".meta"
            normalized_path = os.path.abspath(file_path).replace("\\", "/")
            metadata = {
                "original_path": normalized_path,
                "vaulted_path": vaulted_path,
                "timestamp": timestamp_human,
                "event": (event or "created"),
                "signature": sig,
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)
            _recent_signatures[sig] = now
            log_message(f"[SCANVAULT] {file_path} → {vaulted_path}")
            try:
                telemetry_inc("stabilized_capture")
            except Exception:
                pass
            return vaulted_path, meta_path
        else:
            raise RuntimeError(f"Vaulted file unexpectedly missing: {vaulted_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to vault {file_path}: {e}")
