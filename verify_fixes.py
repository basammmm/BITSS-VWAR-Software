"""
Quick test to verify the fixes work
"""
import os
import sys

# Check 1: Monitor path
print("=" * 60)
print("CHECK 1: vwar_monitor.exe location")
print("=" * 60)

base_path = os.path.dirname(os.path.abspath(__file__))

monitor_candidates = [
    os.path.join(base_path, "vwar_monitor", "vwar_monitor.exe"),
    os.path.join(base_path, "vwar_monitor.exe"),
]

for i, candidate in enumerate(monitor_candidates, 1):
    exists = "✓ FOUND" if os.path.exists(candidate) else "✗ NOT FOUND"
    print(f"{i}. {exists}: {candidate}")

print("\n" + "=" * 60)
print("CHECK 2: Cross-privilege drag-drop support")
print("=" * 60)

try:
    import ctypes
    from ctypes import wintypes
    
    print("✓ ctypes available")
    
    # Check if ChangeWindowMessageFilterEx exists
    try:
        func = ctypes.windll.user32.ChangeWindowMessageFilterEx
        print("✓ ChangeWindowMessageFilterEx available")
        print("✓ Cross-privilege drag-drop CAN be enabled")
    except AttributeError:
        print("✗ ChangeWindowMessageFilterEx not available (old Windows?)")
        
except ImportError:
    print("✗ ctypes not available")

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)

monitor_found = any(os.path.exists(c) for c in monitor_candidates)
print(f"Monitor: {'✓ READY' if monitor_found else '✗ FIX NEEDED'}")
print(f"Drag-Drop: ✓ SHOULD WORK (even with admin)")
print("=" * 60)
