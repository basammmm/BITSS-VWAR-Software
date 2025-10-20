import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from utils.path_utils import resource_path

class HelpPage(tk.Frame):
    """A simple, styled Help page with inline guide and buttons to open the PDF guide only.

    - Searches for PDF guide files in both project root and assets folder
    - Uses resource_path so it works in PyInstaller EXE
    - Disables buttons when files are not found
    """
    COMMON_FILENAMES = [
    "Guide.pdf", "UserGuide.pdf", "VWAR_Guide.pdf", "VWAR_User_Guide.pdf",
    ]

    def __init__(self, parent, app):
        super().__init__(parent, bg="#f6f8fa")
        self.app = app

        # Header
        header = tk.Label(self, text="Help & Usage Guide", font=("Segoe UI", 18, "bold"), bg=self["bg"], fg="#111")
        header.pack(pady=(16, 6))
        sub = tk.Label(self, text="Learn how VWAR works and how to use it effectively.", font=("Segoe UI", 10), bg=self["bg"], fg="#444")
        sub.pack()

        # Content area
        body = tk.Frame(self, bg=self["bg"]) 
        body.pack(fill="both", expand=True, padx=18, pady=12)

        # Inline overview (kept lightweight and scannable)
        overview = (
            "Overview:\n\n"
            "- Real-time protection: Watches your Downloads and Desktop for new/changed files.\n"
            "- ScanVault: Temporarily captures files safely, scans them, then restores or quarantines.\n"
            "- Quarantine: Detected threats are isolated; you can review and delete.\n"
            "- Scheduled Scan: Configure periodic scans for selected folders.\n"
            "- Backup: Manual and automatic backups of important files.\n\n"
            "Tips:\n"
            "- Keep VWAR running to catch downloads instantly.\n"
            "- If you restore from quarantine, VWAR re-checks the file to ensure it's safe.\n"
            "- Use Settings to enable tray notifications and configure startup.\n"
        )
        txt = tk.Text(body, height=14, wrap="word", bg="white", fg="#222")
        txt.insert("1.0", overview)
        txt.config(state="disabled")
        txt.pack(fill="x", padx=2, pady=(0,10))

        # Button to open PDF guide (auto-detected)
        files = self._find_guides()
        btns = tk.Frame(body, bg=self["bg"]) 
        btns.pack(anchor="w")

        pdf_path = files.get("pdf")
        pdf_name = files.get("pdf_name") or "PDF"

        self._make_open_button(btns, f"Open PDF Guide ({pdf_name})", pdf_path).pack(side="left", padx=(0,8))
        if pdf_path:
            ttk.Button(btns, text="Show PDF in Folder", command=lambda p=pdf_path: self._open_folder(os.path.dirname(p))).pack(side="left")

        # Optional: quick access to containing folder if any found
        # (Moved 'Show PDF in Folder' button into the same row as 'Open PDF Guide')

        # Status
        status_lines = []
        if pdf_path:
            ts = files.get("pdf_mtime")
            status_lines.append(f"PDF: {os.path.basename(pdf_path)} (updated {ts})")
        else:
            status_lines.append("PDF: not found")
        tk.Label(body, text=" | ".join(status_lines), bg=self["bg"], fg="#666").pack(anchor="w", pady=(6,0))

    def _make_open_button(self, parent, label, path):
        btn = ttk.Button(parent, text=label, command=(lambda: self._open_file(path)))
        if not path:
            btn.state(["disabled"])  # disable if missing
        return btn

    def _open_file(self, path):
        try:
            os.startfile(path)  # Windows: opens with default app
        except Exception:
            pass

    def _open_folder(self, folder):
        try:
            os.startfile(folder)
        except Exception:
            pass

    def _find_guides(self):
        """Find guide files robustly.

        Priority:
        1) Known common filenames in assets/ then root
        2) Otherwise, newest *.pdf found in assets/ then root
        """
        def exists(p: str) -> bool:
            try:
                return os.path.exists(p)
            except Exception:
                return False

        def fmt_mtime(p: str) -> str:
            try:
                return datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")
            except Exception:
                return "unknown"

        # 1) Try known filenames
        known_candidates = []
        for name in self.COMMON_FILENAMES:
            known_candidates.append(resource_path(os.path.join("assets", name)))
            known_candidates.append(resource_path(name))

        pdf_path = next((p for p in known_candidates if p.lower().endswith('.pdf') and exists(p)), None)
        docx_path = None

        # 2) Fallback to newest match by extension
        def newest_with_ext(exts):
            found = []
            for base in (resource_path("assets"), resource_path(".")):
                try:
                    for fname in os.listdir(base):
                        if any(fname.lower().endswith(e) for e in exts):
                            full = os.path.join(base, fname)
                            if exists(full):
                                try:
                                    found.append((os.path.getmtime(full), full))
                                except Exception:
                                    found.append((0, full))
                except Exception:
                    continue
            if not found:
                return None
            found.sort(reverse=True)
            return found[0][1]

        if not pdf_path:
            pdf_path = newest_with_ext(['.pdf'])

        return {
            "pdf": pdf_path,
            "pdf_name": (os.path.basename(pdf_path) if pdf_path else None),
            "pdf_mtime": (fmt_mtime(pdf_path) if pdf_path else None),
        }
