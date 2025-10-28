"""
Comprehensive test script for exclusion system.
Run this from the project root: python run_exclusion_tests.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.exclusions import is_excluded_path, get_base_dir, get_internal_exclude_roots

def test_exclusions():
    """Run comprehensive exclusion tests."""
    base_dir = get_base_dir()
    tests_passed = 0
    tests_failed = 0
    
    print("=" * 70)
    print("VWAR Scanner - Comprehensive Exclusion Tests")
    print("=" * 70)
    print(f"\nProject Base Directory: {base_dir}\n")
    
    # Define test cases: (path, should_be_excluded, expected_reason)
    test_cases = [
        # Project folders
        (base_dir, True, 'INTERNAL', "Project root"),
        (os.path.join(base_dir, 'dist'), True, 'INTERNAL', "dist/ folder"),
        (os.path.join(base_dir, 'build'), True, 'INTERNAL', "build/ folder"),
        (os.path.join(base_dir, '__pycache__'), True, 'INTERNAL', "__pycache__/ folder"),
        (os.path.join(base_dir, '.git'), True, 'INTERNAL', ".git/ folder"),
        (os.path.join(base_dir, '.venv'), True, 'INTERNAL', ".venv/ folder"),
        (os.path.join(base_dir, 'VWAR_i'), True, 'INTERNAL', "VWAR_i/ installer folder"),
        (os.path.join(base_dir, 'assets', 'yara'), True, 'INTERNAL', "assets/yara/ folder"),
        (os.path.join(base_dir, 'quarantine'), True, 'INTERNAL', "quarantine/ folder"),
        (os.path.join(base_dir, 'scanvault'), True, 'INTERNAL', "scanvault/ folder"),
        (os.path.join(base_dir, 'data'), True, 'INTERNAL', "data/ folder"),
        
        # Nested files in excluded folders
        (os.path.join(base_dir, 'dist', 'VWAR.exe'), True, 'INTERNAL', "File in dist/"),
        (os.path.join(base_dir, 'build', 'VWAR', 'test.pyz'), True, 'INTERNAL', "File in build/"),
        (os.path.join(base_dir, 'VWAR_i', 'setup.exe'), True, 'INTERNAL', "File in VWAR_i/"),
        
        # Recycle Bin paths
        (r"C:\$Recycle.Bin\S-1-5-21\file.txt", True, 'RECYCLE_BIN', "Recycle Bin file"),
        (r"D:\$RECYCLE.BIN\test.doc", True, 'RECYCLE_BIN', "Recycle Bin (uppercase)"),
        
        # System folders
        (r"C:\Windows\Temp\file.tmp", True, 'TEMP_ROOT', "Windows Temp folder"),
        (r"C:\System Volume Information\data", True, 'TEMP_ROOT', "System Volume Info"),
        
        # Normal user files (should NOT be excluded)
        (r"C:\Users\TestUser\Documents\report.pdf", False, 'NONE', "Normal user file"),
        (r"D:\Projects\MyProject\code.py", False, 'NONE', "Normal project file"),
    ]
    
    print("Running Tests...")
    print("-" * 70)
    
    for path, should_exclude, expected_reason, description in test_cases:
        excluded, reason = is_excluded_path(path)
        
        # Check if test passed
        if excluded == should_exclude and reason == expected_reason:
            status = "✓ PASS"
            tests_passed += 1
            color = "\033[92m"  # Green
        else:
            status = "✗ FAIL"
            tests_failed += 1
            color = "\033[91m"  # Red
        
        reset = "\033[0m"
        
        print(f"{color}{status}{reset} | {description}")
        print(f"       Path: {path}")
        print(f"       Expected: excluded={should_exclude}, reason={expected_reason}")
        print(f"       Got:      excluded={excluded}, reason={reason}")
        print()
    
    # List all internal exclusion roots
    print("-" * 70)
    print("\nAll Internal Exclusion Roots:")
    roots = get_internal_exclude_roots()
    for i, root in enumerate(sorted(roots), 1):
        print(f"  {i:2d}. {root}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print(f"  Total Tests: {tests_passed + tests_failed}")
    print(f"  ✓ Passed: {tests_passed}")
    print(f"  ✗ Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! Exclusion system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please review the exclusion configuration.")
        return 1
    print("=" * 70)

if __name__ == '__main__':
    exit_code = test_exclusions()
    sys.exit(exit_code)
