# VWAR Scanner - Build Instructions & PyInstaller Configuration

## Quick Build

**PowerShell (Recommended):**
```powershell
.\build_vwar.ps1
```

**Manual Command:**
```powershell
pyinstaller --noconfirm --onefile --windowed `
  --icon=assets/VWAR.ico `
  --manifest=vwar.manifest `
  --name VWAR `
  --add-data "assets/VWAR.ico;assets" `
  --add-data "assets/yara;assets/yara" `
  --add-data "vwar_monitor;vwar_monitor" `
  --hidden-import=plyer.platforms.win.notification `
  --hidden-import=win10toast `
  --hidden-import=pywin32 `
  --hidden-import=win32api `
  --hidden-import=win32con `
  --hidden-import=win32gui `
  --hidden-import=win32gui_struct `
  --hidden-import=win32file `
  --hidden-import=pywintypes `
  --hidden-import=pystray `
  --hidden-import=PIL `
  --hidden-import=PIL.Image `
  --hidden-import=PIL.ImageDraw `
  --hidden-import=cryptography `
  --hidden-import=cryptography.fernet `
  --hidden-import=yara `
  --hidden-import=requests `
  --hidden-import=psutil `
  --hidden-import=threading `
  --hidden-import=concurrent.futures `
  --hidden-import=queue `
  --collect-all plyer `
  --collect-all win10toast `
  main.py

# Create runtime directories
$dist = (Resolve-Path .\dist).Path
New-Item -ItemType Directory -Force -Path (Join-Path $dist 'quarantine') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dist 'scanvault') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dist 'data') | Out-Null
```

---

## Changes from Previous Build Command

### ✅ What's New (Added for New Features)

#### 1. Notification System Support
```powershell
--hidden-import=plyer.platforms.win.notification  # Primary notification backend
--hidden-import=win10toast                        # Secondary notification backend
--collect-all plyer                               # All plyer platform modules
--collect-all win10toast                          # Win10toast dependencies
```
**Why:** New notification system uses `plyer` (primary) and `win10toast` (fallback) for desktop notifications.

#### 2. System Tray Icon Support
```powershell
--hidden-import=pystray                           # System tray functionality
--hidden-import=PIL                               # Required by pystray
--hidden-import=PIL.Image                         # Image handling
--hidden-import=PIL.ImageDraw                     # Icon drawing
```
**Why:** System tray icon needs PIL (Pillow) for icon rendering.

#### 3. License Encryption Support
```powershell
--hidden-import=cryptography                      # Encryption library
--hidden-import=cryptography.fernet               # Fernet cipher for license files
```
**Why:** License files are encrypted using Fernet cipher.

#### 4. Multi-Threading Support
```powershell
--hidden-import=threading                         # Thread management
--hidden-import=concurrent.futures                # ThreadPoolExecutor
--hidden-import=queue                             # Thread-safe queues
```
**Why:** ScanVault now uses ThreadPoolExecutor with 6 workers for concurrent scanning.

#### 5. Windows API Support (Enhanced)
```powershell
--hidden-import=pywin32                           # Base Windows API
--hidden-import=win32api                          # Windows API functions
--hidden-import=win32con                          # Windows constants
--hidden-import=win32gui                          # GUI functions
--hidden-import=win32gui_struct                   # GUI structures
--hidden-import=win32file                         # File operations (named pipe)
--hidden-import=pywintypes                        # Windows types
```
**Why:** Named pipe communication, tray balloon notifications, and system integration.

#### 6. Core Dependencies (Existing)
```powershell
--hidden-import=yara                              # YARA malware detection
--hidden-import=requests                          # API communication
--hidden-import=psutil                            # Process management
```
**Why:** Core functionality from previous version.

---

## Build Output Structure

```
dist/
├── VWAR.exe                    # Main executable (35-45 MB)
├── quarantine/                 # Runtime folder for quarantined files
├── scanvault/                  # Runtime folder for vaulted files
├── data/                       # Runtime folder for application data
├── assets/
│   ├── VWAR.ico               # Application icon
│   └── yara/                  # YARA rule files
│       ├── ransomware/
│       ├── spyware/
│       ├── trojans/
│       └── worms/
└── vwar_monitor/
    └── vwar_monitor.exe       # C++ real-time monitor
```

---

## Critical Files Required Before Build

### 1. Source Files (Python)
- ✅ `main.py` - Entry point
- ✅ `app_main.py` - Main GUI application
- ✅ `config.py` - Configuration constants

### 2. Assets
- ✅ `assets/VWAR.ico` - Application icon
- ✅ `assets/yara/` - YARA rule files (must contain .yar files)

### 3. Native Components
- ✅ `vwar_monitor/vwar_monitor.exe` - C++ file monitor (compiled separately)

### 4. Manifest
- ✅ `vwar.manifest` - Windows manifest for admin privileges

---

## PyInstaller Flags Explained

### Basic Flags
- `--noconfirm` - Overwrite output without confirmation
- `--onefile` - Bundle everything into single executable
- `--windowed` - Hide console window (GUI app)
- `--name VWAR` - Output executable name

### Icon & Manifest
- `--icon=assets/VWAR.ico` - Application icon
- `--manifest=vwar.manifest` - Windows manifest (UAC, admin)

### Data Files (--add-data)
Format: `"source;destination"`
- `"assets/VWAR.ico;assets"` - Icon for notifications
- `"assets/yara;assets/yara"` - YARA rules
- `"vwar_monitor;vwar_monitor"` - C++ monitor executable

### Hidden Imports (--hidden-import)
PyInstaller can't auto-detect these imports:
- **Dynamic imports** (imported conditionally)
- **Platform-specific modules** (win32api, plyer.platforms.win)
- **Plugin architectures** (plyer backends)
- **C extensions** (yara, cryptography)

### Collection Flags (--collect-all)
- `--collect-all plyer` - Include all plyer platform backends
- `--collect-all win10toast` - Include win10toast resources

---

## Build Process Steps

### 1. Pre-Build Checks
```powershell
# Check Python environment
python --version  # Should be 3.11.5+

# Verify dependencies installed
pip list | Select-String "plyer|win10toast|yara|cryptography|pywin32"

# Check critical files
Test-Path main.py
Test-Path assets/VWAR.ico
Test-Path vwar_monitor/vwar_monitor.exe
```

### 2. Clean Previous Builds
```powershell
Remove-Item -Recurse -Force .\dist, .\build, .\VWAR.spec -ErrorAction SilentlyContinue
```

### 3. Run PyInstaller
```powershell
.\build_vwar.ps1
```

### 4. Post-Build Verification
```powershell
# Check executable exists
Test-Path .\dist\VWAR.exe

# Check size (should be 35-45 MB)
(Get-Item .\dist\VWAR.exe).Length / 1MB

# Verify bundled files
Test-Path .\dist\assets\yara
Test-Path .\dist\vwar_monitor\vwar_monitor.exe
```

---

## Testing the Built Executable

### Test Checklist

#### 1. Launch Test
```powershell
cd dist
.\VWAR.exe
```
**Expected:** Application launches without console window, requests admin elevation.

#### 2. Activation Test
- Enter license key
- Verify 2-device slot detection
- Check "Device Limit Reached" error with 3rd device

#### 3. Notification Test
- Start a scan
- Verify "Scan Started" notification appears
- Verify "Scan Complete" notification appears with file count
- Check notifications are non-blocking (UI responsive)

#### 4. Real-Time Monitoring Test
- Enable "Start Auto Scanning"
- Create a test file in Downloads
- Verify file captured in ScanVault
- Check C++ monitor running (`vwar_monitor.exe` in Task Manager)

#### 5. Installation Mode Test
- Click "🔧 Installation Mode" button
- Verify countdown timer working (10:00 → 09:59 → ...)
- Download an `.msi` file
- Verify file skipped from ScanVault

#### 6. License Validation Test
- Wait 10 seconds (background validation check)
- Verify no errors in logs
- Check license validator thread running

#### 7. Multi-Threading Test
- Copy multiple files to monitored folder
- Check Task Manager → VWAR.exe → Threads (should show 6+ worker threads)
- Verify concurrent scanning working

---

## Common Build Issues & Solutions

### Issue 1: "Module not found: plyer"
**Cause:** Hidden import not specified
**Solution:** Add `--hidden-import=plyer.platforms.win.notification`

### Issue 2: "No module named 'win10toast'"
**Cause:** win10toast not collected
**Solution:** Add `--collect-all win10toast`

### Issue 3: Notifications not working in built EXE
**Cause:** Plyer platform backends not included
**Solution:** Add `--collect-all plyer`

### Issue 4: YARA rules not found
**Cause:** `assets/yara` not bundled correctly
**Solution:** Verify `--add-data "assets/yara;assets/yara"` syntax (semicolon on Windows)

### Issue 5: C++ monitor not starting
**Cause:** `vwar_monitor.exe` not included
**Solution:** Verify `--add-data "vwar_monitor;vwar_monitor"` and check file exists

### Issue 6: Executable too large (>100 MB)
**Cause:** Unnecessary dependencies included
**Solution:** Use virtual environment with only required packages

### Issue 7: "Failed to execute script main"
**Cause:** Missing hidden imports or corrupted build
**Solution:** 
1. Delete `build/` and `dist/` folders
2. Add missing `--hidden-import` flags
3. Rebuild with `--noconfirm`

---

## Size Optimization Tips

### Current Expected Size: 35-45 MB

**If larger than 50 MB:**

1. **Remove unused modules from requirements.txt**
   ```bash
   pip uninstall <unused-package>
   ```

2. **Use UPX compression** (optional)
   ```powershell
   # Download UPX from https://upx.github.io/
   pyinstaller ... --upx-dir=C:\path\to\upx
   ```

3. **Exclude unnecessary packages**
   ```powershell
   --exclude-module matplotlib  # If not used
   --exclude-module numpy       # If not used
   ```

---

## Build Performance

### Build Time Expectations
- **Clean Build:** 2-3 minutes
- **Incremental Build:** 1-2 minutes (if using `--noconfirm`)

### Hardware Recommendations
- **CPU:** 4+ cores (faster compilation)
- **RAM:** 8+ GB (PyInstaller is memory-intensive)
- **Disk:** SSD (faster I/O during bundling)

---

## Version-Specific Notes

### VWAR v2.0 (Current)
- **New Features:**
  - 2-device license support
  - Non-blocking notifications (plyer + win10toast)
  - Multi-threaded ScanVault (6 workers)
  - Real-time license validation (6-hour checks)
  - Installation Mode (10-minute timer)
  
- **New Dependencies:**
  - `plyer==2.1.0`
  - `win10toast==0.9`
  - `cryptography==45.0.6`
  - `concurrent.futures` (built-in, but needs explicit import)

---

## CI/CD Integration (Optional)

### GitHub Actions Example
```yaml
name: Build VWAR.exe

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: .\build_vwar.ps1
      - uses: actions/upload-artifact@v2
        with:
          name: VWAR-EXE
          path: dist/VWAR.exe
```

---

## Final Checklist Before Distribution

- [ ] Build with `build_vwar.ps1`
- [ ] Test all 7 features (activation, notifications, monitoring, etc.)
- [ ] Verify C++ monitor included (`vwar_monitor.exe`)
- [ ] Check YARA rules bundled (`.yar` files)
- [ ] Test on clean Windows machine (no Python installed)
- [ ] Verify admin elevation works
- [ ] Check license validation (6-hour interval)
- [ ] Test Installation Mode countdown
- [ ] Verify 2-device license limit enforcement
- [ ] Check file size (35-45 MB expected)
- [ ] Scan with antivirus (ensure not flagged as false positive)

---

## Support & Troubleshooting

**Build Logs:**
- Check `build/` folder for detailed PyInstaller logs
- Review `VWAR.spec` file for generated configuration

**Runtime Logs:**
- Application logs in `data/` folder
- Check Windows Event Viewer for errors

**Contact:**
- Technical Support: https://bitss.one/contact
- GitHub Issues: https://github.com/TM-Mehrab-Hasan/BITSS-VWAR-Software/issues

---

**Last Updated:** October 21, 2025  
**Build Script Version:** 2.0  
**Minimum Python:** 3.11.5  
**Target OS:** Windows 10/11 (64-bit)
