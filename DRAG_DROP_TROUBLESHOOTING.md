# Drag & Drop Troubleshooting Guide

## Issue: Drag & Drop Not Working

### Symptoms
- Files/folders don't respond when dragged to the green drop zone
- No visual feedback when hovering over drop area
- Drop zone appears but doesn't accept drops

### Root Causes & Solutions

#### 1. TkinterDnD Library Issue
**Symptom**: Drop zone shows warning message in log box
**Cause**: `tkinterdnd2` library not properly initialized
**Solutions**:

**Option A: Reinstall tkinterdnd2**
```cmd
pip uninstall tkinterdnd2
pip install tkinterdnd2==0.3.0
```

**Option B: Check DLL files**
- tkinterdnd2 requires special DLL files
- Location: `.venv/Lib/site-packages/tkinterdnd2/tkdnd/`
- Verify `tkdnd2.8.6-windows-x64.dll` exists

**Option C: Manual DLL installation**
```cmd
cd .venv/Lib/site-packages/tkinterdnd2
python -c "from tkinterdnd2 import _tkdnd_lib; print(_tkdnd_lib._tkdnd_lib_path)"
```

#### 2. Windows Security Blocking
**Symptom**: Drag works in other apps but not VWAR
**Cause**: Windows UAC/security blocking inter-process drag
**Solutions**:

- Run VWAR as Administrator (required anyway)
- Ensure File Explorer is NOT running as admin
- Cannot drag from admin app to non-admin app (or vice versa)

**Test**:
1. Close VWAR
2. Open File Explorer (normal mode)
3. Run VWAR with admin privileges
4. Try drag & drop again

#### 3. Python 3.11+ Compatibility
**Symptom**: Import errors or AttributeErrors
**Cause**: tkinterdnd2 may have issues with Python 3.11+
**Solution**:

Check Python version:
```cmd
python --version
```

If 3.12+, consider downgrading to 3.11:
```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. Virtual Environment Issues
**Symptom**: Works in one environment but not another
**Cause**: Package conflicts or incomplete installation
**Solution**:

Recreate virtual environment:
```cmd
deactivate
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Verification Steps

#### Test 1: Check Library Import
```python
python -c "from tkinterdnd2 import TkinterDnD, DND_FILES; print('OK')"
```
Expected: `OK`

#### Test 2: Check DLL Loading
```python
python -c "from tkinterdnd2 import TkinterDnD; import tkinter; root = TkinterDnD.Tk(); print('Window OK'); root.destroy()"
```
Expected: `Window OK`

#### Test 3: Simple Drop Test
Create `test_drag.py`:
```python
from tkinterdnd2 import TkinterDnD, DND_FILES
import tkinter as tk

root = TkinterDnD.Tk()
root.title("Drag Test")

label = tk.Label(root, text="Drop Files Here", bg="lightgreen", width=40, height=10)
label.pack(padx=20, pady=20)

def on_drop(event):
    print(f"Dropped: {event.data}")
    label.config(text=f"Dropped: {event.data}")

label.drop_target_register(DND_FILES)
label.dnd_bind('<<Drop>>', on_drop)

root.mainloop()
```

Run: `python test_drag.py`

### Alternative: Use File/Folder Buttons

If drag & drop still doesn't work:

1. Click **"Select Target File"** button
2. Or click **"Select Target Folder"** button
3. Navigate to file/folder in dialog
4. Click **"Scan"** button

These buttons provide the same functionality without drag & drop.

### Known Limitations

1. **Cannot drag between privilege levels**
   - Cannot drag from admin File Explorer to non-admin VWAR
   - Cannot drag from non-admin File Explorer to admin VWAR
   - Both must have same privilege level

2. **Network drives may not work**
   - UNC paths might not be supported
   - Map network drive to local letter first

3. **Special characters in paths**
   - Paths with non-ASCII characters may fail
   - Move files to path with ASCII-only names

4. **Large file counts**
   - Dragging 100+ files may timeout
   - Drop smaller batches or use folder drop

### Debug Mode

Enable detailed logging:

1. Go to Settings (Schedule Scan page)
2. Enable "Debug Logging" (should be forced ON)
3. Check console output when dragging
4. Look for error messages starting with `[ERROR]`

### Report Issues

If drag & drop still doesn't work after trying all solutions:

1. Run diagnostic: `python test_components.py`
2. Save output
3. Check `data/vwar.log` for errors
4. Include:
   - Python version
   - Windows version
   - Output of: `pip list | findstr tkinterdnd2`
   - Any error messages from console

### Quick Fix Summary

```cmd
# Most common fix - reinstall tkinterdnd2
pip uninstall tkinterdnd2 -y
pip install tkinterdnd2==0.3.0

# Restart VWAR with admin privileges
python main.py
# Click "Yes" on UAC prompt

# Test with simple file drag
# Should see green drop zone on Scan page
# Hover should show darker green
# Drop should auto-start scan
```

### Visual Indicators

When drag & drop is working:
- ✅ Green drop zone visible on Scan page
- ✅ Color darkens when hovering with files
- ✅ Drop shows "✓ Ready to scan: filename.ext"
- ✅ Scan starts automatically after drop
- ✅ No error messages in log box

When drag & drop is NOT working:
- ❌ Warning message in log box on Scan page load
- ❌ No color change when hovering
- ❌ Drop does nothing
- ❌ No feedback or response

In the latter case, use the "Select Target File/Folder" buttons as a reliable alternative.
