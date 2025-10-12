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
