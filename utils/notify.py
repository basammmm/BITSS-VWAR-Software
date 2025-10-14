from utils.logger import log_message
from utils.path_utils import resource_path

# Optional backends imported at module level so packagers (PyInstaller) pick them up
try:
    from plyer import notification as _plyer_notification  # type: ignore
except Exception:  # pragma: no cover
    _plyer_notification = None  # type: ignore

try:
    from win10toast import ToastNotifier as _ToastNotifier  # type: ignore
except Exception:  # pragma: no cover
    _ToastNotifier = None  # type: ignore

# Optional pywin32 for balloon fallback
try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    import win32gui_struct  # type: ignore
    
    # Define missing constants if not present (pywin32 version issue)
    if not hasattr(win32con, 'NIF_ICON'):
        win32con.NIF_ICON = 0x00000002
    if not hasattr(win32con, 'NIF_MESSAGE'):
        win32con.NIF_MESSAGE = 0x00000001
    if not hasattr(win32con, 'NIF_TIP'):
        win32con.NIF_TIP = 0x00000004
    if not hasattr(win32con, 'NIF_INFO'):
        win32con.NIF_INFO = 0x00000010
except Exception:  # pragma: no cover
    win32api = win32con = win32gui = win32gui_struct = None  # type: ignore

def _icon_path() -> str | None:
    """Resolve app icon in both dev and PyInstaller runtime."""
    try:
        icon = resource_path("assets/VWAR.ico")
        return icon if icon and os.path.exists(icon) else None
    except Exception:
        return None


import os


def notify(title: str, message: str, duration: int = 10) -> bool:
    """Send a desktop notification.

    Tries multiple backends in order:
    1) plyer (cross-platform)
    2) win10toast (Windows toast)

    Returns True on success, False otherwise. Logs any errors.
    """
    icon = _icon_path()

    # Backend 1: plyer
    try:
        if _plyer_notification is not None:
            # Some plyer backends accept app_icon; ignore if not supported
            kwargs = {"title": title, "message": message, "timeout": duration}
            if icon:
                kwargs["app_icon"] = icon  # type: ignore[assignment]
            _plyer_notification.notify(**kwargs)
            log_message("[NOTIFY] Dispatched via plyer")
            return True
    except Exception as e:
        log_message(f"[NOTIFY][plyer] failed: {e}")

    # Backend 2: win10toast (non-blocking)
    try:
        if _ToastNotifier is not None:
            toaster = _ToastNotifier()
            # threaded=True to avoid blocking; this returns immediately
            ok = toaster.show_toast(title, message, icon_path=icon, duration=duration, threaded=True)
            if ok is None:
                # Some versions return None; we treat as best-effort success
                log_message("[NOTIFY] Dispatched via win10toast (threaded)")
                return True
            if ok:
                log_message("[NOTIFY] Dispatched via win10toast")
                return True
    except Exception as e:
        log_message(f"[NOTIFY][win10toast] failed: {e}")

    # Backend 3: Windows tray balloon via pywin32
    try:
        if win32gui is not None:
            # Create a temporary, hidden window with tray icon and show a balloon
            class_name = "VWARNotifyClass"
            message_map = {win32con.WM_DESTROY: (lambda h, m, w, l: None)}  # type: ignore
            wc = win32gui.WNDCLASS()  # type: ignore
            hinst = wc.hInstance = win32api.GetModuleHandle(None)  # type: ignore
            wc.lpszClassName = class_name
            wc.lpfnWndProc = message_map  # type: ignore
            try:
                atom = win32gui.RegisterClass(wc)  # type: ignore
            except Exception:
                atom = win32gui.GetClassInfo(hinst, class_name)  # type: ignore
            hwnd = win32gui.CreateWindowEx(0, atom, "VWARNotifyWnd", 0, 0, 0, 0, 0, 0, 0, hinst, None)  # type: ignore
            # Load icon
            try:
                hicon = win32gui.LoadImage(hinst, icon, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE) if icon else win32gui.LoadIcon(0, win32con.IDI_APPLICATION)  # type: ignore
            except Exception:
                hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)  # type: ignore
            flags = win32con.NIF_ICON | win32con.NIF_MESSAGE | win32con.NIF_TIP  # type: ignore
            nid = (hwnd, 0, flags, win32con.WM_USER + 20, hicon, "VWAR")  # type: ignore
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)  # type: ignore
            # Show balloon
            NIIF_INFO = 0x00000001
            balloon = (hwnd, 0, win32con.NIF_INFO, win32con.WM_USER + 20, hicon, "VWAR", message, duration * 1000, title, NIIF_INFO)  # type: ignore
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, balloon)  # type: ignore
                log_message("[NOTIFY] Dispatched via tray balloon")
                # Schedule cleanup on a short timer in background thread
                import threading, time as _t
                def _cleanup():
                    _t.sleep(max(3, duration + 1))
                    try:
                        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)  # type: ignore
                        win32gui.DestroyWindow(hwnd)  # type: ignore
                    except Exception:
                        pass
                threading.Thread(target=_cleanup, daemon=True).start()
                return True
            except Exception as e:
                # Cleanup on failure
                try:
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)  # type: ignore
                    win32gui.DestroyWindow(hwnd)  # type: ignore
                except Exception:
                    pass
                log_message(f"[NOTIFY][tray] failed: {e}")
    except Exception as e:
        log_message(f"[NOTIFY][tray-init] failed: {e}")

        log_message("[NOTIFY] All backends failed; falling back to log only")
        return False

# ---------------- In-App Notification Manager (Toast) ----------------
# Unique VWAR-styled in-app notifications usable from any page

try:
    import tkinter as _tk
except Exception:  # pragma: no cover
    _tk = None  # type: ignore

_APP_NOTIFY = None  # type: ignore


class _ToastWindow:
    def __init__(self, root, title: str, message: str, *,
                 severity: str = "info", duration_ms: int = 3500,
                 width: int = 320):
        self.root = root
        self.duration_ms = max(1500, int(duration_ms))
        self.severity = severity
        self.win = _tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        # Vista+ drop shadow hint (best effort)
        try:
            self.win.wm_attributes("-alpha", 0.0)
        except Exception:
            pass

        # Styling
        colors = {
            "info": ("#009AA5", "white"),
            "success": ("#1B9E77", "white"),
            "warning": ("#E69F00", "black"),
            "critical": ("#D62839", "white"),
        }
        bg, fg = colors.get(severity, ("#009AA5", "white"))

        frame = _tk.Frame(self.win, bg=bg, bd=0, highlightthickness=0)
        frame.pack(fill="both", expand=True)
        # Title
        _tk.Label(frame, text=title, bg=bg, fg=fg, font=("Arial", 11, "bold"))\
            .pack(anchor="w", padx=12, pady=(10, 0))
        # Message
        _tk.Label(frame, text=message, bg=bg, fg=fg, font=("Arial", 10),
                 justify="left", wraplength=width - 24)\
            .pack(anchor="w", padx=12, pady=(4, 12))

        # Size and position will be set by manager
        self.win.update_idletasks()
        self.win.geometry(f"{width}x{self.win.winfo_reqheight()}+0+0")

        # Fade-in animation
        try:
            self._fade(0.0, 1.0, step=0.15)
        except Exception:
            pass

        # Auto-dismiss
        self._dismiss_after = self.win.after(self.duration_ms, self.destroy)

    def _fade(self, start: float, end: float, step: float = 0.1):
        try:
            a = start
            while a < end:
                self.win.wm_attributes("-alpha", a)
                self.win.update_idletasks()
                self.win.after(16)
                a += step
            self.win.wm_attributes("-alpha", end)
        except Exception:
            pass

    def place(self, x: int, y: int):
        try:
            self.win.geometry(f"+{int(x)}+{int(y)}")
        except Exception:
            pass

    def destroy(self):
        try:
            if self._dismiss_after:
                self.win.after_cancel(self._dismiss_after)
        except Exception:
            pass
        try:
            # Fade-out
            try:
                self._fade(1.0, 0.0, step=0.2)
            except Exception:
                pass
            self.win.destroy()
        except Exception:
            pass


class NotificationManager:
    """Global in-app toast manager.

    Usage:
      init_app_notifier(root)
      notify_app(title, message, severity="info")
    """

    def __init__(self, root, *, corner: str = "bottom-right", max_toasts: int = 4):
        if _tk is None:
            raise RuntimeError("Tkinter is not available for in-app notifications")
        self.root = root
        self.corner = corner
        self.max_toasts = max(1, max_toasts)
        self._toasts: list[_ToastWindow] = []

    def show(self, title: str, message: str, *, severity: str = "info",
             duration_ms: int = 3500):
        # Ensure runs on UI thread
        try:
            if _tk is None:
                return
            if not self._in_ui_thread():
                self.root.after(0, lambda: self.show(title, message, severity=severity, duration_ms=duration_ms))
                return
            # Enforce max stack
            while len(self._toasts) >= self.max_toasts:
                tw = self._toasts.pop(0)
                try:
                    tw.destroy()
                except Exception:
                    pass
            toast = _ToastWindow(self.root, title, message, severity=severity, duration_ms=duration_ms)
            self._toasts.append(toast)
            self._reflow()
            # Edge pulse for critical
            if severity == "critical":
                try:
                    self.edge_pulse(severity="critical")
                except Exception:
                    pass
        except Exception as e:
            log_message(f"[NOTIFY][in-app] show failed: {e}")

    def _reflow(self):
        try:
            # Calculate stacking from chosen corner with 12px gaps
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            gap = 12
            margin = 18
            y = sh - margin
            for tw in reversed(self._toasts):
                tw.win.update_idletasks()
                w = tw.win.winfo_width()
                h = tw.win.winfo_height()
                x = sw - margin - w
                y = y - h
                tw.place(x, y)
                y = y - gap

            # Clean up dead toasts
            alive = []
            for tw in self._toasts:
                try:
                    if tw.win.winfo_exists():
                        alive.append(tw)
                except Exception:
                    pass
            self._toasts = alive
        except Exception as e:
            log_message(f"[NOTIFY][in-app] reflow failed: {e}")

    def _in_ui_thread(self) -> bool:
        try:
            # If we can call winfo_exists without exception, assume UI thread
            _ = self.root.winfo_exists()
            return True
        except Exception:
            return False

    def edge_pulse(self, *, severity: str = "info", duration_ms: int = 1200, thickness: int = 6):
        """Show a brief glow around the app window edges (Windows-friendly).

        Uses a mask-based transparent Toplevel to draw only the border so
        clicks mostly pass through the center. Best-effort; gracefully no-op
        if attributes unsupported.
        """
        try:
            mask = "#00FF01"  # unlikely color, used as transparent key
            colors = {
                "info": "#009AA5",
                "success": "#1B9E77",
                "warning": "#E69F00",
                "critical": "#D62839",
            }
            col = colors.get(severity, "#009AA5")
            # Compute geometry around root
            self.root.update_idletasks()
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            pad = 8
            tw = _tk.Toplevel(self.root)
            tw.overrideredirect(True)
            tw.attributes("-topmost", True)
            try:
                tw.wm_attributes("-transparentcolor", mask)
            except Exception:
                # If transparent color unsupported, fallback to alpha only
                pass
            geo = f"{rw + pad*2}x{rh + pad*2}+{rx - pad}+{ry - pad}"
            tw.geometry(geo)
            cv = _tk.Canvas(tw, highlightthickness=0, bd=0, background=mask)
            cv.pack(fill="both", expand=True)
            W = rw + pad*2
            H = rh + pad*2
            t = thickness
            # Draw 4 border rectangles
            cv.create_rectangle(0, 0, W, t, fill=col, width=0)
            cv.create_rectangle(0, H - t, W, H, fill=col, width=0)
            cv.create_rectangle(0, 0, t, H, fill=col, width=0)
            cv.create_rectangle(W - t, 0, W, H, fill=col, width=0)
            # Fade in/out via alpha, if available
            try:
                tw.wm_attributes("-alpha", 0.0)
                a = 0.0
                while a < 0.85:
                    tw.wm_attributes("-alpha", a)
                    tw.update_idletasks()
                    tw.after(16)
                    a += 0.2
                tw.wm_attributes("-alpha", 0.85)
            except Exception:
                pass
            # Auto-destroy after duration_ms with quick fade
            def _end():
                try:
                    try:
                        a = 0.85
                        while a > 0.0:
                            tw.wm_attributes("-alpha", a)
                            tw.update_idletasks()
                            tw.after(16)
                            a -= 0.22
                    except Exception:
                        pass
                    tw.destroy()
                except Exception:
                    pass
            tw.after(max(600, duration_ms), _end)
        except Exception as e:
            log_message(f"[NOTIFY][edge-pulse] failed: {e}")


def init_app_notifier(root) -> NotificationManager:
    """Initialize the global in-app notifier with the given Tk root."""
    global _APP_NOTIFY
    try:
        if _APP_NOTIFY is None:
            _APP_NOTIFY = NotificationManager(root)
        return _APP_NOTIFY
    except Exception as e:
        log_message(f"[NOTIFY] Failed to init app notifier: {e}")
        raise


def notify_app(title: str, message: str, *, severity: str = "info", duration_ms: int = 3500) -> bool:
    """Show an in-app toast if initialized, otherwise fall back to system notify.

    Thread-safe: can be called from worker threads.
    Returns True if dispatched to either in-app or system notification.
    """
    global _APP_NOTIFY
    try:
        if _APP_NOTIFY is not None:
            _APP_NOTIFY.show(title, message, severity=severity, duration_ms=duration_ms)
            return True
    except Exception as e:
        log_message(f"[NOTIFY] notify_app error: {e}")
    # Fallback to system notification
    try:
        return notify(title, message, duration=max(1, duration_ms // 1000))
    except Exception:
        return False
