import os, threading, base64, time, shutil, traceback
from tkinter import Frame, Button, Label, Text, Canvas, filedialog, TclError
from tkinter.ttk import Progressbar
from tkinterdnd2 import DND_FILES, TkinterDnD

from Scanning.yara_engine import fetch_and_generate_yara_rules, compile_yara_rules
from Scanning.quarantine import quarantine_file
from utils.tooltip import Tooltip
from utils.logger import log_message
from utils.notify import notify
from utils.settings import SETTINGS
import yara
import os
from datetime import datetime
import shutil
import json

from Scanning.scanner_core import scan_file_for_realtime

# Windows API for enabling drag-drop with admin privileges
import sys
if sys.platform == 'win32':
    try:
        import ctypes
        from ctypes import wintypes
        
        # Constants for ChangeWindowMessageFilterEx
        MSGFLT_ADD = 1
        MSGFLT_ALLOW = 1
        WM_DROPFILES = 0x0233
        WM_COPYDATA = 0x004A
        WM_COPYGLOBALDATA = 0x0049
        
        def enable_drag_drop_for_elevated_window(hwnd):
            """Enable drag-drop from non-elevated processes to elevated window"""
            try:
                # Try using ChangeWindowMessageFilterEx (Windows 7+)
                try:
                    user32 = ctypes.windll.user32
                    user32.ChangeWindowMessageFilterEx.argtypes = [
                        wintypes.HWND, wintypes.UINT, wintypes.DWORD, ctypes.c_void_p
                    ]
                    user32.ChangeWindowMessageFilterEx.restype = wintypes.BOOL
                    
                    # Allow these messages from lower privilege processes
                    user32.ChangeWindowMessageFilterEx(hwnd, WM_DROPFILES, MSGFLT_ALLOW, None)
                    user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYDATA, MSGFLT_ALLOW, None)
                    user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYGLOBALDATA, MSGFLT_ALLOW, None)
                    user32.ChangeWindowMessageFilterEx(hwnd, 0x0049, MSGFLT_ALLOW, None)
                    print("[INFO] ✓ Drag-drop enabled for elevated window using ChangeWindowMessageFilterEx")
                    return True
                except Exception as e1:
                    # Fallback to ChangeWindowMessageFilter (Vista)
                    try:
                        user32 = ctypes.windll.user32
                        user32.ChangeWindowMessageFilter(WM_DROPFILES, MSGFLT_ADD)
                        user32.ChangeWindowMessageFilter(WM_COPYDATA, MSGFLT_ADD)
                        user32.ChangeWindowMessageFilter(WM_COPYGLOBALDATA, MSGFLT_ADD)
                        print("[INFO] ✓ Drag-drop enabled using ChangeWindowMessageFilter (fallback)")
                        return True
                    except Exception as e2:
                        print(f"[WARNING] Could not enable drag-drop for elevated window: {e2}")
                        return False
            except Exception as e:
                print(f"[WARNING] Failed to enable elevated drag-drop: {e}")
                return False
    except ImportError:
        def enable_drag_drop_for_elevated_window(hwnd):
            return False
else:
    def enable_drag_drop_for_elevated_window(hwnd):
        return False


class ScanPage(Frame):
    def __init__(self, root, switch_page_callback):
        super().__init__(root, bg="#009AA5")
        self.root = root
        self.switch_page_callback = switch_page_callback

        self.target_path = None
        self.rules = None
        self.stop_scan = False
        
        # Notification tracking
        self.scan_start_time = None
        self.files_scanned = 0
        self.threats_found = 0

        self.build_ui()
        fetch_and_generate_yara_rules(self.log)
        self.root.after(100, self.load_rules)


    def build_ui(self):
        # === Top Navigation ===
        nav_frame = Frame(self, bg="#009AA5")
        nav_frame.pack(fill="x", pady=5, padx=5)

        # Button(nav_frame, text="← Back", command=lambda: self.switch_page_callback("home"),
        #     bg="gold", fg="white", font=("Inter", 12)).pack(side="left")
        # 🔹 Title
        Label(nav_frame, text="Scanning page ", font=("Arial", 24),
            bg="#009AA5", fg="white").pack(side="top",expand=True,fill='both')
        
        Button(nav_frame, text="Show Quarantined Files", command=lambda: self.switch_page_callback("monitor"),
            bg="purple", fg="white", font=("Inter", 12)).pack(side="right", padx=(0, 10))

        # === Load Log Box ===
        log_frame = Frame(self, bg="#009AA5")
        log_frame.pack(fill="x", padx=10)

        self.LOAD_TEXT = Text(log_frame, height=6, bg="#D9D9D9", fg="black", wrap="word", highlightthickness=0)
        self.LOAD_TEXT.pack(fill="x", expand=True)

        # === Drag & Drop Zone ===
        drop_zone_frame = Frame(self, bg="#009AA5")
        drop_zone_frame.pack(fill="x", padx=10, pady=10)

        self.drop_label = Label(drop_zone_frame, text="📁 Drag & Drop Files or Folders Here\n(or use buttons below)",
                                bg="#1ABC9C", fg="white", font=("Arial", 14, "bold"),
                                relief="ridge", bd=2, height=3)
        self.drop_label.pack(fill="x", expand=True)
        
        # Register drag-and-drop events - use try/except for compatibility
        try:
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind('<<Drop>>', self.on_drop)
            self.drop_label.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.drop_label.dnd_bind('<<DragLeave>>', self.on_drag_leave)
            self.log("[INFO] ✓ Drag & Drop enabled successfully!", "load")
            
            # Enable cross-privilege drag-drop on Windows (for admin apps)
            if sys.platform == 'win32':
                try:
                    # Must wait for widget to be fully created
                    self.drop_label.update_idletasks()
                    # Get the window handle for this widget
                    window_id = self.drop_label.winfo_id()
                    if enable_drag_drop_for_elevated_window(window_id):
                        self.log("[INFO] ✓ Cross-privilege drag-drop enabled (works with admin)", "load")
                except Exception as e:
                    self.log(f"[DEBUG] Cross-privilege setup: {e}", "load")
                    
        except Exception as e:
            # Fallback if tkinterdnd2 doesn't work properly
            self.log(f"[WARNING] Drag-and-drop initialization failed: {e}", "load")
            self.log("[INFO] Please use 'Select Target File/Folder' buttons instead", "load")
            self.drop_label.config(text="⚠ Drag & Drop Not Available\n(Use buttons below)", bg="#E67E22")

        # === File/Folder Controls ===
        control_frame = Frame(self, bg="#009AA5")
        control_frame.pack(fill="x", padx=10, pady=10)

        self._add_button_with_tooltip(control_frame, "Select Target File", self.select_file,
                                    "Choose a file to scan with YARA rules.")
        self._add_button_with_tooltip(control_frame, "Select Target Folder", self.select_folder,
                                    "Choose a folder to scan recursively")
        self._add_button_with_tooltip(control_frame, "Scan", self.start_scan_thread,
                                    "Start the scanning immediately.", bg="green", fg="white")
        self._add_button_with_tooltip(control_frame, "Stop", self.stop_scan_thread,
                                    "Stop the scanning immediately.", bg="red", fg="white")

        # === Progress Bar ===
        progress_frame = Frame(self, bg="#009AA5")
        progress_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.progress_label = Label(progress_frame, text="PROGRESS : 0%", bg="#12e012", fg="#000000", font=("Inter", 12))
        self.progress_label.pack(anchor="w")

        self.progress = Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x")

        # === Results Area (Matched / Tested) ===
        results_frame = Frame(self, bg="#009AA5")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_result = Frame(results_frame, bg="#AE0505")
        left_result.pack(side="left", expand=True, fill="both", padx=5)

        Label(left_result, text="MATCHED FILES", bg="#AE0505", fg="white", font=("Inter", 16, "bold")).pack(fill="x")
        self.matched_text = Text(left_result, bg="#F0CDCD", fg="#000000", wrap="word")
        self.matched_text.pack(fill="both", expand=True)

        right_result = Frame(results_frame, bg="#0A8D05")
        right_result.pack(side="right", expand=True, fill="both", padx=5)

        Label(right_result, text="TESTED FILES", bg="#0A8D05", fg="white", font=("Inter", 16, "bold")).pack(fill="x")
        self.tested_text = Text(right_result, bg="#B6F7AD", fg="#000000", wrap="word")
        self.tested_text.pack(fill="both", expand=True)



    def _add_button_with_tooltip(self, parent, text, command, tooltip, bg=None, fg=None):
        btn = Button(parent, text=text, command=command, bg=bg, fg=fg)
        btn.pack(side="left", padx=5)
        tip_label = Label(parent, text="?", bg="#009AA5", fg="white", font=("Arial", 12, "bold"))
        tip_label.pack(side="left", padx=(0, 10))
        Tooltip(tip_label, tooltip)

    def on_drop(self, event):
        """Handle drag-and-drop events"""
        try:
            self.log(f"[DEBUG] Drop event triggered! Data: {event.data[:100]}", "load")
            
            # Parse the dropped data (can be multiple files/folders)
            dropped_data = self._parse_drop_data(event.data)
            
            if len(dropped_data) == 0:
                self.log("[WARNING] No valid files or folders dropped.", "load")
                self.log(f"[DEBUG] Raw data was: {event.data}", "load")
                return
            
            # If single item, set as target and save it
            if len(dropped_data) == 1:
                path = dropped_data[0]
                self.target_path = path
                self.LOAD_TEXT.delete("1.0", "end")
                
                # Save the dropped path for later use
                if os.path.isfile(path):
                    self.log(f"[INFO] File dropped and saved: {path}", "load")
                elif os.path.isdir(path):
                    self.log(f"[INFO] Folder dropped and saved: {path}", "load")
                else:
                    self.log(f"[WARNING] Unknown type: {path}", "load")
                
                # Change drop zone color to indicate ready
                basename = os.path.basename(path) if path else "Unknown"
                self.drop_label.config(bg="#27AE60", text=f"✓ Path saved:\n{basename}\n(Click 'Scan' to start)")
                
                # DON'T auto-start - let user click Scan button
                self.log("[INFO] Path saved. Click 'Scan' button to start scanning.", "load")
                
            # If multiple items, save first one and log others
            else:
                self.log(f"[INFO] Multiple items dropped ({len(dropped_data)} items)", "load")
                # Save first valid path
                if dropped_data:
                    self.target_path = dropped_data[0]
                    self.log(f"[INFO] Primary path saved: {self.target_path}", "load")
                    for idx, path in enumerate(dropped_data[1:], 1):
                        self.log(f"  [{idx}] {path}", "load")
                    self.log("[INFO] Click 'Scan' to scan the primary path.", "load")
                        
        except Exception as e:
            self.log(f"[ERROR] Drop failed: {e}", "load")
            traceback.print_exc()
    
    def on_drag_enter(self, event):
        """Visual feedback when dragging over drop zone"""
        try:
            self.drop_label.config(bg="#16A085")  # Darker green on hover
        except Exception:
            pass
    
    def on_drag_leave(self, event):
        """Reset visual feedback when leaving drop zone"""
        try:
            self.drop_label.config(bg="#1ABC9C")  # Original green
        except Exception:
            pass

    def _parse_drop_data(self, data):
        """Parse tkinterdnd2 drop data into list of paths"""
        paths = []
        
        # Handle Windows file paths with curly braces
        if data.startswith('{'):
            # Split by } { pattern for multiple files
            items = data.strip('{}').split('} {')
            paths = [item.strip() for item in items]
        else:
            # Single file or space-separated paths
            paths = [data.strip()]
        
        # Clean and validate paths
        cleaned_paths = []
        for path in paths:
            # Remove quotes if present
            path = path.strip('"').strip("'")
            if os.path.exists(path):
                cleaned_paths.append(path)
        
        return cleaned_paths








    def log(self, msg, target="load"):
        log_message(msg)
        if target == "load":
            self.LOAD_TEXT.insert("end", msg + "\n")
        elif target == "matched":
            self.matched_text.insert("end", msg + "\n")
            self.matched_text.see("end")
            
        elif target == "tested":
            self.tested_text.insert("end", msg + "\n")
            self.tested_text.see("end")  

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.target_path = path
            self.LOAD_TEXT.delete("1.0", "end")
            self.log(f"[INFO] Selected file: {path}", "load")

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.target_path = path
            self.LOAD_TEXT.delete("1.0", "end")
            self.log(f"[INFO] Selected folder: {path}", "load")

    def start_scan_thread(self):
        self.stop_scan = False
        thread = threading.Thread(target=self.scan, daemon=True)
        thread.start()

    def stop_scan_thread(self):
        self.stop_scan = True
        self.log("[INFO] Scan stop requested.", "load")

    def load_rules(self):
        self.rules = compile_yara_rules(log_func=self.log)

    def scan(self):
        if not self.rules:
            self.log("[ERROR] No YARA rules loaded.", "load")
            return
        if not self.target_path:
            self.log("[ERROR] No target path selected.", "load")
            return

        self.matched_text.delete("1.0", "end")
        self.tested_text.delete("1.0", "end")
        
        # Reset tracking
        self.scan_start_time = time.time()
        self.files_scanned = 0
        self.threats_found = 0

        if os.path.isfile(self.target_path):
            self.scan_file(self.target_path)
        elif os.path.isdir(self.target_path):
            self.scan_directory(self.target_path)

        self.progress.stop()
        self.progress_label.config(text="Scan Complete!")
        
        # Send completion notification
        self._send_scan_complete_notification()

    def scan_directory(self, directory):
        files = []
        for root, _, filenames in os.walk(directory):
            for f in filenames:
                files.append(os.path.join(root, f))

        total = len(files)
        self.progress["maximum"] = total
        self.progress["value"] = 0

        for i, file_path in enumerate(files, 1):
            if self.stop_scan:
                break
            self.scan_file(file_path)
            self.progress["value"] = i
            percent = int((i / total) * 100)
            self.progress_label.config(text=f"PROGRESS : {percent}%")
            self.root.update_idletasks()

    def scan_file(self, path):
        self.log(path, "tested")
        self.files_scanned += 1
        
        result = scan_file_for_realtime(path)
        # Backwards compatibility still allows tuple, but we prefer named fields
        matched, rule, qpath, meta_path = result[:4]
        status = getattr(result, 'status', 'UNKNOWN')

        if matched:
            self.threats_found += 1
            self.log(f"[MATCH] {path} => Rule: {rule}", "matched")
            # Send threat detection notification
            if SETTINGS.tray_notifications:
                notify("⚠️ Threat Detected!", f"File: {os.path.basename(path)}\nRule: {rule}", duration=8)
        else:
            if status == "NO_RULES":
                self.log(f"[WARN] Rules not loaded when scanning: {path}", "tested")
            elif status == "SKIPPED_INTERNAL":
                self.log(f"[SKIP] Internal rule file skipped: {path}", "tested")
            elif status == "QUARANTINE_FAILED":
                self.log(f"[WARNING] Match but quarantine failed: {path} (rule={rule})", "tested")
            elif status == "YARA_ERROR":
                self.log(f"[WARNING] YARA engine error on: {path}", "tested")
            elif status == "ERROR":
                self.log(f"[ERROR] Unexpected failure scanning: {path}", "tested")
            # CLEAN is silent except already logged as tested
    
    def _send_scan_complete_notification(self):
        """Send notification when scan completes."""
        if not SETTINGS.tray_notifications:
            return
        
        duration = time.time() - self.scan_start_time if self.scan_start_time else 0
        duration_str = f"{int(duration)}s" if duration < 60 else f"{int(duration//60)}m {int(duration%60)}s"
        
        if self.threats_found > 0:
            message = f"Scanned: {self.files_scanned} files\n⚠️ Threats found: {self.threats_found}\nTime: {duration_str}"
            notify("🔍 Scan Complete - Threats Found!", message, duration=10)
        else:
            message = f"Scanned: {self.files_scanned} files\n✅ No threats detected\nTime: {duration_str}"
            notify("🔍 Scan Complete - All Clear!", message, duration=5)












