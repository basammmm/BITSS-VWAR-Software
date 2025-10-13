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
        from tkinter import ttk
        
        # Main container
        container = tk.Frame(parent, bg="#009AA5")
        
        # Header
        header_frame = tk.Frame(container, bg="#006666", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="⚙️ Settings & Configuration", 
                font=("Arial", 22, "bold"), bg="#006666", fg="white").pack(pady=15)
        
        # Tabbed interface using ttk.Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.TNotebook', background='#009AA5', borderwidth=0)
        style.configure('Custom.TNotebook.Tab', 
                       background='#006666', 
                       foreground='white',
                       padding=[20, 10],
                       font=('Arial', 11, 'bold'))
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', '#009AA5')],
                 foreground=[('selected', 'white')])
        
        notebook = ttk.Notebook(container, style='Custom.TNotebook')
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create tabs
        general_tab = self._build_general_tab(notebook)
        schedule_tab = self._build_schedule_tab(notebook)
        exclusions_tab = self._build_exclusions_tab(notebook)
        
        notebook.add(general_tab, text="  🏠 General  ")
        notebook.add(schedule_tab, text="  📅 Scheduled Scans  ")
        notebook.add(exclusions_tab, text="  🚫 Exclusions  ")
        
        return container
    
    # ========== TAB 1: GENERAL SETTINGS ==========
    def _build_general_tab(self, parent):
        import tkinter as tk
        
        # Scrollable frame
        canvas = tk.Canvas(parent, bg="#009AA5", highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#009AA5")
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        ui_font = ("Arial", 11)
        section_font = ("Arial", 14, "bold")
        
        # === Application Behavior ===
        self._create_section_header(frame, "🔧 Application Behavior", section_font)
        
        settings_frame = tk.Frame(frame, bg="#007777", relief="ridge", bd=2)
        settings_frame.pack(fill="x", padx=20, pady=5)
        
        # Debug toggle
        set_debug(True)
        self._settings_debug_var = tk.BooleanVar(value=True)
        def on_debug_toggle():
            set_debug(self._settings_debug_var.get())
            global DEBUG
            DEBUG = SETTINGS.debug
        
        debug_chk = tk.Checkbutton(settings_frame, text="Enable Debug Logging", 
                                   variable=self._settings_debug_var,
                                   command=on_debug_toggle, bg="#007777", fg="white", 
                                   selectcolor="#004d4d", font=ui_font, state="disabled")
        debug_chk.pack(anchor="w", padx=15, pady=8)
        
        tk.Label(settings_frame, text="Prints detailed diagnostic information to console and log file.",
                bg="#007777", fg="#CCCCCC", font=("Arial", 9), wraplength=600, justify="left").pack(anchor="w", padx=15, pady=(0,8))
        
        # === Startup Options ===
        self._create_section_header(frame, "🚀 Startup & Tray", section_font)
        
        startup_frame = tk.Frame(frame, bg="#007777", relief="ridge", bd=2)
        startup_frame.pack(fill="x", padx=20, pady=5)
        
        # Start with Windows
        from utils.startup import is_startup_enabled, enable_startup, disable_startup
        self._startup_var = tk.BooleanVar(value=is_startup_enabled())
        def on_startup_toggle():
            if self._startup_var.get():
                ok = enable_startup()
                if not ok:
                    self._startup_var.set(False)
            else:
                disable_startup()
        
        tk.Checkbutton(startup_frame, text="Start with Windows (Run at login)", 
                      variable=self._startup_var, command=on_startup_toggle,
                      bg="#007777", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=15, pady=8)
        
        # Startup minimized
        self._startup_tray_var = tk.BooleanVar(value=SETTINGS.startup_tray)
        def on_startup_tray_toggle():
            SETTINGS.startup_tray = self._startup_tray_var.get()
        
        tk.Checkbutton(startup_frame, text="   ↳ Start minimized to system tray", 
                      variable=self._startup_tray_var, command=on_startup_tray_toggle,
                      bg="#007777", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=15, pady=4)
        
        # Minimize to tray on close
        from utils.tray import create_tray
        # ICON_PATH is already imported at top from config.py
        
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
        
        tk.Checkbutton(startup_frame, text="Minimize to tray on close (X button)", 
                      variable=self._minimize_tray_var, command=on_minimize_tray_toggle,
                      bg="#007777", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=15, pady=4)
        
        # Tray notifications
        self._tray_notify_var = tk.BooleanVar(value=SETTINGS.tray_notifications)
        def on_tray_notify_toggle():
            SETTINGS.tray_notifications = self._tray_notify_var.get()
        
        tk.Checkbutton(startup_frame, text="Show tray notifications for threats", 
                      variable=self._tray_notify_var, command=on_tray_notify_toggle,
                      bg="#007777", fg="white", selectcolor="#004d4d", font=ui_font).pack(anchor="w", padx=15, pady=(4,8))
        
        # Info note
        tk.Label(frame, text="💡 Tip: Running in the system tray keeps VWAR active without cluttering your taskbar.",
                bg="#009AA5", fg="#FFEB3B", font=("Arial", 10), wraplength=700, justify="left").pack(anchor="w", padx=20, pady=10)
        
        return canvas
    
    # ========== TAB 2: SCHEDULED SCANS ==========
    def _build_schedule_tab(self, parent):
        import tkinter as tk
        
        # Scrollable frame
        canvas = tk.Canvas(parent, bg="#009AA5", highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#009AA5")
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        ui_font = ("Arial", 11)
        section_font = ("Arial", 14, "bold")
        
        # === Schedule Configuration ===
        self._create_section_header(frame, "📅 Schedule Configuration", section_font)
        
        from Scanning.scheduled_scan import load_scan_schedule, save_scan_schedule, ScanScheduleConfig
        cfg = load_scan_schedule()
        self._sched_enabled_var = tk.BooleanVar(value=True)
        self._sched_time_var = tk.StringVar(value=cfg.time)
        self._sched_paths_var = tk.StringVar(value=";".join(cfg.paths))
        self._sched_recursive_var = tk.BooleanVar(value=cfg.include_subdirs)
        self._sched_freq_var = tk.StringVar(value=cfg.frequency)
        self._sched_interval_var = tk.StringVar(value=str(cfg.interval_minutes))
        self._sched_last_run = tk.StringVar(value=cfg.last_run or "Never")
        
        # Card-style container
        schedule_card = tk.Frame(frame, bg="#007777", relief="ridge", bd=2)
        schedule_card.pack(fill="x", padx=20, pady=5)
        
        # Frequency (Horizontal modern buttons)
        tk.Label(schedule_card, text="Scan Frequency:", bg="#007777", fg="white", 
                font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(15,8))
        
        freq_container = tk.Frame(schedule_card, bg="#007777")
        freq_container.pack(fill="x", padx=15, pady=5)
        
        for val, label, emoji in [
            ("realtime", "Realtime", "⚡"),
            ("hourly", "Hourly", "⏰"),
            ("daily", "Daily", "📅"),
            ("custom", "Custom", "⚙️")
        ]:
            tk.Radiobutton(freq_container, text=f"{emoji} {label}", value=val, 
                          variable=self._sched_freq_var,
                          bg="#007777", fg="white", selectcolor="#004d4d", 
                          font=ui_font, indicatoron=0, width=12, relief="raised", bd=2,
                          activebackground="#009AA5").pack(side="left", padx=5)
        
        # Time & Interval (Grid layout)
        config_frame = tk.Frame(schedule_card, bg="#007777")
        config_frame.pack(fill="x", padx=15, pady=10)
        
        # Time
        time_frame = tk.Frame(config_frame, bg="#007777")
        time_frame.grid(row=0, column=0, sticky="w", padx=(0,20))
        
        tk.Label(time_frame, text="⏰ Time (HH:MM):", bg="#007777", fg="white", 
                font=ui_font).pack(side="left", padx=(0,10))
        time_entry = tk.Entry(time_frame, textvariable=self._sched_time_var, width=8, 
                             font=("Arial", 12), justify="center")
        time_entry.pack(side="left")
        
        # Custom interval
        interval_frame = tk.Frame(config_frame, bg="#007777")
        interval_frame.grid(row=0, column=1, sticky="w")
        
        tk.Label(interval_frame, text="⚙️ Custom Interval:", bg="#007777", fg="white", 
                font=ui_font).pack(side="left", padx=(0,10))
        interval_entry = tk.Entry(interval_frame, textvariable=self._sched_interval_var, 
                                 width=6, font=("Arial", 12), justify="center")
        interval_entry.pack(side="left")
        tk.Label(interval_frame, text="min", bg="#007777", fg="white", 
                font=ui_font).pack(side="left", padx=(5,0))
        
        # Paths
        tk.Label(schedule_card, text="Scan Paths:", bg="#007777", fg="white", 
                font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=(15,8))
        
        path_container = tk.Frame(schedule_card, bg="#007777")
        path_container.pack(fill="x", padx=15, pady=5)
        
        path_entry = tk.Entry(path_container, textvariable=self._sched_paths_var, 
                             font=ui_font, relief="solid", bd=1)
        path_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        
        def add_dir():
            from tkinter import filedialog
            d = filedialog.askdirectory(title="Add Folder to Scan")
            if d:
                current = self._sched_paths_var.get().strip()
                self._sched_paths_var.set((current+';' if current else '') + d)
        
        tk.Button(path_container, text="📁 Add Folder", command=add_dir, 
                 bg="#009AA5", fg="white", font=("Arial", 10, "bold"), 
                 relief="raised", bd=2, cursor="hand2").pack(side="left")
        
        # Options
        tk.Checkbutton(schedule_card, text="Include subdirectories", 
                      variable=self._sched_recursive_var,
                      bg="#007777", fg="white", selectcolor="#004d4d", 
                      font=ui_font).pack(anchor="w", padx=15, pady=8)
        
        # Last run & Actions
        status_frame = tk.Frame(schedule_card, bg="#006666", relief="sunken", bd=1)
        status_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(status_frame, text="Last Run:", bg="#006666", fg="#AAAAAA", 
                font=("Arial", 9)).pack(side="left", padx=10, pady=5)
        tk.Label(status_frame, textvariable=self._sched_last_run, bg="#006666", 
                fg="#FFEB3B", font=("Arial", 9, "bold")).pack(side="left")
        
        # Feedback label
        self._sched_feedback = tk.Label(schedule_card, text="", bg="#007777", 
                                       fg="yellow", font=ui_font)
        self._sched_feedback.pack(anchor="w", padx=15, pady=(0,5))
        
        # Action buttons
        btn_container = tk.Frame(schedule_card, bg="#007777")
        btn_container.pack(fill="x", padx=15, pady=(0,15))
        
        def validate_time(t: str) -> bool:
            import re
            return bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t))
        
        def save_schedule():
            raw_time = self._sched_time_var.get().strip()
            if self._sched_freq_var.get() in ('hourly','twice_daily','daily') and not validate_time(raw_time):
                self._sched_feedback.config(text="❌ Invalid time format. Use HH:MM (24h)", fg="red")
                return
            try:
                interval_val = int(self._sched_interval_var.get())
                if interval_val <= 0:
                    raise ValueError
            except Exception:
                if self._sched_freq_var.get() == 'custom':
                    self._sched_feedback.config(text="❌ Interval must be positive integer", fg="red")
                    return
                interval_val = 1440
            
            raw_paths = [p.strip() for p in self._sched_paths_var.get().split(';') if p.strip()]
            new_cfg = ScanScheduleConfig(
                enabled=self._sched_enabled_var.get(),
                time=raw_time or '02:00',
                paths=raw_paths,
                include_subdirs=self._sched_recursive_var.get(),
                frequency=self._sched_freq_var.get(),
                interval_minutes=interval_val,
                last_run=cfg.last_run
            )
            save_scan_schedule(new_cfg)
            self.scheduled_scan_runner.reload_config()
            self._sched_feedback.config(text="✅ Schedule saved successfully!", fg="lime")
            updated = load_scan_schedule()
            self._sched_last_run.set(updated.last_run or "Never")
        
        def run_now():
            self.scheduled_scan_runner.run_now()
        
        tk.Button(btn_container, text="💾 Save Schedule", command=save_schedule, 
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), 
                 relief="raised", bd=3, cursor="hand2", width=15).pack(side="left", padx=(0,10))
        
        tk.Button(btn_container, text="▶️ Run Now", command=run_now, 
                 bg="#2196F3", fg="white", font=("Arial", 11, "bold"), 
                 relief="raised", bd=3, cursor="hand2", width=15).pack(side="left")
        
        # Dynamic state management
        def refresh_enable_state(*_):
            freq = self._sched_freq_var.get()
            time_entry.config(state=("normal" if freq in ("hourly","twice_daily","daily") else "disabled"))
            interval_entry.config(state=("normal" if freq=="custom" else "disabled"))
        
        self._sched_freq_var.trace_add('write', lambda *a: refresh_enable_state())
        refresh_enable_state()
        
        return canvas
    
    # ========== TAB 3: EXCLUSIONS ==========
    def _build_exclusions_tab(self, parent):
        import tkinter as tk
        
        # Scrollable frame
        canvas = tk.Canvas(parent, bg="#009AA5", highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#009AA5")
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        ui_font = ("Arial", 11)
        section_font = ("Arial", 14, "bold")
        
        # Import exclusions backend
        from utils.user_exclusions import UserExclusions
        self.user_exclusions = UserExclusions()
        
        # Header
        self._create_section_header(frame, "🚫 Scan Exclusions", section_font)
        
        tk.Label(frame, text="Add paths or file extensions to exclude from all scans (manual, scheduled, and real-time).", 
                bg="#009AA5", fg="white", font=("Arial", 10), wraplength=700, justify="left").pack(anchor="w", padx=20, pady=(0,15))
        
        # Two-column layout
        columns_container = tk.Frame(frame, bg="#009AA5")
        columns_container.pack(fill="both", expand=True, padx=20, pady=5)
        
        # === LEFT: Excluded Paths ===
        left_card = tk.Frame(columns_container, bg="#007777", relief="ridge", bd=2)
        left_card.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        tk.Label(left_card, text="📂 Excluded Paths", bg="#006666", fg="white", 
                font=("Arial", 13, "bold")).pack(fill="x", padx=0, pady=10)
        
        # Listbox
        paths_list_frame = tk.Frame(left_card, bg="#007777")
        paths_list_frame.pack(fill="both", expand=True, padx=15, pady=(0,10))
        
        paths_scrollbar = tk.Scrollbar(paths_list_frame)
        paths_scrollbar.pack(side="right", fill="y")
        
        self.excl_paths_listbox = tk.Listbox(paths_list_frame, yscrollcommand=paths_scrollbar.set, 
                                             height=10, bg="white", fg="black", font=ui_font,
                                             relief="solid", bd=1)
        self.excl_paths_listbox.pack(side="left", fill="both", expand=True)
        paths_scrollbar.config(command=self.excl_paths_listbox.yview)
        
        # Populate
        for path in self.user_exclusions.get_excluded_paths():
            self.excl_paths_listbox.insert("end", path)
        
        # Buttons
        paths_btn_frame = tk.Frame(left_card, bg="#007777")
        paths_btn_frame.pack(fill="x", padx=15, pady=(0,15))
        
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
        
        tk.Button(paths_btn_frame, text="📁 + Folder", command=add_path, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), 
                 width=10, cursor="hand2").pack(side="left", padx=2)
        tk.Button(paths_btn_frame, text="📄 + File", command=add_file, 
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold"), 
                 width=10, cursor="hand2").pack(side="left", padx=2)
        tk.Button(paths_btn_frame, text="🗑️ Remove", command=remove_path, 
                 bg="#F44336", fg="white", font=("Arial", 10, "bold"), 
                 width=10, cursor="hand2").pack(side="left", padx=2)
        
        # === RIGHT: Excluded Extensions ===
        right_card = tk.Frame(columns_container, bg="#007777", relief="ridge", bd=2)
        right_card.pack(side="right", fill="both", expand=True, padx=(10,0))
        
        tk.Label(right_card, text="📎 Excluded Extensions", bg="#006666", fg="white", 
                font=("Arial", 13, "bold")).pack(fill="x", padx=0, pady=10)
        
        # Listbox
        ext_list_frame = tk.Frame(right_card, bg="#007777")
        ext_list_frame.pack(fill="both", expand=True, padx=15, pady=(0,10))
        
        ext_scrollbar = tk.Scrollbar(ext_list_frame)
        ext_scrollbar.pack(side="right", fill="y")
        
        self.excl_ext_listbox = tk.Listbox(ext_list_frame, yscrollcommand=ext_scrollbar.set, 
                                           height=10, bg="white", fg="black", font=ui_font,
                                           relief="solid", bd=1)
        self.excl_ext_listbox.pack(side="left", fill="both", expand=True)
        ext_scrollbar.config(command=self.excl_ext_listbox.yview)
        
        # Populate
        for ext in self.user_exclusions.get_excluded_extensions():
            self.excl_ext_listbox.insert("end", ext)
        
        # Buttons
        ext_btn_frame = tk.Frame(right_card, bg="#007777")
        ext_btn_frame.pack(fill="x", padx=15, pady=(0,15))
        
        def add_extension():
            dialog = tk.Toplevel(self.root)
            dialog.title("Add Extension")
            dialog.geometry("350x140")
            dialog.configure(bg="#009AA5")
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Enter extension (e.g., .mp4 or mp4):", 
                    bg="#009AA5", fg="white", font=("Arial", 11)).pack(pady=15)
            entry = tk.Entry(dialog, font=("Arial", 12), width=20, justify="center")
            entry.pack(padx=20)
            entry.focus()
            
            def save_ext():
                ext = entry.get().strip()
                if ext:
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    self.user_exclusions.add_extension(ext)
                    self.excl_ext_listbox.insert("end", ext)
                dialog.destroy()
            
            tk.Button(dialog, text="Add Extension", command=save_ext, 
                     bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                     cursor="hand2").pack(pady=15)
            entry.bind('<Return>', lambda e: save_ext())
        
        def remove_extension():
            selection = self.excl_ext_listbox.curselection()
            if selection:
                idx = selection[0]
                ext = self.excl_ext_listbox.get(idx)
                self.user_exclusions.remove_extension(ext)
                self.excl_ext_listbox.delete(idx)
        
        tk.Button(ext_btn_frame, text="➕ Add Ext", command=add_extension, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), 
                 width=10, cursor="hand2").pack(side="left", padx=2)
        tk.Button(ext_btn_frame, text="🗑️ Remove", command=remove_extension, 
                 bg="#F44336", fg="white", font=("Arial", 10, "bold"), 
                 width=10, cursor="hand2").pack(side="left", padx=2)
        
        # Quick Presets
        tk.Label(frame, text="", bg="#009AA5").pack(pady=10)
        self._create_section_header(frame, "⚡ Quick Presets", ("Arial", 12, "bold"))
        
        preset_card = tk.Frame(frame, bg="#007777", relief="ridge", bd=2)
        preset_card.pack(fill="x", padx=20, pady=5)
        
        tk.Label(preset_card, text="Quickly exclude common file types:", 
                bg="#007777", fg="white", font=ui_font).pack(anchor="w", padx=15, pady=(10,5))
        
        preset_btns = tk.Frame(preset_card, bg="#007777")
        preset_btns.pack(fill="x", padx=15, pady=(5,15))
        
        def add_preset(exts, name):
            count = 0
            for ext in exts:
                if ext not in self.user_exclusions.get_excluded_extensions():
                    self.user_exclusions.add_extension(ext)
                    self.excl_ext_listbox.insert("end", ext)
                    count += 1
            if count > 0:
                self._create_toast(frame, f"✅ Added {count} {name} extensions", "lime")
        
        tk.Button(preset_btns, text="🎬 Videos (.mp4, .avi, .mkv, etc.)", 
                 command=lambda: add_preset(['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'], "video"),
                 bg="#9C27B0", fg="white", font=("Arial", 10), cursor="hand2", width=28).pack(side="left", padx=5)
        
        tk.Button(preset_btns, text="🖼️ Images (.jpg, .png, .gif, etc.)", 
                 command=lambda: add_preset(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico'], "image"),
                 bg="#FF9800", fg="white", font=("Arial", 10), cursor="hand2", width=28).pack(side="left", padx=5)
        
        tk.Button(preset_btns, text="📦 Archives (.zip, .rar, .7z, etc.)", 
                 command=lambda: add_preset(['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'], "archive"),
                 bg="#795548", fg="white", font=("Arial", 10), cursor="hand2", width=28).pack(side="left", padx=5)
        
        return canvas
    
    # ========== HELPER METHODS ==========
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





