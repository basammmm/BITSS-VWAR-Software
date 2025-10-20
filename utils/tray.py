"""System tray integration for VWAR.

Provides a minimal wrapper to show a Windows notification area (system tray)
icon with a context menu allowing the user to restore the full GUI or exit.

Relies on pywin32. If unavailable or any call fails, functions degrade
gracefully and return False.
"""
from __future__ import annotations

import os
import sys
import threading
from typing import Callable, Optional

try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    import win32gui_struct  # type: ignore
except Exception:  # pragma: no cover
    win32api = win32con = win32gui = win32gui_struct = None  # type: ignore

try:
    from utils.logger import log_message
except Exception:  # pragma: no cover
    def log_message(msg: str):  # type: ignore
        print(msg)


class TrayIcon:
    def __init__(self, tooltip: str, icon_path: Optional[str], on_restore: Callable[[], None], on_exit: Callable[[], None], on_scan_now: Optional[Callable[[], None]] = None):
        self.tooltip = tooltip
        self.icon_path = icon_path
        self.on_restore = on_restore
        self.on_exit = on_exit
        self.on_scan_now = on_scan_now
        self.hwnd = None
        self.hicon = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> bool:
        if win32gui is None:
            log_message("[TRAY] pywin32 not available; tray disabled")
            return False
        if self._running:
            return True
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if win32gui and self.hwnd:
            try:
                win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)  # type: ignore
            except Exception:
                pass

    # Windows message loop implementation
    def _message_loop(self):  # pragma: no cover - GUI thread
        message_map = {
            win32con.WM_COMMAND: self._on_command,  # type: ignore
            win32con.WM_DESTROY: self._on_destroy,  # type: ignore
            win32con.WM_USER + 20: self._on_notify,  # type: ignore
        }
        wc = win32gui.WNDCLASS()  # type: ignore
        hinst = wc.hInstance = win32api.GetModuleHandle(None)  # type: ignore
        wc.lpszClassName = "VWARTrayClass"
        wc.lpfnWndProc = message_map  # type: ignore
        try:
            class_atom = win32gui.RegisterClass(wc)  # type: ignore
        except Exception:
            return
        self.hwnd = win32gui.CreateWindowEx(0, class_atom, "VWARTray", 0, 0, 0, 0, 0, 0, 0, hinst, None)  # type: ignore
        # Load icon
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                self.hicon = win32gui.LoadImage(hinst, self.icon_path, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE)  # type: ignore
            except Exception:
                self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)  # type: ignore
        else:
            self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)  # type: ignore
        flags = win32con.NIF_ICON | win32con.NIF_MESSAGE | win32con.NIF_TIP  # type: ignore
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.hicon, self.tooltip)  # type: ignore
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)  # type: ignore
        except Exception:
            return
        # Standard message loop
        while self._running:
            win32gui.PumpWaitingMessages()  # type: ignore
            win32gui.Sleep(100)  # type: ignore
        # Cleanup
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)  # type: ignore
        except Exception:
            pass

    def _on_notify(self, hwnd, msg, wparam, lparam):  # pragma: no cover - user interaction
        if lparam == win32con.WM_LBUTTONUP:  # type: ignore
            self.on_restore()
        elif lparam == win32con.WM_RBUTTONUP:  # context menu
            self._show_menu()
        return True

    def _show_menu(self):  # pragma: no cover
        menu = win32gui.CreatePopupMenu()  # type: ignore
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1, "Open VWAR")  # type: ignore
        win32gui.AppendMenu(menu, win32con.MF_STRING, 3, "Scan Now")  # type: ignore
        win32gui.AppendMenu(menu, win32con.MF_STRING, 2, "Exit")  # type: ignore
        pos = win32gui.GetCursorPos()  # type: ignore
        win32gui.SetForegroundWindow(self.hwnd)  # type: ignore
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)  # type: ignore

    def _on_command(self, hwnd, msg, wparam, lparam):  # pragma: no cover
        cmd_id = win32api.LOWORD(wparam)  # type: ignore
        if cmd_id == 1:
            self.on_restore()
        elif cmd_id == 2:
            self.on_exit()
        elif cmd_id == 3 and self.on_scan_now:
            self.on_scan_now()

    def _on_destroy(self, hwnd, msg, wparam, lparam):  # pragma: no cover
        self.stop()


def create_tray(on_restore: Callable[[], None], on_exit: Callable[[], None], icon_path: Optional[str], tooltip: str = "VWAR Scanner", on_scan_now: Optional[Callable[[], None]] = None) -> Optional[TrayIcon]:
    tray = TrayIcon(tooltip, icon_path, on_restore, on_exit, on_scan_now=on_scan_now)
    if tray.start():
        return tray
    return None

__all__ = ["create_tray", "TrayIcon"]
