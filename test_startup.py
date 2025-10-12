"""Test script to diagnose startup crashes"""
import sys
import traceback

print("=" * 60)
print("VWAR Startup Diagnostic Test")
print("=" * 60)

try:
    print("\n[1/10] Testing Python version...")
    print(f"   ✓ Python {sys.version}")
    
    print("\n[2/10] Testing basic imports...")
    import os
    import tkinter as tk
    print("   ✓ os, tkinter")
    
    print("\n[3/10] Testing tkinterdnd2...")
    from tkinterdnd2 import TkinterDnD, DND_FILES
    print("   ✓ tkinterdnd2")
    
    print("\n[4/10] Testing config...")
    from config import ICON_PATH, ACTIVATION_FILE, QUARANTINE_FOLDER
    print(f"   ✓ ICON_PATH: {ICON_PATH}")
    print(f"   ✓ ACTIVATION_FILE: {ACTIVATION_FILE}")
    
    print("\n[5/10] Testing activation module...")
    from activation.license_utils import is_activated
    print("   ✓ activation.license_utils")
    
    print("\n[6/10] Testing activation GUI...")
    from activation.gui import show_activation_window
    print("   ✓ activation.gui")
    
    print("\n[7/10] Testing scan modules...")
    from Scanning.scan_page import ScanPage
    print("   ✓ Scanning.scan_page")
    
    print("\n[8/10] Testing monitoring modules...")
    from RMonitoring.monitor_page import MonitorPage
    print("   ✓ RMonitoring.monitor_page")
    
    print("\n[9/10] Testing app_main...")
    from app_main import VWARScannerGUI
    print("   ✓ app_main.VWARScannerGUI")
    
    print("\n[10/10] Testing TkinterDnD.Tk() window creation...")
    root = TkinterDnD.Tk()
    root.withdraw()  # Hide window
    print("   ✓ TkinterDnD.Tk() created successfully")
    root.destroy()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - No startup issues detected")
    print("=" * 60)
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ ERROR DETECTED:")
    print("=" * 60)
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    print("\nFull Traceback:")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    print("\n⚠️ This is the error causing the crash!")
    
input("\nPress Enter to exit...")
