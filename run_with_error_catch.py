"""Wrapper to run main.py with error catching"""
import sys
import traceback

print("Starting VWAR Scanner with error catching...")
print("=" * 60)

try:
    # Import and run main
    import main
    print("Main module imported successfully")
    
    # Call main function
    main.main()
    
except SystemExit as e:
    print(f"\n[INFO] Program exited with code: {e.code}")
    if e.code == 0:
        print("✅ Clean exit")
    else:
        print(f"⚠️ Exit code: {e.code}")
        
except KeyboardInterrupt:
    print("\n[INFO] Interrupted by user (Ctrl+C)")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ CRASH DETECTED:")
    print("=" * 60)
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    print("\nFull Traceback:")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    
finally:
    print("\n" + "=" * 60)
    input("Press Enter to exit...")
