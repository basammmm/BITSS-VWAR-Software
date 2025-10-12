import os
import json

from tkinter import Tk, Frame, Label, Button, LabelFrame
from tkinterdnd2 import TkinterDnD
from config import ICON_PATH, ACTIVATION_FILE, QUARANTINE_FOLDER
from Scanning.scan_page import ScanPage
from Backup.main_backup_page import BackupMainPage
from Backup.backup_page import ManualBackupPage
from Backup.restore_page import RestoreBackupPage
from Backup.auto_backup_page import AutoBackupPage
from Backup.auto_backup import AutoBackupScheduler
from RMonitoring.monitor_page import MonitorPage
from utils.profile_info import LicenseTermsPage
from utils.help_page import HelpPage
from utils.exclusions_page import ExclusionsPage
from utils.settings import SETTINGS, set_debug, is_debug
from utils.startup import enable_startup, disable_startup, is_startup_enabled
from utils.tray import create_tray
from Scanning.scheduled_scan import ScheduledScanRunner, load_scan_schedule, save_scan_schedule, ScanScheduleConfig

from datetime import datetime, timedelta
from utils.update_checker import check_for_updates,CURRENT_VERSION,up_to
from cryptography.fernet import Fernet
import base64, hashlib

DEBUG = False  # Set True for verbose debugging

class VWARScannerGUI:
    def __init__(self, root):
        # Basic window setup
        self.root = root
        self.root.title("VWAR SCANNER")
        self.root.geometry("1200x722")
        self.root.configure(bg="#009AA5")

        # Start background services (auto backup scheduler)
        AutoBackupScheduler().start()
        
        # System tray icon
        self.tray_icon = None
        self.minimize_to_tray = getattr(SETTINGS, "minimize_to_tray", True)  # Default enabled

        # Shared state / attributes
        self.pages = {}
        self.rules = None
        self.target_path = None
        self.stop_scan = False
        self.selected_files = []
        self.rule_folder = os.path.join(os.getcwd(), "assets", "yara")
        os.makedirs(self.rule_folder, exist_ok=True)

        self.quarantine_folder = QUARANTINE_FOLDER
        os.makedirs(self.quarantine_folder, exist_ok=True)

        self.activated_user = "Unknown"
        self.valid_till = "Unknown"
        self.load_activation_info()
        self.watch_paths = self.get_all_accessible_drives()

        # Main layout containers
        self.main_container = Frame(self.root, bg="#009AA5")
        self.main_container.pack(fill="both", expand=True)

        self.sidebar = Frame(self.main_container, bg="#004d4d", width=200)
        self.sidebar.pack(side="left", fill="both")
        self.main_area = Frame(self.main_container, bg="#ffffff")
        self.main_area.pack(side="right", fill="both", expand=True)

        # Build persistent UI elements
        self.build_sidebar()
        self._init_pages()

        # Start scheduled scan runner
        self.scheduled_scan_runner = ScheduledScanRunner(gui_ref=self)
        # Wire callbacks for progress modal
        self.scheduled_scan_runner.on_start = self._scheduled_scan_on_start
        self.scheduled_scan_runner.on_progress = self._scheduled_scan_on_progress
        self.scheduled_scan_runner.on_complete = self._scheduled_scan_on_complete
        self.scheduled_scan_runner.start()

        # Attempt to auto-start monitoring
        try:
            monitor_page = self.pages.get("monitor")
            if monitor_page:
                monitor_page.toggle_monitoring()
                print("[INFO] Auto-started Real-Time Monitoring from app_main.py")
        except Exception as e:
            print(f"[ERROR] Could not auto-start Real-Time Monitoring: {e}")

        # Show default page
        self.show_page("home")

        # Icon & close handler
        self.root.iconbitmap(ICON_PATH)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    # Allow background threads to schedule GUI updates safely
    def schedule_gui(self, func, *args):
        try:
            self.root.after(0, lambda: func(*args))
        except Exception:
            pass
        
        
    def build_sidebar(self):
        Label(self.sidebar, text="📂 VWAR SCANNER", font=("Arial", 14, "bold"),
            bg="#004d4d", fg="white").pack(pady=20)



        Button(self.sidebar, text="🏠 Home", bg="#007777", fg="white", font=("Arial", 12),
            command=lambda: self.show_page("home")).pack(fill="x", padx=10, pady=5)

        Button(self.sidebar, text="🧪 Scan", bg="#007777", fg="white", font=("Arial", 12),
            command=lambda: self.show_page("scan")).pack(fill="x", padx=10, pady=5)

        Button(self.sidebar, text="💾 Backup", bg="#007777", fg="white", font=("Arial", 12),
            command=lambda: self.show_page("backup")).pack(fill="x", padx=10, pady=5)

        Button(self.sidebar, text="♻️ Scan Vault", bg="#007777", fg="white", font=("Arial", 12),
            command=lambda: self.show_page("monitor")).pack(fill="x", padx=10, pady=5)

        Button(self.sidebar, text="❓ Help", bg="#007777", fg="white", font=("Arial", 12),
            command=lambda: self.show_page("help")).pack(fill="x", padx=10, pady=5)

        Button(self.sidebar, text="📅 Schedule Scan", bg="#007777", fg="white", font=("Arial", 12),
            command=lambda: self.show_page("settings")).pack(fill="x", padx=10, pady=5)

    
    def create_home_page(self):
        frame = Frame(self.main_area, bg="#009AA5")
        self.pages["home"] = frame
        
        
        Button(frame, text="📋 License Terms", font=("Arial", 10),
       command=lambda: self.show_page("license_terms")).pack(side='right')

        # 🔹 Update Status
        update_frame = Frame(frame, bg="#009AA5")
        update_frame.pack(side="top",fill='x')
        
        if up_to() == 1:
            Button(update_frame, text="🔺 Update Available", command=check_for_updates,
                bg="white", fg="red", font=("Arial", 10)).pack(side='left')
        else:
            Label(update_frame, text="✅ Up to Date", font=("Arial", 10),
                bg="white", fg="green").pack(side='left')
        
        
        # 🔹 Title
        Label(frame, text="VWAR SCANNER", font=("Arial", 24),
            bg="#009AA5", fg="white").pack(side="top",expand=True,fill='both')
        
        
                # 🔹 User Info
        user_info_frame = Frame(frame, bg="#009AA5")
        user_info_frame.pack(side="top",expand=True,fill='both')
        
        Label(user_info_frame, text=f"User: {self.activated_user}",
            font=("Arial", 12), bg="white", fg="black").pack(pady=2)

        Label(user_info_frame, text=f"Valid Till: {self.valid_till}",
            font=("Arial", 12), bg="white", fg="black").pack(pady=2)
        
        
                        # 🔹 Auto Scan Status
        self.home_scan_status_label = Label(frame, text="Status: Running ●",
                                            font=("Arial", 16, "bold"),
                                            bg="#009AA5", fg="green")
        
        self.home_scan_status_label.pack(side="top",expand=True,fill='both')
        
        Label(self.home_scan_status_label, text="AUTO SCANNING STATUS :", font=("Arial", 18,"bold"),
                bg="white", fg="BLACK").pack(side='left')
        
        
        
                # 🔹 Contact Section
        contact_frame = LabelFrame(frame, text="About / Contact Us",
                                bg="#009AA5", fg="white",
                                font=("Arial", 12, "bold"),
                                padx=10, pady=10)
        
        contact_frame.pack(side="bottom",expand=True,fill='both')
        
        Label(contact_frame, text=f"Version: {CURRENT_VERSION}",
            bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Developer BY : Bitss.one",
            bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        # Label(contact_frame, text="Email: Bitss.fr",
        #     bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Website: http://www.bitss.one",
            bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")
        Label(contact_frame, text="Support: support@bobosohomail.com",
            bg="#009AA5", fg="white", font=("Arial", 10)).pack(anchor="w")

        # 🔄 Status Animation
        self.animate_home_status()


    def animate_home_status(self):
        if getattr(self, "pages", None) and "monitor" in self.pages:
            monitor_page = self.pages["monitor"]
            if getattr(monitor_page, "monitoring_active", False):
                current = self.home_scan_status_label.cget("text")
                new_text = "Status: Running" if "●" in current else "Status: Running ●"
                self.home_scan_status_label.config(text=new_text)
            else:
                self.home_scan_status_label.config(text="Status: Stopped", fg="red")
        self.root.after(500, self.animate_home_status)

    def show_page(self, name):
        if DEBUG:
            print(f"[DEBUG] Switching to page: {name}")

        # Hide all other pages
        for page in self.pages.values():
            page.pack_forget()

        if name not in self.pages:
            print(f"[ERROR] Page '{name}' not found.")
            return

        # Show the requested page
        self.pages[name].pack(fill="both", expand=True)

        # self.pages[name].place(x=0, y=0, width=843, height=722)
        # self.pages[name].place(x=200, y=0, width=843, height=722)

        # ✅ If Monitor page is shown, auto-refresh list
        if name == "monitor":
            try:
                self.pages["monitor"].update_quarantine_listbox()
                # Also refresh ScanVault view when entering the page
                if hasattr(self.pages["monitor"], "update_scanvault_listbox"):
                    self.pages["monitor"].update_scanvault_listbox()
                if DEBUG:
                    print("[DEBUG] Auto-refreshed quarantine list in Monitor page.")
            except Exception as e:
                print(f"[ERROR] Failed to refresh Monitor page: {e}")

        if name == "settings" and hasattr(self, "_settings_debug_var"):
            # Sync checkbox with current setting
            self._settings_debug_var.set(SETTINGS.debug)


    def generate_fernet_key_from_string(self,secret_string):
        sha256 = hashlib.sha256(secret_string.encode()).digest()
        return base64.urlsafe_b64encode(sha256)


    
    
    def load_activation_info(self):
        """Reads activation.json and sets user info."""
        try:
            SECRET_KEY = self.generate_fernet_key_from_string("VWAR@BIFIN")
            fernet = Fernet(SECRET_KEY)
            if DEBUG:
                print("[DEBUG] Trying to load:", ACTIVATION_FILE)
            with open(ACTIVATION_FILE, "rb") as f:
                encrypted = f.read()
                decrypted = fernet.decrypt(encrypted)
                data = json.loads(decrypted.decode("utf-8"))

            self.activated_user = data.get("username", "unknown")
            self.valid_till = data.get("valid_till", "unknown")
            self.created_at = data.get("created_at", "unknown")
            
                        
            
            
            # with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
            #     data = json.load(f)
            self.activated_user = data.get("username","unknown" )
            self.valid_till = data.get("valid_till","unknown")
        except Exception  as  e:
            print("[ERROR] Failed to load activation info:", e)
            self.activated_user = "unknown"
            self.valid_till = "unknown"

    def on_close(self):
        """Minimize to tray or exit based on settings."""
        if self.minimize_to_tray:
            # Minimize to tray instead of closing
            self.root.withdraw()  # Hide window
            
            # Create tray icon if not already created
            if not self.tray_icon:
                self.tray_icon = create_tray(
                    on_restore=self.restore_from_tray,
                    on_exit=self.exit_app,
                    icon_path=ICON_PATH,
                    tooltip="VWAR Scanner - Running in background",
                    on_scan_now=self.tray_scan_now
                )
        else:
            # Normal exit
            self.exit_app()
    
    def restore_from_tray(self):
        """Restore window from system tray."""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception as e:
            print(f"[ERROR] Failed to restore window: {e}")
    
    def tray_scan_now(self):
        """Trigger scan from tray menu."""
        try:
            self.restore_from_tray()
            if "scan" in self.pages:
                self.show_page("scan")
        except Exception as e:
            print(f"[ERROR] Tray scan failed: {e}")
    
    def exit_app(self):
        """Stops monitoring/backup if running, exits app cleanly."""
        # Stop tray icon
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        
        # Stop monitor page's realtime engine if running
        try:
            monitor_page = self.pages.get("monitor")
            if monitor_page and hasattr(monitor_page, "stop_monitoring"):
                monitor_page.stop_monitoring()
        except Exception:
            pass
        # Legacy guard
        if hasattr(self, "real_time_monitor"):
            try:
                self.real_time_monitor.stop()
            except Exception:
                pass
        if hasattr(self, "auto_backup"):
            self.auto_backup.stop()
        self.root.destroy()
        os._exit(0)  # Force exit


    def get_all_accessible_drives(self):
        from string import ascii_uppercase
        drives = [f"{d}:/" for d in ascii_uppercase if os.path.exists(f"{d}:/")]
        drives.append(os.path.expanduser("~"))  # Include user home folder
        return list(set(drives))

    def _init_pages(self):
        """Initialize GUI pages (isolated to avoid indentation issues)."""
        self.create_home_page()
        self.pages["scan"] = ScanPage(self.main_area, self.show_page)
        self.pages["backup"] = BackupMainPage(self.main_area, self.show_page)
        self.pages["manual_backup"] = ManualBackupPage(self.main_area, self.show_page)
        self.pages["restore_backup"] = RestoreBackupPage(self.main_area, self.show_page)
        self.pages["auto_backup"] = AutoBackupPage(self.main_area, self.show_page)
        self.pages["monitor"] = MonitorPage(self.main_area, self, self.show_page)
        self.pages["license_terms"] = LicenseTermsPage(self.main_area, self)
        self.pages["help"] = HelpPage(self.main_area, self)
        self.pages["exclusions"] = ExclusionsPage(self.main_area, self.show_page)
        self.pages["settings"] = self._build_settings_page(self.main_area)

    # ---------------- Settings Page -----------------
    def _build_settings_page(self, parent):
        import tkinter as tk
        
        # Create container with scrollbar
        container = tk.Frame(parent, bg="#009AA5")
        
        canvas = tk.Canvas(container, bg="#009AA5", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#009AA5")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Now use scrollable_frame instead of frame
        frame = scrollable_frame
        header = tk.Label(frame, text="Settings & Schedule", font=("Arial", 24, "bold"), bg="#009AA5", fg="white")
        header.pack(pady=10)
        ui_font = ("Arial", 12)

        # Debug toggle (forced ON)
        set_debug(True)
        self._settings_debug_var = tk.BooleanVar(value=True)
        def on_debug_toggle():
            set_debug(self._settings_debug_var.get())
            global DEBUG
            DEBUG = SETTINGS.debug
            if DEBUG:
                print("[DEBUG] Debug mode enabled via Schedule Scan UI")
        debug_chk = tk.Checkbutton(frame, text="Enable Debug Logging", variable=self._settings_debug_var,
                                   command=on_debug_toggle, bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font)
        debug_chk.pack(anchor="w", padx=20, pady=5)
        debug_chk.config(state="disabled")

        # Startup (Run at Windows login) toggle
        self._startup_var = tk.BooleanVar(value=is_startup_enabled())
        def on_startup_toggle():
            if self._startup_var.get():
                ok = enable_startup()
                if not ok:
                    self._startup_var.set(False)
                    self._sched_feedback.config(text="Failed enabling startup (permissions?)", fg="red")
            else:
                disable_startup()
        startup_chk = tk.Checkbutton(frame, text="Start with Windows", variable=self._startup_var,
                                      command=on_startup_toggle, bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font)
        startup_chk.pack(anchor="w", padx=20, pady=(0,5))

        # Startup tray preference
        self._startup_tray_var = tk.BooleanVar(value=SETTINGS.startup_tray)
        def on_startup_tray_toggle():
            SETTINGS.startup_tray = self._startup_tray_var.get()
        tk.Checkbutton(frame, text="Start minimized to tray when auto-starting", variable=self._startup_tray_var,
                       command=on_startup_tray_toggle, bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=40, pady=(0,5))

        # Minimize to tray on close
        self._minimize_tray_var = tk.BooleanVar(value=self.minimize_to_tray)
        def on_minimize_tray_toggle():
            self.minimize_to_tray = self._minimize_tray_var.get()
            SETTINGS.minimize_to_tray = self.minimize_to_tray
            # If enabled and no tray icon exists, create it
            if self.minimize_to_tray and not self.tray_icon:
                self.tray_icon = create_tray(
                    on_restore=self.restore_from_tray,
                    on_exit=self.exit_app,
                    icon_path=ICON_PATH,
                    tooltip="VWAR Scanner - Running in background",
                    on_scan_now=self.tray_scan_now
                )
        tk.Checkbutton(frame, text="Minimize to tray on close (X button)", variable=self._minimize_tray_var,
                       command=on_minimize_tray_toggle, bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=40, pady=(0,5))

        # Tray notification preference
        self._tray_notify_var = tk.BooleanVar(value=SETTINGS.tray_notifications)
        def on_tray_notify_toggle():
            SETTINGS.tray_notifications = self._tray_notify_var.get()
        tk.Checkbutton(frame, text="Show tray notifications on detections", variable=self._tray_notify_var,
                       command=on_tray_notify_toggle, bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=40, pady=(0,10))

        note = tk.Label(frame, text="Debug mode prints extra diagnostic messages to console/log.",
                        bg="#009AA5", fg="white", wraplength=600, justify="left", font=ui_font)
        note.pack(anchor="w", padx=20, pady=(0,15))

        # Scheduled Scan Section
        sched_header = tk.Label(frame, text="Scheduled Scanning", font=("Arial", 18, "bold"), bg="#009AA5", fg="white")
        sched_header.pack(anchor="w", padx=20, pady=(10,5))

        from Scanning.scheduled_scan import load_scan_schedule, save_scan_schedule, ScanScheduleConfig
        cfg = load_scan_schedule()
        self._sched_enabled_var = tk.BooleanVar(value=True)
        self._sched_time_var = tk.StringVar(value=cfg.time)
        self._sched_paths_var = tk.StringVar(value=";".join(cfg.paths))
        self._sched_recursive_var = tk.BooleanVar(value=cfg.include_subdirs)
        self._sched_freq_var = tk.StringVar(value=cfg.frequency)
        self._sched_interval_var = tk.StringVar(value=str(cfg.interval_minutes))
        self._sched_last_run = tk.StringVar(value=cfg.last_run or "Never")
        weekdays = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        self._weekday_vars = []

        sched_enable_chk = tk.Checkbutton(frame, text="Enable Scheduled Scan", variable=self._sched_enabled_var,
                       bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font)
        sched_enable_chk.pack(anchor="w", padx=30)
        sched_enable_chk.config(state="disabled")

        # Frequency selection
        freq_row = tk.Frame(frame, bg="#009AA5")
        freq_row.pack(fill="x", padx=30, pady=2)
        tk.Label(freq_row, text="Frequency:", bg="#009AA5", fg="white", font=ui_font).pack(side="left")
        for val, label in [
            ("realtime","Realtime"),
            ("hourly","Hourly"),
            ("twice_daily","Twice Daily"),
            ("daily","Daily"),
            ("custom","Custom")
        ]:
            tk.Radiobutton(freq_row, text=label, value=val, variable=self._sched_freq_var,
                           bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font).pack(side="left", padx=5)

        # Time input
        time_row = tk.Frame(frame, bg="#009AA5")
        time_row.pack(fill="x", padx=30, pady=2)
        tk.Label(time_row, text="Time (HH:MM 24h):", bg="#009AA5", fg="white", font=ui_font).pack(side="left")
        tk.Entry(time_row, textvariable=self._sched_time_var, width=8, font=ui_font).pack(side="left", padx=5)

        # Placeholder for legacy weekday row (hidden with new model)
        weekday_row = tk.Frame(frame, bg="#009AA5")  # kept for layout consistency; not populated

        # Custom interval minutes
        interval_row = tk.Frame(frame, bg="#009AA5")
        interval_row.pack(fill="x", padx=30, pady=2)
        tk.Label(interval_row, text="Custom Interval (minutes):", bg="#009AA5", fg="white", font=ui_font).pack(side="left")
        tk.Entry(interval_row, textvariable=self._sched_interval_var, width=6, font=ui_font).pack(side="left", padx=5)

        # Paths section with directory picker
        path_row = tk.Frame(frame, bg="#009AA5")
        path_row.pack(fill="x", padx=30, pady=2)
        tk.Label(path_row, text="Paths (separate with ;):", bg="#009AA5", fg="white", font=ui_font).pack(side="left", anchor="w")
        path_entry = tk.Entry(path_row, textvariable=self._sched_paths_var, font=ui_font)
        path_entry.pack(side="left", padx=5, fill="x", expand=True)
        def add_dir():
            from tkinter import filedialog
            d = filedialog.askdirectory()
            if d:
                current = self._sched_paths_var.get().strip()
                self._sched_paths_var.set((current+';' if current else '') + d)
        tk.Button(path_row, text="+Dir", command=add_dir, bg="#007777", fg="white", font=ui_font).pack(side="left", padx=5)

        tk.Checkbutton(frame, text="Include Subdirectories", variable=self._sched_recursive_var,
                       bg="#009AA5", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=30, pady=2)

        # Last run display
        last_run_row = tk.Frame(frame, bg="#009AA5")
        last_run_row.pack(fill="x", padx=30, pady=(4,2))
        tk.Label(last_run_row, text="Last Run:", bg="#009AA5", fg="white", font=ui_font).pack(side="left")
        tk.Label(last_run_row, textvariable=self._sched_last_run, bg="#009AA5", fg="yellow", font=ui_font).pack(side="left")

        # Validation feedback label
        self._sched_feedback = tk.Label(frame, text="", bg="#009AA5", fg="yellow", font=ui_font)
        self._sched_feedback.pack(anchor="w", padx=30)

        def validate_time(t: str) -> bool:
            import re
            return bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t))

        def save_schedule():
            # Gather and validate
            raw_time = self._sched_time_var.get().strip()
            if self._sched_freq_var.get() in ('hourly','twice_daily','daily') and not validate_time(raw_time):
                self._sched_feedback.config(text="Invalid time format. Use HH:MM (24h)", fg="red")
                return
            try:
                interval_val = int(self._sched_interval_var.get())
                if interval_val <= 0:
                    raise ValueError
            except Exception:
                if self._sched_freq_var.get() == 'custom':
                    self._sched_feedback.config(text="Interval must be positive integer", fg="red")
                    return
                interval_val = 1440
            raw_paths = [p.strip() for p in self._sched_paths_var.get().split(';') if p.strip()]
            new_cfg = ScanScheduleConfig(
                enabled=self._sched_enabled_var.get(),
                time=raw_time or '02:00',
                paths=raw_paths,
                include_subdirs=self._sched_recursive_var.get(),
                frequency=self._sched_freq_var.get(),
                weekdays=[],
                interval_minutes=interval_val,
                last_run=cfg.last_run
            )
            save_scan_schedule(new_cfg)
            self._sched_feedback.config(text="Saved", fg="green")
            # Refresh last run display from persisted file
            updated = load_scan_schedule()
            self._sched_last_run.set(updated.last_run or "Never")

        btn_row = tk.Frame(frame, bg="#009AA5")
        btn_row.pack(anchor="w", padx=30, pady=5)
        tk.Button(btn_row, text="Save", command=save_schedule, bg="#007777", fg="white", font=ui_font).pack(side="left")
        def run_now():
            self.scheduled_scan_runner.run_now()
        tk.Button(btn_row, text="Run Now", command=run_now, bg="#555577", fg="white", font=ui_font).pack(side="left", padx=10)
        
        # === Inline Exclusions Section ===
        tk.Label(frame, text="", bg="#009AA5").pack(pady=15)  # Spacer
        
        excl_header = tk.Label(frame, text="Scan Exclusions", font=("Arial", 18, "bold"), bg="#009AA5", fg="white")
        excl_header.pack(anchor="w", padx=20, pady=(10,5))
        
        excl_desc = tk.Label(frame, text="Add paths or file extensions to exclude from all scans.", 
                            bg="#009AA5", fg="white", font=ui_font, wraplength=800, justify="left")
        excl_desc.pack(anchor="w", padx=30, pady=(0,10))
        
        # Import exclusions backend
        from utils.user_exclusions import UserExclusions
        self.user_exclusions = UserExclusions()
        
        # Create two-column layout for paths and extensions
        exclusions_container = tk.Frame(frame, bg="#009AA5")
        exclusions_container.pack(fill="both", expand=True, padx=30, pady=5)
        
        # Left: Excluded Paths
        left_col = tk.Frame(exclusions_container, bg="#009AA5")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(left_col, text="Excluded Paths:", bg="#009AA5", fg="white", font=("Arial", 12, "bold")).pack(anchor="w")
        
        paths_frame = tk.Frame(left_col, bg="#009AA5")
        paths_frame.pack(fill="both", expand=True)
        
        paths_scrollbar = tk.Scrollbar(paths_frame)
        paths_scrollbar.pack(side="right", fill="y")
        
        self.excl_paths_listbox = tk.Listbox(paths_frame, yscrollcommand=paths_scrollbar.set, height=6, bg="white", fg="black")
        self.excl_paths_listbox.pack(side="left", fill="both", expand=True)
        paths_scrollbar.config(command=self.excl_paths_listbox.yview)
        
        # Populate paths
        for path in self.user_exclusions.get_excluded_paths():
            self.excl_paths_listbox.insert("end", path)
        
        paths_btn_frame = tk.Frame(left_col, bg="#009AA5")
        paths_btn_frame.pack(fill="x", pady=5)
        
        def add_path():
            from tkinter import filedialog
            path = filedialog.askdirectory(title="Select Folder to Exclude")
            if path:
                self.user_exclusions.add_path(path)
                self.excl_paths_listbox.insert("end", path)
        
        def add_file():
            from tkinter import filedialog
            path = filedialog.askopenfilename(title="Select File to Exclude")
            if path:
                self.user_exclusions.add_path(path)
                self.excl_paths_listbox.insert("end", path)
        
        def remove_path():
            selection = self.excl_paths_listbox.curselection()
            if selection:
                idx = selection[0]
                path = self.excl_paths_listbox.get(idx)
                self.user_exclusions.remove_path(path)
                self.excl_paths_listbox.delete(idx)
        
        tk.Button(paths_btn_frame, text="+ Add Folder", command=add_path, bg="#007777", fg="white", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Button(paths_btn_frame, text="+ Add File", command=add_file, bg="#007777", fg="white", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Button(paths_btn_frame, text="- Remove", command=remove_path, bg="#AA0000", fg="white", font=("Arial", 10)).pack(side="left", padx=2)
        
        # Right: Excluded Extensions
        right_col = tk.Frame(exclusions_container, bg="#009AA5")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(right_col, text="Excluded Extensions:", bg="#009AA5", fg="white", font=("Arial", 12, "bold")).pack(anchor="w")
        
        ext_frame = tk.Frame(right_col, bg="#009AA5")
        ext_frame.pack(fill="both", expand=True)
        
        ext_scrollbar = tk.Scrollbar(ext_frame)
        ext_scrollbar.pack(side="right", fill="y")
        
        self.excl_ext_listbox = tk.Listbox(ext_frame, yscrollcommand=ext_scrollbar.set, height=6, bg="white", fg="black")
        self.excl_ext_listbox.pack(side="left", fill="both", expand=True)
        ext_scrollbar.config(command=self.excl_ext_listbox.yview)
        
        # Populate extensions
        for ext in self.user_exclusions.get_excluded_extensions():
            self.excl_ext_listbox.insert("end", ext)
        
        ext_btn_frame = tk.Frame(right_col, bg="#009AA5")
        ext_btn_frame.pack(fill="x", pady=5)
        
        def add_extension():
            # Create simple dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Add Extension")
            dialog.geometry("300x120")
            dialog.configure(bg="#009AA5")
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Enter extension (e.g., .mp4):", bg="#009AA5", fg="white", font=ui_font).pack(pady=10)
            entry = tk.Entry(dialog, font=ui_font)
            entry.pack(padx=20, fill="x")
            entry.focus()
            
            def save_ext():
                ext = entry.get().strip()
                if ext:
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    self.user_exclusions.add_extension(ext)
                    self.excl_ext_listbox.insert("end", ext)
                dialog.destroy()
            
            tk.Button(dialog, text="Add", command=save_ext, bg="#007777", fg="white", font=ui_font).pack(pady=10)
            entry.bind('<Return>', lambda e: save_ext())
        
        def remove_extension():
            selection = self.excl_ext_listbox.curselection()
            if selection:
                idx = selection[0]
                ext = self.excl_ext_listbox.get(idx)
                self.user_exclusions.remove_extension(ext)
                self.excl_ext_listbox.delete(idx)
        
        tk.Button(ext_btn_frame, text="+ Add Extension", command=add_extension, bg="#007777", fg="white", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Button(ext_btn_frame, text="- Remove", command=remove_extension, bg="#AA0000", fg="white", font=("Arial", 10)).pack(side="left", padx=2)
        
        # Quick presets
        tk.Label(frame, text="", bg="#009AA5").pack(pady=5)  # Spacer
        preset_frame = tk.Frame(frame, bg="#009AA5")
        preset_frame.pack(fill="x", padx=30, pady=5)
        tk.Label(preset_frame, text="Quick Add:", bg="#009AA5", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(0,10))
        
        def add_preset(exts, name):
            for ext in exts:
                if ext not in self.user_exclusions.get_excluded_extensions():
                    self.user_exclusions.add_extension(ext)
                    self.excl_ext_listbox.insert("end", ext)
        
        tk.Button(preset_frame, text="Videos (.mp4, .avi, .mkv)", 
                 command=lambda: add_preset(['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'], "Videos"),
                 bg="#005555", fg="white", font=("Arial", 9)).pack(side="left", padx=2)
        tk.Button(preset_frame, text="Images (.jpg, .png, .gif)", 
                 command=lambda: add_preset(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'], "Images"),
                 bg="#005555", fg="white", font=("Arial", 9)).pack(side="left", padx=2)
        tk.Button(preset_frame, text="Archives (.zip, .rar, .7z)", 
                 command=lambda: add_preset(['.zip', '.rar', '.7z', '.tar', '.gz'], "Archives"),
                 bg="#005555", fg="white", font=("Arial", 9)).pack(side="left", padx=2)

        # --- Dynamic enabling/disabling logic ---
        def refresh_enable_state(*_):
            freq = self._sched_freq_var.get()
            # Time needed for hourly / twice_daily / daily
            for child in time_row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.config(state=("normal" if freq in ("hourly","twice_daily","daily") else "disabled"))
            # Custom interval entry only for custom
            for child in interval_row.winfo_children():
                if isinstance(child, tk.Entry):
                    child.config(state=("normal" if freq=="custom" else "disabled"))
        self._sched_freq_var.trace_add('write', lambda *a: refresh_enable_state())
        refresh_enable_state()

        return container

    # ---------- Scheduled Scan Progress Modal ----------
    def _ensure_sched_modal(self):
        import tkinter as tk
        if hasattr(self, '_sched_modal') and self._sched_modal.winfo_exists():
            return
        self._sched_modal = tk.Toplevel(self.root)
        self._sched_modal.title("Scheduled Scan")
        self._sched_modal.configure(bg="#004d4d")
        self._sched_modal.geometry("420x320")
        self._sched_modal.transient(self.root)
        self._sched_modal.grab_set()
        self._sched_modal_label = tk.Label(self._sched_modal, text="Starting...", bg="#004d4d", fg="white", justify="left", anchor="nw")
        self._sched_modal_label.pack(fill="both", expand=True, padx=10, pady=10)
        self._sched_modal_progress = tk.Label(self._sched_modal, text="", bg="#004d4d", fg="yellow")
        self._sched_modal_progress.pack(pady=4)
        self._sched_modal_close_btn = tk.Button(self._sched_modal, text="Close", state="disabled", command=self._sched_modal.destroy)
        self._sched_modal_close_btn.pack(pady=6)

    def _scheduled_scan_on_start(self, total):
        self._ensure_sched_modal()
        self._sched_modal_label.config(text=f"Scheduled scan started\nTotal files queued: {total}")
        self._sched_modal_progress.config(text="0 / {} (0 matches)".format(total))
        self._sched_modal_close_btn.config(state="disabled")

    def _scheduled_scan_on_progress(self, scanned, total, matches):
        if hasattr(self, '_sched_modal') and self._sched_modal.winfo_exists():
            self._sched_modal_progress.config(text=f"{scanned} / {total} ({matches} matches)")

    def _scheduled_scan_on_complete(self, summary: dict):
        if not (hasattr(self, '_sched_modal') and self._sched_modal.winfo_exists()):
            self._ensure_sched_modal()
        lines = [
            "Scheduled scan complete:",
            f"Total files: {summary.get('total_files')}",
            f"Matches: {summary.get('matches')}",
            f"Missing paths: {len(summary.get('missing_paths', []))}",
            f"Duration: {summary.get('duration_sec'):.2f}s",
            f"Ended: {summary.get('ended_at')}"
        ]
        samples = summary.get('matched_samples') or []
        if samples:
            lines.append("Sample matches:")
            for p, rule in samples[:5]:
                lines.append(f"- {os.path.basename(p)} ({rule})")
        self._sched_modal_label.config(text="\n".join(lines))
        self._sched_modal_close_btn.config(state="normal")





