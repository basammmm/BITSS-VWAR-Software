import os
import sys
import ctypes
import tkinter as tk
from activation.license_utils import is_activated
from activation.gui import show_activation_window
from app_main import VWARScannerGUI
from utils.update_checker import check_for_updates
from tkinter import messagebox
import subprocess
import time
import argparse
from utils.startup import is_startup_enabled
from utils.tray import create_tray
from config import ICON_PATH

def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunch the script with admin rights if not already."""
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)

def already_running():
    """Check if VWAR.exe is already running."""
    try:
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq VWAR.exe"], stdout=subprocess.PIPE, text=True)
        lines = result.stdout.strip().splitlines()
        process_lines = [line for line in lines if "VWAR.exe" in line]
        if len(process_lines) > 2:  # More than one instance
            return True
    except Exception as e:
        print(f"[WARNING] Failed to check running tasks: {e}")
    return False

def check_exe_name():
    """Ensure executable is named correctly."""
    exe_name = os.path.basename(sys.argv[0])
    if exe_name.lower() != "vwar.exe":
        messagebox.showerror("Invalid File", "Executable must be named VWAR.exe")
        sys.exit()

def run_vwar_monitor():
    """Start the C++ monitor process silently."""
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle
        base_path = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
    else:
        # Dev mode
        base_path = os.path.dirname(os.path.abspath(__file__))

    monitor_path = os.path.join(base_path, "vwar_monitor.exe")

    if os.path.exists(monitor_path):
        try:
            subprocess.Popen(
                [monitor_path],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("[INFO] VWAR Monitor started.")
        except Exception as e:
            print("[ERROR] Failed to start VWAR Monitor:", e)
    else:
        print("[WARNING] VWAR Monitor not found:", monitor_path)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--silent", action="store_true", help="Run services only (no GUI)")
    parser.add_argument("--tray", action="store_true", help="Start minimized to system tray")
    parser.add_argument("--help", action="store_true", help="Show help and exit")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("VWAR Scanner options:\n  --silent   Run background services only (monitor, scheduler)\n  --tray     Start to system tray; GUI shown when icon clicked\n  --help     Show this help")
        return
    # check_exe_name()
    if already_running():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("VWAR Scanner", "VWAR is already running.")
        sys.exit()

    # Step 1: Elevate to admin
    if not is_admin():
        print("[INFO] Not running as admin. Relaunching...")
        run_as_admin()
        return

    # Step 2: Check activation
    activated, reason = is_activated()
    if not activated:
        print(f"[INFO] Activation check failed: {reason}")
        show_activation_window(reason=reason)
        return

    # Step 3: Check for updates
    check_for_updates()

    # Step 4: Start background monitor
    run_vwar_monitor()

    # Step 5: Launch main GUI unless --silent
    if args.silent:
        print("[INFO] Silent mode: GUI not started (services running if any threads started in imports).")
        # Keep process alive minimally for scheduled scanning / monitoring; spin sleep loop
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            return
    else:
        # Normal mode: Create GUI with system tray integration
        print("[INFO] Launching VWAR Scanner GUI with system tray...")
        root = tk.Tk()
        
        # Start minimized to tray if --tray flag is set
        if args.tray:
            root.withdraw()
        
        app = VWARScannerGUI(root)
        
        # Create tray icon functions
        def restore():
            try:
                root.deiconify()
                root.state('normal')
                root.after(0, lambda: root.lift())
                root.focus_force()
            except Exception as e:
                print(f"[TRAY] Restore failed: {e}")
        
        def exit_app():
            try:
                # Stop monitoring and cleanup
                if hasattr(app, 'on_close'):
                    app.on_close()
                root.quit()
            finally:
                os._exit(0)
        
        def scan_now():
            try:
                # Restore window first
                restore()
                # Show scan page
                if hasattr(app, 'pages') and "scan" in app.pages:
                    app.show_page("scan")
            except Exception as e:
                print(f"[TRAY] Scan now failed: {e}")
        
        # Create system tray icon
        tray = create_tray(restore, exit_app, ICON_PATH, on_scan_now=scan_now)
        
        # Store tray reference in app for access
        app.tray_icon = tray
        
        root.mainloop()

if __name__ == "__main__":
    main()

