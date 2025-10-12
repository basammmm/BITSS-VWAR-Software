# Drag & Drop Not Working? Here's Why & How to Fix

## The Problem

Windows **blocks drag-and-drop between processes with different privilege levels** for security reasons.

### What's happening:
- Your VWAR app runs as **Administrator** (elevated)
- Windows File Explorer runs as **Normal User** (not elevated)
- Windows sees this as a security risk and **silently blocks** the drop operation

## Solutions

### ✅ Solution 1: Run Without Admin (RECOMMENDED for testing drag-drop)

```powershell
# From your project folder:
python main.py --no-admin
```

**Pros:**
- Drag & drop will work perfectly
- Good for testing drag-drop functionality

**Cons:**
- Real-time monitoring won't work (needs admin)
- Some scans may have limited access

---

### ✅ Solution 2: Run File Explorer as Admin (RECOMMENDED for production use)

1. Press `Win + X`, choose **Windows Terminal (Admin)** or **PowerShell (Admin)**
2. Type:
   ```powershell
   Start-Process explorer
   ```
3. A new **elevated** File Explorer window opens
4. Drag files from this admin File Explorer to VWAR

**Pros:**
- Full app functionality (monitoring + drag-drop)
- Best of both worlds

**Cons:**
- Must remember to use admin File Explorer
- Regular File Explorer won't work

---

### ✅ Solution 3: Use the Test Script

Test if drag-drop is working at all:

```powershell
# Run the test (WITHOUT admin)
python test_drag_drop.py
```

**What it does:**
- Opens a simple test window
- Shows if tkinterdnd2 is working
- Drag a file from regular File Explorer
- Should turn **lime green** and show the file path

**If the test works:**
- tkinterdnd2 is fine
- Main app has privilege mismatch issue

**If the test fails:**
- tkinterdnd2 may not be installed correctly
- Try: `pip install --upgrade --force-reinstall tkinterdnd2`

---

## Why Can't We Just Fix This in Code?

**Unfortunately, no.** This is a Windows security feature, not a bug. Microsoft intentionally blocks drag-drop between different privilege levels to prevent:

- Malicious programs tricking elevated apps
- Privilege escalation attacks
- Accidental security bypasses

**Every Windows app** (Chrome, VS Code, etc.) has this same limitation.

---

## Alternative: Use the Buttons

If drag-drop is too much hassle, use the built-in buttons:

1. **Select Target File** - Pick a single file
2. **Select Target Folder** - Pick a folder to scan recursively
3. **Scan** - Start the scan

These buttons work **regardless of privilege level**.

---

## Technical Details (for developers)

### Detection Logic

The app now logs drag-drop initialization:

```
[INFO] ✓ Drag & Drop enabled successfully!
```

If you see this, tkinterdnd2 is registered. If drop still doesn't work, it's privilege mismatch.

### Windows UAC Levels

- **High Integrity**: Admin processes
- **Medium Integrity**: Normal user processes
- **Low Integrity**: Sandboxed processes (browsers)

Windows only allows drag-drop **within the same integrity level**.

### Why Admin is Required

VWAR needs admin for:

1. **Real-time monitoring** (file system driver hooks)
2. **System-wide protection** (scanning all user folders)
3. **Service management** (starting/stopping vwar_monitor.exe)

Without admin, these features won't work.

---

## Quick Reference

| Scenario | Drag-Drop Works? | Monitoring Works? | Recommended? |
|----------|------------------|-------------------|--------------|
| App as Admin + Normal Explorer | ❌ No | ✅ Yes | ❌ No |
| App as Admin + Admin Explorer | ✅ Yes | ✅ Yes | ✅ **BEST** |
| App without Admin | ✅ Yes | ❌ No | ⚠️ Testing only |

---

## Still Having Issues?

1. Check console output for error messages
2. Run `test_drag_drop.py` to isolate the problem
3. Try different files (not system files)
4. Check Windows Event Viewer for UAC blocks
5. Temporarily disable antivirus (might block tkinterdnd2 DLL)

---

**Bottom Line:** Use an **admin File Explorer** or run VWAR **without admin** for drag-drop to work.
