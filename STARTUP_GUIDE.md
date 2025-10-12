# VWAR Scanner Startup Guide

## Normal Startup Behavior

When you run `python main.py`, you'll see these steps:

```
[INFO] Compiled 6 YARA rule files.
[INFO] Not running as admin. Relaunching...
```

This is **NORMAL** - the application requires administrator privileges to function properly.

### What Happens Next

1. **UAC Prompt Appears**: Windows will show a "User Account Control" dialog
2. **Click "Yes"**: Allow the application to make changes
3. **App Relaunches**: The application starts again with admin rights
4. **GUI Opens**: The main VWAR Scanner window appears

## Troubleshooting

### "Application Closes Immediately"
- **Cause**: You clicked "No" on the UAC prompt
- **Solution**: Run again and click "Yes"

### "Nothing Happens After UAC"
- **Possible causes**:
  - Activation check failed
  - Missing dependencies
  - Port conflict (if monitor is already running)

### Check for Existing Instance
```cmd
tasklist | findstr python
```
If VWAR is already running, kill it:
```cmd
taskkill /F /IM python.exe
```

## Running Without Admin (Development Only)

For testing without admin privileges, use:
```cmd
python main.py --help
```

Or modify `main.py` to skip the admin check (lines 200-203):
```python
# Comment out these lines:
# if not is_admin():
#     print("[INFO] Not running as admin. Relaunching...")
#     run_as_admin()
#     return
```

**Warning**: Some features won't work without admin (real-time monitoring, system folder scans).

## Command Line Options

```
python main.py              # Normal GUI mode (requires admin)
python main.py --tray       # Start minimized to system tray
python main.py --silent     # Background services only (no GUI)
python main.py --help       # Show help without admin check
```

## Recent Features Added

1. **Drag & Drop Scanning** - Drop files/folders on the scan page
2. **Minimize to Tray** - Close button minimizes instead of exits (configurable in settings)
3. **Progress Notifications** - Toast notifications for scan completion and threats
4. **User Exclusions** - Manage custom scan exclusions in settings

## Verification Steps

After the GUI opens, verify:

1. ✅ Main window appears (1200x722)
2. ✅ Sidebar shows: Home, Scan, Backup, Scan Vault, Help, Schedule Scan
3. ✅ No error messages in terminal
4. ✅ System tray icon appears (if minimize-to-tray enabled)

## Error Logs

Check logs in:
- `data/vwar.log` - Application logs
- Terminal output - Real-time errors

## Support

If issues persist:
1. Check `data/vwar.log` for errors
2. Verify all dependencies: `pip list`
3. Ensure Python 3.11+ is installed
4. Run with debug mode in settings

## Dependencies

Required packages (from requirements.txt):
- tkinterdnd2==0.3.0 (NEW - for drag & drop)
- yara-python==4.5.4
- pywin32==310
- plyer==2.1.0
- win10toast==0.9
- And 20+ others...

Install all:
```cmd
pip install -r requirements.txt
```
