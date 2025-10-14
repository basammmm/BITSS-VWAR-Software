import os
import json
import ctypes

from tkinter import Tk, Frame, Label, Button, LabelFrame
from tkinterdnd2 import TkinterDnD
from config import ICON_PATH, ACTIVATION_FILE, QUARANTINE_FOLDER
from Scanning.scan_page import ScanPage, enable_drag_drop_for_elevated_window
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
from utils.notify import init_app_notifier, notify_app
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

        # Initialize global in-app notifier (unique toast system)
        try:
            init_app_notifier(self.root)
            notify_app("VWAR", "Notifications are enabled.", severity="success", duration_ms=1800)
        except Exception:
            pass

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
        
        # Enable drag-drop for elevated window
        try:
            self.root.update_idletasks()  # Ensure window is created
            window_id = self.root.winfo_id()
            if window_id:
                enable_drag_drop_for_elevated_window(window_id)
        except Exception as e:
            print(f"[WARNING] Could not enable drag-drop for main window: {e}")
    
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
        
        # Main container with single scrollbar
        container = tk.Frame(parent, bg="#009AA5")
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(container, bg="#009AA5", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, width=14, 
                                bg="#007777", troughcolor="#009AA5", activebackground="#00CCCC")
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
        
        # Use scrollable_frame as parent
        frame = scrollable_frame
        ui_font = ("Arial", 11)
        
        # === HEADER ===
        header = tk.Frame(frame, bg="#006666", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚙️ Settings", font=("Arial", 28, "bold"), 
                bg="#006666", fg="white").pack(pady=15)
        
        # Build all sections
        self._build_app_behavior_section(frame, ui_font)
        self._build_startup_tray_section(frame, ui_font)
        self._build_scheduled_scan_section(frame, ui_font)
        self._build_scan_exclusions_section(frame, ui_font)
        
        # Footer spacer
        tk.Frame(frame, bg="#009AA5", height=30).pack()
        
        return container
    
    def _build_app_behavior_section(self, parent, ui_font):
        """Application Behavior Section"""
        import tkinter as tk
        
        # Section header
        header = tk.Frame(parent, bg="#007777", height=50)
        header.pack(fill="x", pady=(15,0))
        header.pack_propagate(False)
        tk.Label(header, text="🔧  Application Behavior", font=("Arial", 14, "bold"),
                bg="#007777", fg="white").pack(side="left", padx=20, pady=12)
        
        # Content
        content = tk.Frame(parent, bg="#008888")
        content.pack(fill="x", pady=(0,15))
        
        # Debug logging
        set_debug(True)
        self._settings_debug_var = tk.BooleanVar(value=True)
        def on_debug_toggle():
            set_debug(self._settings_debug_var.get())
        
        chk = tk.Checkbutton(content, text="Enable Debug Logging", 
                            variable=self._settings_debug_var,
                            command=on_debug_toggle, bg="#008888", fg="white",
                            selectcolor="#006666", font=ui_font, activebackground="#008888")
        chk.pack(anchor="w", padx=20, pady=(12,5))
        chk.config(state="disabled")
        
        tk.Label(content, text="Prints detailed diagnostic information to console and log file.",
                bg="#008888", fg="#CCFFFF", font=("Arial", 9), wraplength=700, 
                justify="left").pack(anchor="w", padx=45, pady=(0,12))
    
    def _build_startup_tray_section(self, parent, ui_font):
        """Startup & System Tray Section"""
        import tkinter as tk
        from utils.startup import enable_startup, disable_startup, is_startup_enabled
        from utils.settings import SETTINGS
        from utils.tray import create_tray
        
        # Section header
        header = tk.Frame(parent, bg="#007777", height=50)
        header.pack(fill="x", pady=(0,0))
        header.pack_propagate(False)
        tk.Label(header, text="🚀  Startup & System Tray", font=("Arial", 14, "bold"),
                bg="#007777", fg="white").pack(side="left", padx=20, pady=12)
        
        # Content
        content = tk.Frame(parent, bg="#008888")
        content.pack(fill="x", pady=(0,15))
        
        # Start with Windows
        self._startup_var = tk.BooleanVar(value=is_startup_enabled())
        def on_startup_toggle():
            if self._startup_var.get():
                enable_startup()
            else:
                disable_startup()
        
        tk.Checkbutton(content, text="Start with Windows (Run at login)", 
                      variable=self._startup_var, command=on_startup_toggle,
                      bg="#008888", fg="white", selectcolor="#006666", 
                      font=ui_font, activebackground="#008888").pack(anchor="w", padx=20, pady=(12,5))
        
        # Start minimized to tray
        self._startup_tray_var = tk.BooleanVar(value=SETTINGS.startup_tray)
        def on_startup_tray_toggle():
            SETTINGS.startup_tray = self._startup_tray_var.get()
        
        tk.Checkbutton(content, text="  ↳  Start minimized to system tray", 
                      variable=self._startup_tray_var, command=on_startup_tray_toggle,
                      bg="#008888", fg="#CCFFFF", selectcolor="#006666", 
                      font=("Arial", 10), activebackground="#008888").pack(anchor="w", padx=40, pady=3)
        
        # Minimize to tray on close
        self._minimize_tray_var = tk.BooleanVar(value=self.minimize_to_tray)
        def on_minimize_tray_toggle():
            self.minimize_to_tray = self._minimize_tray_var.get()
            SETTINGS.minimize_to_tray = self.minimize_to_tray
            if self.minimize_to_tray and not self.tray_icon:
                self.tray_icon = create_tray(
                    on_restore=self.restore_from_tray,
                    on_exit=self.exit_app,
                    icon_path=ICON_PATH,
                    tooltip="VWAR Scanner - Running in background",
                    on_scan_now=self.tray_scan_now
                )
        
        tk.Checkbutton(content, text="Minimize to tray on close (X button)", 
                      variable=self._minimize_tray_var, command=on_minimize_tray_toggle,
                      bg="#008888", fg="white", selectcolor="#006666", 
                      font=ui_font, activebackground="#008888").pack(anchor="w", padx=20, pady=5)
        
        # Show tray notifications
        self._tray_notify_var = tk.BooleanVar(value=SETTINGS.tray_notifications)
        def on_tray_notify_toggle():
            SETTINGS.tray_notifications = self._tray_notify_var.get()
        
        tk.Checkbutton(content, text="Show tray notifications for threats", 
                      variable=self._tray_notify_var, command=on_tray_notify_toggle,
                      bg="#008888", fg="white", selectcolor="#006666", 
                      font=ui_font, activebackground="#008888").pack(anchor="w", padx=20, pady=(5,12))
    
    def _build_scheduled_scan_section(self, parent, ui_font):
        """Scheduled Scanning Section"""
        import tkinter as tk
        from Scanning.scheduled_scan import load_scan_schedule, save_scan_schedule, ScanScheduleConfig
        
        # Section header
        header = tk.Frame(parent, bg="#007777", height=50)
        header.pack(fill="x", pady=(0,0))
        header.pack_propagate(False)
        tk.Label(header, text="📅  Scheduled Scanning", font=("Arial", 14, "bold"),
                bg="#007777", fg="white").pack(side="left", padx=20, pady=12)
        
        # Content
        content = tk.Frame(parent, bg="#008888")
        content.pack(fill="x", pady=(0,15))
        
        # Load config
        cfg = load_scan_schedule()
        self._sched_enabled_var = tk.BooleanVar(value=True)
        self._sched_time_var = tk.StringVar(value=cfg.time)
        self._sched_paths_var = tk.StringVar(value=";".join(cfg.paths))
        self._sched_recursive_var = tk.BooleanVar(value=cfg.include_subdirs)
        self._sched_freq_var = tk.StringVar(value=cfg.frequency)
        self._sched_interval_var = tk.StringVar(value=str(cfg.interval_minutes))
        self._sched_last_run = tk.StringVar(value=cfg.last_run or "Never")
        
        # Frequency
        freq_frame = tk.Frame(content, bg="#008888")
        freq_frame.pack(fill="x", padx=20, pady=(12,8))
        tk.Label(freq_frame, text="Frequency:", bg="#008888", fg="white", 
                font=("Arial", 11, "bold")).pack(side="left", padx=(0,15))
        
        for val, label in [("realtime","Realtime"), ("hourly","Hourly"), 
                          ("twice_daily","Twice Daily"), ("daily","Daily"), ("custom","Custom")]:
            tk.Radiobutton(freq_frame, text=label, value=val, variable=self._sched_freq_var,
                          bg="#008888", fg="white", selectcolor="#006666", 
                          font=ui_font, activebackground="#008888").pack(side="left", padx=8)
        
        # Time
        time_frame = tk.Frame(content, bg="#008888")
        time_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(time_frame, text="Time (HH:MM 24h):", bg="#008888", fg="white", 
                font=ui_font).pack(side="left", padx=(0,10))
        tk.Entry(time_frame, textvariable=self._sched_time_var, width=10, 
                font=("Arial", 11), bg="white", fg="#333").pack(side="left")
        
        # Custom interval
        interval_frame = tk.Frame(content, bg="#008888")
        interval_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(interval_frame, text="Custom Interval (minutes):", bg="#008888", fg="white", 
                font=ui_font).pack(side="left", padx=(0,10))
        tk.Entry(interval_frame, textvariable=self._sched_interval_var, width=10, 
                font=("Arial", 11), bg="white", fg="#333").pack(side="left")
        
        # Scan Paths with folder picker
        tk.Label(content, text="Scan Paths:", bg="#008888", fg="white", 
                font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(12,5))
        
        path_frame = tk.Frame(content, bg="#008888")
        path_frame.pack(fill="x", padx=20, pady=5)
        
        # Listbox to show paths
        path_list_frame = tk.Frame(path_frame, bg="#008888")
        path_list_frame.pack(fill="x", pady=(0,8))
        
        path_scrollbar = tk.Scrollbar(path_list_frame, orient="vertical", bg="#006666")
        path_scrollbar.pack(side="right", fill="y")
        
        self._sched_paths_list = tk.Listbox(path_list_frame, height=3, bg="white", fg="#333",
                                            font=("Consolas", 9), yscrollcommand=path_scrollbar.set)
        self._sched_paths_list.pack(side="left", fill="x", expand=True)
        path_scrollbar.config(command=self._sched_paths_list.yview)
        
        # Populate existing paths
        for path in cfg.paths:
            if path:
                self._sched_paths_list.insert("end", path)
        
        # Update string var when list changes
        def update_paths_var():
            paths = [self._sched_paths_list.get(i) for i in range(self._sched_paths_list.size())]
            self._sched_paths_var.set(";".join(paths))
        
        # Path buttons
        path_btn_frame = tk.Frame(path_frame, bg="#008888")
        path_btn_frame.pack(fill="x")
        
        def add_folder():
            from tkinter import filedialog
            folder = filedialog.askdirectory(title="Select Folder to Scan")
            if folder:
                self._sched_paths_list.insert("end", folder)
                update_paths_var()
        
        def remove_path():
            selection = self._sched_paths_list.curselection()
            if selection:
                self._sched_paths_list.delete(selection[0])
                update_paths_var()
        
        def clear_all():
            self._sched_paths_list.delete(0, "end")
            update_paths_var()
        
        tk.Button(path_btn_frame, text="📁 Add Folder", command=add_folder, 
                 bg="#006666", fg="white", font=("Arial", 10, "bold"), 
                 cursor="hand2", relief="raised", bd=2, padx=12, pady=5).pack(side="left", padx=(0,8))
        tk.Button(path_btn_frame, text="✖ Remove Selected", command=remove_path, 
                 bg="#AA4444", fg="white", font=("Arial", 10), 
                 cursor="hand2", relief="raised", bd=2, padx=12, pady=5).pack(side="left", padx=(0,8))
        tk.Button(path_btn_frame, text="Clear All", command=clear_all, 
                 bg="#666666", fg="white", font=("Arial", 10), 
                 cursor="hand2", relief="raised", bd=2, padx=12, pady=5).pack(side="left")
        
        # Include subdirectories
        tk.Checkbutton(content, text="Include subdirectories", variable=self._sched_recursive_var,
                      bg="#008888", fg="white", selectcolor="#006666", 
                      font=ui_font, activebackground="#008888").pack(anchor="w", padx=20, pady=8)
        
        # Last run
        last_run_frame = tk.Frame(content, bg="#008888")
        last_run_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(last_run_frame, text="Last Run:", bg="#008888", fg="#CCFFFF", 
                font=ui_font).pack(side="left", padx=(0,10))
        tk.Label(last_run_frame, textvariable=self._sched_last_run, bg="#008888", 
                fg="yellow", font=("Arial", 11, "bold")).pack(side="left")
        
        # Feedback label
        self._sched_feedback = tk.Label(content, text="", bg="#008888", fg="yellow", font=ui_font)
        self._sched_feedback.pack(anchor="w", padx=20, pady=5)
        
        # Save & Run buttons
        btn_frame = tk.Frame(content, bg="#008888")
        btn_frame.pack(fill="x", padx=20, pady=(8,12))
        
        def save_schedule():
            import re
            update_paths_var()  # Ensure paths are synced
            raw_time = self._sched_time_var.get().strip()
            if self._sched_freq_var.get() in ('hourly','twice_daily','daily'):
                if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", raw_time):
                    self._sched_feedback.config(text="❌ Invalid time format. Use HH:MM (24h)", fg="#FF6666")
                    return
            try:
                interval_val = int(self._sched_interval_var.get())
                if interval_val <= 0:
                    raise ValueError
            except:
                if self._sched_freq_var.get() == 'custom':
                    self._sched_feedback.config(text="❌ Interval must be positive integer", fg="#FF6666")
                    return
                interval_val = 1440
            
            raw_paths = [p.strip() for p in self._sched_paths_var.get().split(';') if p.strip()]
            new_cfg = ScanScheduleConfig(
                enabled=self._sched_enabled_var.get(),
                time=raw_time or '02:00',
                paths=raw_paths,
                include_subdirs=self._sched_recursive_var.get(),
                frequency=self._sched_freq_var.get(),
                interval_minutes=interval_val
            )
            save_scan_schedule(new_cfg)
            self.scheduled_scan_runner.reload_schedule()
            updated = self.scheduled_scan_runner.get_schedule()
            self._sched_last_run.set(updated.last_run or "Never")
            self._sched_feedback.config(text="✓ Schedule saved successfully", fg="#66FF66")
        
        def run_now():
            self.scheduled_scan_runner.run_now()
            self._sched_feedback.config(text="✓ Scan started...", fg="#66FF66")
        
        tk.Button(btn_frame, text="💾 Save Schedule", command=save_schedule, 
                 bg="#006666", fg="white", font=("Arial", 11, "bold"), 
                 cursor="hand2", relief="raised", bd=3, padx=20, pady=8).pack(side="left", padx=(0,12))
        tk.Button(btn_frame, text="▶ Run Now", command=run_now, 
                 bg="#007700", fg="white", font=("Arial", 11, "bold"), 
                 cursor="hand2", relief="raised", bd=3, padx=20, pady=8).pack(side="left")
        
        # Dynamic enabling/disabling
        def refresh_enable_state(*_):
            freq = self._sched_freq_var.get()
            for child in time_frame.winfo_children():
                if isinstance(child, tk.Entry):
                    child.config(state=("normal" if freq in ("hourly","twice_daily","daily") else "disabled"))
            for child in interval_frame.winfo_children():
                if isinstance(child, tk.Entry):
                    child.config(state=("normal" if freq=="custom" else "disabled"))
        
        self._sched_freq_var.trace_add('write', lambda *a: refresh_enable_state())
        refresh_enable_state()
    
    def _build_scan_exclusions_section(self, parent, ui_font):
        """Scan Exclusions Section"""
        import tkinter as tk
        from utils.user_exclusions import UserExclusions
        
        # Section header
        header = tk.Frame(parent, bg="#007777", height=50)
        header.pack(fill="x", pady=(0,0))
        header.pack_propagate(False)
        tk.Label(header, text="🚫  Scan Exclusions", font=("Arial", 14, "bold"),
                bg="#007777", fg="white").pack(side="left", padx=20, pady=12)
        
        # Content
        content = tk.Frame(parent, bg="#008888")
        content.pack(fill="x", pady=(0,15))
        
        tk.Label(content, text="Exclude specific paths or file extensions from all scans.",
                bg="#008888", fg="#CCFFFF", font=("Arial", 9)).pack(anchor="w", padx=20, pady=(12,8))
        
        self.user_exclusions = UserExclusions()
        
        # Two columns
        cols_frame = tk.Frame(content, bg="#008888")
        cols_frame.pack(fill="x", padx=20, pady=5)
        
        # LEFT: Paths
        left_col = tk.Frame(cols_frame, bg="#008888")
        left_col.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        tk.Label(left_col, text="Excluded Paths", bg="#008888", fg="white", 
                font=("Arial", 11, "bold")).pack(anchor="w", pady=(0,5))
        
        # Paths listbox
        paths_list_frame = tk.Frame(left_col, bg="#008888")
        paths_list_frame.pack(fill="both", expand=True)
        
        paths_scroll = tk.Scrollbar(paths_list_frame, bg="#006666")
        paths_scroll.pack(side="right", fill="y")
        
        self.excl_paths_list = tk.Listbox(paths_list_frame, height=5, bg="white", fg="#333", 
                                          font=("Consolas", 9), yscrollcommand=paths_scroll.set)
        self.excl_paths_list.pack(side="left", fill="both", expand=True)
        paths_scroll.config(command=self.excl_paths_list.yview)
        
        # Populate paths
        for path in self.user_exclusions.get_excluded_paths():
            self.excl_paths_list.insert("end", path)
        
        # Paths buttons
        paths_btn = tk.Frame(left_col, bg="#008888")
        paths_btn.pack(fill="x", pady=(8,0))
        
        def add_folder_excl():
            from tkinter import filedialog
            path = filedialog.askdirectory(title="Exclude Folder from Scans")
            if path:
                self.user_exclusions.add_path(path)
                self.excl_paths_list.insert("end", path)
        
        def add_file_excl():
            from tkinter import filedialog
            path = filedialog.askopenfilename(title="Exclude File from Scans")
            if path:
                self.user_exclusions.add_path(path)
                self.excl_paths_list.insert("end", path)
        
        def remove_path_excl():
            selection = self.excl_paths_list.curselection()
            if selection:
                idx = selection[0]
                path = self.excl_paths_list.get(idx)
                self.user_exclusions.remove_path(path)
                self.excl_paths_list.delete(idx)
        
        tk.Button(paths_btn, text="+ Folder", command=add_folder_excl, bg="#006666", fg="white",
                 font=("Arial", 9), cursor="hand2", relief="raised", bd=2, padx=10, pady=4).pack(side="left", padx=(0,5))
        tk.Button(paths_btn, text="+ File", command=add_file_excl, bg="#006666", fg="white",
                 font=("Arial", 9), cursor="hand2", relief="raised", bd=2, padx=10, pady=4).pack(side="left", padx=(0,5))
        tk.Button(paths_btn, text="✖ Remove", command=remove_path_excl, bg="#AA4444", fg="white",
                 font=("Arial", 9), cursor="hand2", relief="raised", bd=2, padx=10, pady=4).pack(side="left")
        
        # RIGHT: Extensions
        right_col = tk.Frame(cols_frame, bg="#008888")
        right_col.pack(side="right", fill="both", expand=True, padx=(10,0))
        
        tk.Label(right_col, text="Excluded Extensions", bg="#008888", fg="white", 
                font=("Arial", 11, "bold")).pack(anchor="w", pady=(0,5))
        
        # Extensions listbox
        ext_list_frame = tk.Frame(right_col, bg="#008888")
        ext_list_frame.pack(fill="both", expand=True)
        
        ext_scroll = tk.Scrollbar(ext_list_frame, bg="#006666")
        ext_scroll.pack(side="right", fill="y")
        
        self.excl_ext_list = tk.Listbox(ext_list_frame, height=5, bg="white", fg="#333", 
                                        font=("Consolas", 9), yscrollcommand=ext_scroll.set)
        self.excl_ext_list.pack(side="left", fill="both", expand=True)
        ext_scroll.config(command=self.excl_ext_list.yview)
        
        # Populate extensions
        for ext in self.user_exclusions.get_excluded_extensions():
            self.excl_ext_list.insert("end", ext)
        
        # Extension buttons
        ext_btn = tk.Frame(right_col, bg="#008888")
        ext_btn.pack(fill="x", pady=(8,0))
        
        def add_extension_excl():
            dialog = tk.Toplevel(self.root)
            dialog.title("Add Extension to Exclude")
            dialog.geometry("350x150")
            dialog.configure(bg="#009AA5")
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Enter extension (e.g., .mp4 or mp4):", 
                    bg="#009AA5", fg="white", font=("Arial", 11)).pack(pady=15, padx=20)
            entry = tk.Entry(dialog, font=("Arial", 11), width=25)
            entry.pack(padx=20, fill="x")
            entry.focus()
            
            def save_ext():
                ext = entry.get().strip()
                if ext:
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    self.user_exclusions.add_extension(ext)
                    self.excl_ext_list.insert("end", ext)
                dialog.destroy()
            
            tk.Button(dialog, text="Add Extension", command=save_ext, bg="#006666", fg="white",
                     font=("Arial", 10, "bold"), cursor="hand2", relief="raised", 
                     bd=2, padx=20, pady=8).pack(pady=15)
            entry.bind('<Return>', lambda e: save_ext())
        
        def remove_extension_excl():
            selection = self.excl_ext_list.curselection()
            if selection:
                idx = selection[0]
                ext = self.excl_ext_list.get(idx)
                self.user_exclusions.remove_extension(ext)
                self.excl_ext_list.delete(idx)
        
        tk.Button(ext_btn, text="+ Add Extension", command=add_extension_excl, bg="#006666", fg="white",
                 font=("Arial", 9), cursor="hand2", relief="raised", bd=2, padx=10, pady=4).pack(side="left", padx=(0,5))
        tk.Button(ext_btn, text="✖ Remove", command=remove_extension_excl, bg="#AA4444", fg="white",
                 font=("Arial", 9), cursor="hand2", relief="raised", bd=2, padx=10, pady=4).pack(side="left")
        
        # Quick Presets
        tk.Label(content, text="Quick Presets:", bg="#008888", fg="white", 
                font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15,5))
        
        preset_frame = tk.Frame(content, bg="#008888")
        preset_frame.pack(fill="x", padx=20, pady=(0,12))
        
        def add_preset(exts):
            for ext in exts:
                if ext not in self.user_exclusions.get_excluded_extensions():
                    self.user_exclusions.add_extension(ext)
                    self.excl_ext_list.insert("end", ext)
        
        tk.Button(preset_frame, text="🎬 Videos", 
                 command=lambda: add_preset(['.mp4', '.avi', '.mkv', '.mov', '.wmv']),
                 bg="#006666", fg="white", font=("Arial", 9, "bold"), cursor="hand2", 
                 relief="raised", bd=2, padx=12, pady=6).pack(side="left", padx=(0,8))
        tk.Button(preset_frame, text="🖼️ Images", 
                 command=lambda: add_preset(['.jpg', '.jpeg', '.png', '.gif', '.bmp']),
                 bg="#006666", fg="white", font=("Arial", 9, "bold"), cursor="hand2", 
                 relief="raised", bd=2, padx=12, pady=6).pack(side="left", padx=(0,8))
        tk.Button(preset_frame, text="📦 Archives", 
                 command=lambda: add_preset(['.zip', '.rar', '.7z', '.tar', '.gz']),
                 bg="#006666", fg="white", font=("Arial", 9, "bold"), cursor="hand2", 
                 relief="raised", bd=2, padx=12, pady=6).pack(side="left")

    # ---------- Toast Notification Helper ----------
    def _show_toast(self, parent, message):
        """Show a toast notification"""
        import tkinter as tk
        toast = tk.Label(parent, text=message, bg="#00CC00", fg="white", 
                        font=("Arial", 10, "bold"), relief="raised", bd=2)
        toast.place(relx=0.5, rely=0.1, anchor="center")
        parent.after(2000, toast.destroy)

    # ---------- Scheduled Scan Progress Modal ----------
    def _ensure_sched_modal(self):
        import tkinter as tk
        if hasattr(self, '_sched_modal') and self._sched_modal.winfo_exists():
            return
        self._sched_modal = tk.Toplevel(self.root)
        self._sched_modal.title("Scheduled Scan")

    # ---------- Section Header Helper ----------
    def _create_section_header(self, parent, text, font):
        """Create a styled section header"""
        import tkinter as tk
        header_frame = tk.Frame(parent, bg="#006666", relief="raised", bd=1, height=40)
        header_frame.pack(fill="x", padx=15, pady=(15,10))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=text, font=font, bg="#006666", fg="white").pack(pady=8, padx=15, anchor="w")
    
    def _create_toast(self, parent, message, color):
        """Show a temporary toast notification"""
        import tkinter as tk
        toast = tk.Label(parent, text=message, bg=color, fg="black", 
                        font=("Arial", 10, "bold"), relief="raised", bd=2)
        toast.place(relx=0.5, rely=0.1, anchor="center")
        parent.after(2000, toast.destroy)

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

    def update_sched_modal(self, message):
        if hasattr(self, '_sched_modal_label') and self._sched_modal_label.winfo_exists():
            self._sched_modal_label.config(text=message)
    
    def complete_sched_modal(self, final_message, threat_count):
        if hasattr(self, '_sched_modal') and self._sched_modal.winfo_exists():
            self._sched_modal_label.config(text=final_message)
            self._sched_modal_progress.config(text=f"Threats found: {threat_count}")
            self._sched_modal_close_btn.config(state="normal")

    # ---------- Section Header Helper ----------
    def _create_section_header(self, parent, text, font):
        """Create a styled section header"""
        import tkinter as tk
        header_frame = tk.Frame(parent, bg="#006666", relief="raised", bd=1, height=40)
        header_frame.pack(fill="x", padx=15, pady=(15,10))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=text, font=font, bg="#006666", fg="white").pack(pady=8, padx=15, anchor="w")
    
    def _create_toast(self, parent, message, color):
        """Show a temporary toast notification"""
        import tkinter as tk
        toast = tk.Label(parent, text=message, bg=color, fg="black", 
                        font=("Arial", 10, "bold"), relief="raised", bd=2)
        toast.place(relx=0.5, rely=0.1, anchor="center")
        parent.after(2000, toast.destroy)

    # ---------- Section Header Helper ----------
    def _create_section_header(self, parent, text, font):
        """Create a styled section header"""
        import tkinter as tk
        header_frame = tk.Frame(parent, bg="#006666", relief="raised", bd=1, height=40)
        header_frame.pack(fill="x", padx=15, pady=(15,10))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=text, font=font, bg="#006666", fg="white").pack(pady=8, padx=15, anchor="w")
    
    def _create_toast(self, parent, message, color):
        """Show a temporary toast notification"""
        import tkinter as tk
        toast = tk.Label(parent, text=message, bg=color, fg="black", 
                        font=("Arial", 10, "bold"), relief="raised", bd=2)
        toast.place(relx=0.5, rely=0.1, anchor="center")
        parent.after(2000, toast.destroy)

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
        try:
            notify_app("Scheduled Scan", f"Started (Total: {total})", severity="info", duration_ms=2200)
        except Exception:
            pass

    def _scheduled_scan_on_progress(self, scanned, total, matches):
        if hasattr(self, '_sched_modal_progress') and self._sched_modal_progress.winfo_exists():
            self._sched_modal_progress.config(text=f"{scanned} / {total} ({matches} matches)")

    def _scheduled_scan_on_complete(self, summary):
        if not hasattr(self, '_sched_modal') or not self._sched_modal.winfo_exists():
            return
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
                import os
                lines.append(f"- {os.path.basename(p)} ({rule})")
        self._sched_modal_label.config(text="\n".join(lines))
        self._sched_modal_close_btn.config(state="normal")
        try:
            sev = "critical" if (summary.get('matches') or 0) > 0 else "success"
            msg = f"Files: {summary.get('total_files')}  Matches: {summary.get('matches')}"
            notify_app("Scheduled Scan Complete", msg, severity=sev, duration_ms=3000)
        except Exception:
            pass
