"""
Quick test script to verify VWAR components are working
Run this to check if there are any import or initialization errors
"""

print("=" * 60)
print("VWAR SCANNER - COMPONENT TEST")
print("=" * 60)

# Test 1: Basic imports
print("\n[TEST 1] Testing basic imports...")
try:
    import os, sys, json, threading
    import tkinter as tk
    print("✓ Standard library imports OK")
except Exception as e:
    print(f"✗ Standard library import failed: {e}")
    sys.exit(1)

# Test 2: Third-party imports
print("\n[TEST 2] Testing third-party imports...")
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    print("✓ tkinterdnd2 OK")
except Exception as e:
    print(f"✗ tkinterdnd2 import failed: {e}")
    print("  Fix: pip install tkinterdnd2")

try:
    import yara
    print("✓ yara-python OK")
except Exception as e:
    print(f"✗ yara import failed: {e}")

try:
    import win32api, win32con, win32gui
    print("✓ pywin32 OK")
except Exception as e:
    print(f"✗ pywin32 import failed: {e}")

try:
    from plyer import notification
    print("✓ plyer OK")
except Exception as e:
    print(f"✗ plyer import failed: {e}")

# Test 3: Project modules
print("\n[TEST 3] Testing project modules...")
try:
    from config import ICON_PATH, QUARANTINE_FOLDER, SCANVAULT_FOLDER
    print(f"✓ config OK")
    print(f"  - Icon: {ICON_PATH}")
    print(f"  - Quarantine: {QUARANTINE_FOLDER}")
    print(f"  - ScanVault: {SCANVAULT_FOLDER}")
except Exception as e:
    print(f"✗ config import failed: {e}")
    sys.exit(1)

try:
    from utils.logger import log_message
    print("✓ utils.logger OK")
except Exception as e:
    print(f"✗ utils.logger import failed: {e}")

try:
    from utils.notify import notify
    print("✓ utils.notify OK")
except Exception as e:
    print(f"✗ utils.notify import failed: {e}")

try:
    from utils.tray import create_tray
    print("✓ utils.tray OK")
except Exception as e:
    print(f"✗ utils.tray import failed: {e}")

try:
    from utils.settings import SETTINGS
    print("✓ utils.settings OK")
except Exception as e:
    print(f"✗ utils.settings import failed: {e}")

# Test 4: Scanning modules
print("\n[TEST 4] Testing scanning modules...")
try:
    from Scanning.yara_engine import compile_yara_rules
    print("✓ Scanning.yara_engine OK")
except Exception as e:
    print(f"✗ Scanning.yara_engine import failed: {e}")

try:
    from Scanning.scanvault import vault_capture_file
    print("✓ Scanning.scanvault OK")
except Exception as e:
    print(f"✗ Scanning.scanvault import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from Scanning.scan_page import ScanPage
    print("✓ Scanning.scan_page OK")
except Exception as e:
    print(f"✗ Scanning.scan_page import failed: {e}")

# Test 5: Main GUI
print("\n[TEST 5] Testing main GUI import...")
try:
    from app_main import VWARScannerGUI
    print("✓ app_main.VWARScannerGUI OK")
except Exception as e:
    print(f"✗ app_main import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: TkinterDnD window creation
print("\n[TEST 6] Testing TkinterDnD window creation...")
try:
    root = TkinterDnD.Tk()
    root.withdraw()  # Don't show window
    print("✓ TkinterDnD.Tk() window created")
    root.destroy()
except Exception as e:
    print(f"✗ TkinterDnD window creation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Check YARA rules
print("\n[TEST 7] Checking YARA rules...")
try:
    yara_dir = "assets/yara"
    if os.path.exists(yara_dir):
        rule_count = sum(1 for root, dirs, files in os.walk(yara_dir) 
                        for f in files if f.endswith(('.yar', '.yara')))
        print(f"✓ Found {rule_count} YARA rule files")
    else:
        print(f"✗ YARA directory not found: {yara_dir}")
except Exception as e:
    print(f"✗ YARA rules check failed: {e}")

# Test 8: Check data directories
print("\n[TEST 8] Checking data directories...")
dirs_to_check = [
    ("data", "Data directory"),
    ("quarantine", "Quarantine directory"),
    ("scanvault", "ScanVault directory"),
    ("assets", "Assets directory"),
]
for dir_path, desc in dirs_to_check:
    if os.path.exists(dir_path):
        print(f"✓ {desc}: {dir_path}")
    else:
        print(f"⚠ {desc} not found: {dir_path} (will be created on first run)")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("\nIf all tests passed (✓), the application should work correctly.")
print("The 'relaunch' behavior when running main.py is NORMAL - it's")
print("requesting admin privileges via Windows UAC.")
print("\nTo run the GUI:")
print("  1. Run: python main.py")
print("  2. Click 'Yes' on the UAC prompt")
print("  3. Wait for the GUI window to appear")
print("\nOr bypass admin check for testing:")
print("  python main.py --help")
print("=" * 60)
