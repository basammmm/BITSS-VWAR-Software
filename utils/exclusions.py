import os
import sys
import tempfile
import string
from functools import lru_cache
import re

# Centralized path exclusion helpers for scanning/monitoring

# Import user exclusions (lazy load to avoid circular imports)
def _get_user_exclusions():
    try:
        from utils.user_exclusions import get_user_exclusions
        return get_user_exclusions()
    except Exception:
        return None

@lru_cache(maxsize=1)
def get_base_dir() -> str:
    # utils/ -> project root assumed one level up
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@lru_cache(maxsize=1)
def get_internal_exclude_roots() -> set[str]:
    base = get_base_dir()
    # When packaged by PyInstaller, also exclude the folder containing the EXE
    exe_dir = None
    try:
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.abspath(os.path.dirname(sys.executable))
    except Exception:
        exe_dir = None
    roots = {
        base,
        os.path.join(base, 'assets', 'yara'),
        os.path.join(base, 'quarantine'),
        os.path.join(base, 'build'),
        os.path.join(base, '__pycache__'),
        os.path.join(base, 'data', 'scan_queue'),
        os.path.join(base, '.venv'),
        os.path.join(base, 'dist'),
        os.path.join(base, 'build'),
        os.path.join(base, '.git'),
        os.path.join(base, '.mypy_cache'),
        os.path.join(base, '.pytest_cache'),
    }
    if exe_dir:
        roots.update({
            exe_dir,
            os.path.join(exe_dir, 'assets'),
            os.path.join(exe_dir, 'assets', 'yara'),
            os.path.join(exe_dir, 'vwar_monitor'),
            os.path.join(exe_dir, 'quarantine'),
            os.path.join(exe_dir, 'scanvault'),
            os.path.join(exe_dir, 'data'),
        })
    # Installer/system folders (installer-aware policy)
    # These should be copy-scanned, not quarantined
    system_folders = [
        os.environ.get('ProgramFiles', 'C:\Program Files'),
        os.environ.get('ProgramFiles(x86)', 'C:\Program Files (x86)'),
        os.environ.get('ProgramData', 'C:\ProgramData'),
        os.environ.get('SystemRoot', 'C:\Windows'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Installer'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'WinSxS'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Temp'),
    ]
    for folder in system_folders:
        if folder:
            roots.add(os.path.abspath(folder))
    # MSI cache locations (common installer temp)
    msi_cache = [
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Installer'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'WinSxS'),
    ]
    for folder in msi_cache:
        roots.add(os.path.abspath(folder))
    return {os.path.abspath(p) for p in roots}

@lru_cache(maxsize=1)
def get_temp_roots() -> set[str]:
    roots: set[str] = set()
    # OS temp
    try:
        roots.add(os.path.abspath(tempfile.gettempdir()))
    except Exception:
        pass
    # Windows temp dirs
    for env in ("TEMP", "TMP"):  # user-level
        val = os.environ.get(env)
        if val:
            roots.add(os.path.abspath(val))
    # System temp
    sys_temp = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')
    roots.add(os.path.abspath(sys_temp))
    # Recycle Bin on each drive (Windows)
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            # Add canonical recycle bin + system volume information
            roots.add(os.path.abspath(os.path.join(drive, '$Recycle.Bin')))
            roots.add(os.path.abspath(os.path.join(drive, 'System Volume Information')))
    return roots

_TEMP_EXTS = (
    '.tmp', '.temp', '.part', '.partial', '.crdownload', '.download',
    '.swp', '.swo', '.bak', '.old', '.log', '.lock', '.cache', '.dmp',
    '.tmp~', '.~tmp'
)
_TEMP_FILES = (
    'thumbs.db', '.ds_store',
)
_TEMP_PREFIXES = (
    '~$', '._',
)


def is_temp_like_file(path: str) -> bool:
    name = os.path.basename(path).lower()
    if name.startswith(_TEMP_PREFIXES):
        return True
    if name in _TEMP_FILES:
        return True
    root, ext = os.path.splitext(name)
    if ext in _TEMP_EXTS:
        return True
    # zero-byte files often transient; treat cautiously
    try:
        if os.path.exists(path) and os.path.getsize(path) == 0:
            return True
    except Exception:
        return True
    return False


def is_under_any(path: str, roots: set[str]) -> bool:
    """Case-insensitive containment check for Windows paths (still works on *nix)."""
    try:
        p = os.path.abspath(path)
        pl = p.lower()
        for r in roots:
            rr = os.path.abspath(r)
            rrl = rr.lower()
            if pl == rrl or pl.startswith(rrl + os.sep.lower()):
                return True
    except Exception:
        return False
    return False


_RECYCLE_BIN_PATTERN = re.compile(r"^[A-Z]:\\\\?\\?\$recycle\.bin", re.IGNORECASE)

def is_excluded_path(path: str) -> tuple[bool, str]:
    """
    Returns (excluded, reason) where reason is one of:
      INTERNAL, TEMP_ROOT, TEMP_FILE, RECYCLE_BIN, USER_EXCLUDED, INSTALLER_PROTECTED, NONE
    Explicit recycle bin detection added to prevent vaulting deleted files.
    """
    # Normalize early
    norm = os.path.abspath(path)
    
    # Check user-defined exclusions first (highest priority)
    user_excl = _get_user_exclusions()
    if user_excl and user_excl.is_excluded(norm):
        return True, 'USER_EXCLUDED'
    
    if is_under_any(norm, get_internal_exclude_roots()):
        return True, 'INTERNAL'
    # Explicit recycle bin pattern check first (fast lower-case compare)
    low = norm.lower()
    if low.endswith('.lnk'):
        # Shortcuts themselves not necessarily transient; continue normally
        pass
    if '$recycle.bin' in low:
        # Ensure we catch any nested items inside Recycle Bin (sometimes localized or with GUIDs)
        # Path segments check
        parts = low.split(os.sep)
        for seg in parts:
            if seg == '$recycle.bin':
                return True, 'RECYCLE_BIN'
    # Temp roots (includes canonical recycle bins added earlier)
    if is_under_any(norm, get_temp_roots()):
        return True, 'TEMP_ROOT'
    if is_temp_like_file(norm):
        return True, 'TEMP_FILE'
    # Installer-aware exclusions
    installer_roots = [
        os.environ.get('ProgramFiles', 'C:\Program Files'),
        os.environ.get('ProgramFiles(x86)', 'C:\Program Files (x86)'),
        os.environ.get('ProgramData', 'C:\ProgramData'),
        os.environ.get('SystemRoot', 'C:\Windows'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Installer'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'WinSxS'),
    ]
    for folder in installer_roots:
        if is_under_any(norm, {os.path.abspath(folder)}):
            return True, 'INSTALLER_PROTECTED'
    return False, 'NONE'
