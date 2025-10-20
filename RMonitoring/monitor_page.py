import os
import re
import json
import time
import threading
from tkinter import Frame, Label, Button, Listbox, Scrollbar, Text, StringVar, filedialog, Toplevel, messagebox
from RMonitoring.real_time_monitor import RealTimeMonitor
from utils.notify import notify as notify_user
from utils.tooltip import Tooltip
from utils.logger import log_message
from config import QUARANTINE_FOLDER, SCANVAULT_FOLDER
from Scanning.vault_processor import start_vault_processor, stop_vault_processor, get_vault_processor

class MonitorPage(Frame):
    def __init__(self, root, app_main, switch_page_callback):
        super().__init__(root, bg="#009AA5")
        self.root = root
        self.app_main = app_main  # VWARScannerGUI instance
        self.switch_page_callback = switch_page_callback

        self.display_index_to_meta = {}
        self.vault_index_to_meta = {}
        self.monitoring_active = False
        self.real_time_monitor = None
        self.auto_scan_button_text = StringVar(value="Start Auto Scanning")

        self.quarantine_folder = QUARANTINE_FOLDER
        self.scanvault_folder = SCANVAULT_FOLDER

        # Start ScanVault processor (always active)
        start_vault_processor(monitor_page_ref=self)

        self.setup_gui()

    def setup_gui(self):
        # Top bar
        Button(self, text="Back", command=lambda: self.switch_page_callback("home"),
               bg="red", fg="white", font=("Inter", 12)).place(x=10, y=10, width=80, height=30)
        Label(self, text="Auto Scanning", font=("Inter", 16, "bold"),
              bg="#009AA5", fg="white").place(x=400, y=10)

        # ---- ScanVault (top-left) ----
        Label(self, text="ScanVault (captured files)", font=("Inter", 12, "bold"),
              bg="#009AA5", fg="white").place(x=20, y=60)
        self.scanvault_listbox = Listbox(self, font=("Inter", 10))
        self.scanvault_listbox.place(x=20, y=90, width=950, height=150)
        yscroll_v = Scrollbar(self, orient="vertical", command=self.scanvault_listbox.yview)
        yscroll_v.place(x=970, y=90, height=150)
        self.scanvault_listbox.config(yscrollcommand=yscroll_v.set)
        self.scanvault_listbox.bind("<<ListboxSelect>>", self.on_select_vault)
        Button(self, text="Refresh Vault", command=self.update_scanvault_listbox,
               bg="#006666", fg="white", font=("Inter", 10)).place(x=20, y=255, width=120, height=25)
        Button(self, text="Delete Selected", command=self.delete_selected_vault,
               bg="#B22222", fg="white", font=("Inter", 10)).place(x=150, y=255, width=120, height=25)
        Button(self, text="Clear History", command=self.clear_vault_history,
               bg="#555577", fg="white", font=("Inter", 10)).place(x=280, y=255, width=120, height=25)

        # ---- Divider ----
        Label(self, text="", bg="#009AA5").place(x=20, y=285, width=950, height=2)

        # ---- Quarantine (bottom-left) ----
        Label(self, text="Quarantined Files", font=("Inter", 12, "bold"),
              bg="#009AA5", fg="white").place(x=20, y=310)
        self.quarantine_listbox = Listbox(self, font=("Inter", 10))
        self.quarantine_listbox.place(x=20, y=340, width=500, height=130)
        yscroll = Scrollbar(self, orient="vertical", command=self.quarantine_listbox.yview)
        yscroll.place(x=520, y=340, height=130)
        self.quarantine_listbox.config(yscrollcommand=yscroll.set)
        self.quarantine_listbox.bind("<<ListboxSelect>>", self.on_select)

        # ---- Metadata (right side) ----
        Label(self, text="Quarantine Metadata", font=("Inter", 12, "bold"),
              bg="#009AA5", fg="white").place(x=550, y=310)
        self.quarantine_detail_text = Text(self, font=("Inter", 11), wrap="word", state="disabled",
                                           bg="white", fg="black")
        self.quarantine_detail_text.place(x=550, y=340, width=420, height=130)

     # ---- Quarantine actions ----
        Button(self, text="Refresh Quarantine", command=self.update_quarantine_listbox,
            bg="#006666", fg="white", font=("Inter", 10)).place(x=20, y=480, width=180, height=25)
        Button(self, text="Delete Selected", command=self.delete_selected,
            bg="#B22222", fg="white", font=("Inter", 10)).place(x=210, y=480, width=120, height=25)
        Button(self, text="Restore from Backup", command=self.restore_quarantined_file,
            bg="blue", fg="white", font=("Inter", 10)).place(x=340, y=480, width=160, height=25)

        # ---- Auto scan controls ----
        Button(self, textvariable=self.auto_scan_button_text, command=self.toggle_monitoring,
               bg="#004953", fg="white", font=("Inter", 12, "bold")).place(x=20, y=520, width=220, height=32)
        self.auto_scan_status_label = Label(self, text="Status: Stopped",
                                            font=("Inter", 12, "bold"), bg="#FFFFFF", fg="red")
        self.auto_scan_status_label.place(x=260, y=524)

        # Initial population
        self.update_quarantine_listbox()
        self.update_scanvault_listbox()

    # ---------------- Monitoring Controls ----------------
    def toggle_monitoring(self):
        if self.monitoring_active:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        if self.monitoring_active:
            return
        try:
            # Start the C++ realtime monitor and pipe
            if self.real_time_monitor is None:
                self.real_time_monitor = RealTimeMonitor(self)
            self.real_time_monitor.start_cpp_monitor_engine()

            self.monitoring_active = True
            self.auto_scan_button_text.set("Stop Auto Scanning")
            try:
                self.auto_scan_status_label.config(text="Status: Running", fg="green")
            except Exception:
                pass
            log_message("[MONITOR] Real-time monitoring started")
            try:
                notify_user("VWAR", "Auto scanning is running")
            except Exception:
                pass
        except Exception as e:
            log_message(f"[ERROR] Failed to start monitoring: {e}")

    def stop_monitoring(self):
        if not self.monitoring_active:
            return
        try:
            if self.real_time_monitor:
                try:
                    self.real_time_monitor.stop_cpp_monitor_engine()
                except Exception:
                    pass
            self.monitoring_active = False
            self.auto_scan_button_text.set("Start Auto Scanning")
            try:
                self.auto_scan_status_label.config(text="Status: Stopped", fg="red")
            except Exception:
                pass
            log_message("[MONITOR] Real-time monitoring stopped")
            try:
                notify_user("VWAR", "Auto scanning stopped")
            except Exception:
                pass
        except Exception as e:
            log_message(f"[ERROR] Failed to stop monitoring: {e}")

    def on_select(self, event):
        index = self.quarantine_listbox.curselection()
        if not index:
            # clear panel when nothing selected
            self.quarantine_detail_text.config(state="normal")
            self.quarantine_detail_text.delete("1.0", "end")
            self.quarantine_detail_text.config(state="disabled")
            return
        meta_path = self.display_index_to_meta.get(index[0])
        if not meta_path or not os.path.exists(meta_path):
            return
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            detail_text = (
                f"Original Path:\n{metadata.get('original_path', 'Unknown')}\n\n"
                f"Quarantined At:\n{metadata.get('timestamp', 'Unknown')}\n\n"
                f"Matched Rules:\n{', '.join(metadata.get('matched_rules', []))}"
            )
        except Exception as e:
            detail_text = f"Failed to load metadata:\n{e}"
        self.quarantine_detail_text.config(state="normal")
        self.quarantine_detail_text.delete("1.0", "end")
        self.quarantine_detail_text.insert("end", detail_text)
        self.quarantine_detail_text.config(state="disabled")

    def on_select_vault(self, event):
        # No metadata panel in this reverted UI version; ignore selection
        return

    def delete_selected(self):
        index = self.quarantine_listbox.curselection()
        if not index:
            return
        index = index[0]

        # Use stored meta path instead of parsing text
        meta_path = self.display_index_to_meta.get(index)
        if not meta_path:
            messagebox.showerror("Error", "Metadata not found for selected file.")
            return

        qpath = meta_path.replace(".meta", "")

        try:
            if os.path.exists(qpath): os.remove(qpath)
            if os.path.exists(meta_path): os.remove(meta_path)

            self.quarantine_listbox.delete(index)
            self.quarantine_detail_text.config(state="normal")
            self.quarantine_detail_text.delete("1.0", "end")
            self.quarantine_detail_text.config(state="disabled")
            self.update_quarantine_listbox()
            print(f"[INFO] Deleted {qpath} and metadata.")
        except Exception as e:
            print(f"[ERROR] Delete failed: {e}")

    def restore_quarantined_file(self):
        index = self.quarantine_listbox.curselection()
        if not index:
            messagebox.showwarning("No Selection", "Please select a file.")
            return
        text = self.quarantine_listbox.get(index)
        match = re.search(r"→ From:\s*(.+)", text)
        if not match:
            messagebox.showerror("Error", "Could not parse original path.")
            return
        original_path = match.group(1)
        fname = os.path.basename(original_path)

        backup_root = filedialog.askdirectory(title="Select VWARbackup Folder")
        if not backup_root or not backup_root.endswith("VWARbackup"):
            messagebox.showerror("Error", "Invalid backup folder.")
            return

        found = []
        for root, _, files in os.walk(backup_root):
            for file in files:
                if file == fname + ".backup":
                    found.append(os.path.join(root, file))
        if not found:
            messagebox.showinfo("Not Found", "No backup file found.")
            return

        selected = found[0]
        if len(found) > 1:
            top = Toplevel(self.root)
            top.title("Choose Backup")
            listbox = Listbox(top, width=80)
            listbox.pack()
            for f in found:
                listbox.insert("end", f)
            def confirm():
                nonlocal selected
                if listbox.curselection():
                    selected = listbox.get(listbox.curselection()[0])
                    top.destroy()
            Button(top, text="Restore", command=confirm).pack()
            top.transient(self.root)
            top.grab_set()
            self.root.wait_window(top)

        try:
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            import shutil
            shutil.copy2(selected, original_path)
            messagebox.showinfo("Restored", f"Restored to:\n{original_path}")
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))

    def add_to_quarantine_listbox(self, file_path, meta_path, matched_rules):
        # Always marshal UI mutations to main thread
        def _do_insert():
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            file_name = os.path.basename(file_path)
            display_text = (
                f"File: {file_name}\n→ From: {file_path}\n→ Matched: {', '.join(matched_rules)}\n→ Time: {timestamp}"
            )
            try:
                self.quarantine_listbox.insert("end", display_text)
                self.display_index_to_meta[self.quarantine_listbox.size() - 1] = meta_path
            except Exception:
                pass
            try:
                self.update_quarantine_listbox()
            except Exception:
                pass
        try:
            self.root.after(0, _do_insert)
        except Exception:
            _do_insert()

    def add_to_scanvault_listbox(self, vaulted_path: str, meta_path: str):
        """Insert or update a single vaulted entry (pending). Fallback to full refresh for simplicity."""
        # Route through main loop for thread safety
        try:
            self.root.after(0, self.update_scanvault_listbox)
        except Exception:
            self.update_scanvault_listbox()

    def update_quarantine_listbox(self):
        """Refresh the quarantine list with current files."""
        # Ensure executed in Tk main thread
        if threading.current_thread().name != 'MainThread':
            try:
                return self.root.after(0, self.update_quarantine_listbox)
            except Exception:
                pass
        self.quarantine_listbox.delete(0, "end")
        self.display_index_to_meta = {}

        if not os.path.exists(self.quarantine_folder):
            return

        # Get and sort quarantined files by creation time
        files = [f for f in os.listdir(self.quarantine_folder) if f.endswith(".quarantined")]
        files.sort(key=lambda f: os.path.getctime(os.path.join(self.quarantine_folder, f)))

        for index, file in enumerate(files, start=1):
            base_name = file[:-12]  # Remove '.quarantined'
            meta_file = os.path.join(self.quarantine_folder, file + ".meta")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    original_path = meta.get("original_path", "Unknown")
                    display = f"{index}. File: {base_name}\n→ From: {original_path}"
                    self.quarantine_listbox.insert("end", display)
                    self.display_index_to_meta[self.quarantine_listbox.size() - 1] = meta_file
                except Exception as e:
                    print(f"[WARNING] Failed to load metadata for {file}: {e}")

    def update_scanvault_listbox(self):
        """Rebuild ScanVault list (pending + history) newest first, with status suffix for completed."""
        if not hasattr(self, 'scanvault_listbox'):
            return
        # Marshal to main thread if called from worker
        if threading.current_thread().name != 'MainThread':
            try:
                return self.root.after(0, self.update_scanvault_listbox)
            except Exception:
                pass
        self.scanvault_listbox.delete(0, 'end')
        self.vault_index_to_meta = {}
        if not os.path.isdir(self.scanvault_folder):
            return
        entries = []  # (dt, display_text, meta_path)
        # Pending (.vaulted)
        for f in os.listdir(self.scanvault_folder):
            if not f.endswith('.vaulted'):
                continue
            meta = os.path.join(self.scanvault_folder, f + '.meta')
            if not os.path.exists(meta):
                continue
            try:
                with open(meta, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                ts = data.get('timestamp', '')
                try:
                    dt_key = time.mktime(time.strptime(ts, '%Y-%m-%d %H:%M:%S'))
                except Exception:
                    dt_key = os.path.getctime(meta)
                fname = os.path.basename(data.get('vaulted_path', f))
                display = f"{fname} | {ts}"
                entries.append((dt_key, display, meta))
            except Exception:
                continue
        # History (.meta in history)
        history_dir = os.path.join(self.scanvault_folder, 'history')
        if os.path.isdir(history_dir):
            for f in os.listdir(history_dir):
                if not f.endswith('.meta'):
                    continue
                meta = os.path.join(history_dir, f)
                try:
                    with open(meta, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    ts = data.get('timestamp', '')
                    try:
                        dt_key = time.mktime(time.strptime(ts, '%Y-%m-%d %H:%M:%S'))
                    except Exception:
                        dt_key = os.path.getctime(meta)
                    fname = os.path.basename(data.get('vaulted_path', data.get('file_name', f)))
                    status = data.get('final_status')
                    suffix = ''
                    if status:
                        s = str(status).lower()
                        if s == 'quarantined':
                            suffix = ' — quarantined'
                        elif s == 'restored':
                            suffix = ' — restored'
                        elif s == 'duplicate_suppressed':
                            suffix = ' — duplicate suppressed'
                    display = f"{fname} | {ts}{suffix}"
                    entries.append((dt_key, display, meta))
                except Exception:
                    continue
        entries.sort(key=lambda x: x[0], reverse=True)
        for _, display, meta in entries:
            self.scanvault_listbox.insert('end', display)
            self.vault_index_to_meta[self.scanvault_listbox.size() - 1] = meta

    def delete_selected_vault(self):
        sel = self.scanvault_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        meta_path = self.vault_index_to_meta.get(idx)
        if not meta_path:
            return
        try:
            history_dir = os.path.join(self.scanvault_folder, 'history')
            if os.path.commonpath([os.path.abspath(meta_path), os.path.abspath(history_dir)]) == os.path.abspath(history_dir):
                if os.path.exists(meta_path):
                    os.remove(meta_path)
            else:
                vaulted_path = meta_path[:-5] if meta_path.endswith('.meta') else meta_path
                if os.path.exists(vaulted_path):
                    try:
                        os.remove(vaulted_path)
                    except Exception:
                        pass
                if os.path.exists(meta_path):
                    os.remove(meta_path)
        except Exception as e:
            print(f"[WARNING] Failed to delete vault item: {e}")
        finally:
            self.update_scanvault_listbox()

    def clear_vault_history(self):
        try:
            history_dir = os.path.join(self.scanvault_folder, 'history')
            if os.path.isdir(history_dir):
                for f in os.listdir(history_dir):
                    if f.endswith('.meta'):
                        try:
                            os.remove(os.path.join(history_dir, f))
                        except Exception:
                            pass
            self.update_scanvault_listbox()
        except Exception as e:
            print(f"[WARNING] Failed to clear vault history: {e}")
