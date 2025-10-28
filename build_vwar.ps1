# VWAR v3.0.0 Build Script with All Features
# Build Date: October 28, 2025
# Includes: Real-time validation (30s), Auto-renew sync, 2-device licensing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VWAR v3.0.0 Build Script" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean previous builds
Write-Host "[1/5] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path ".\build") { Remove-Item -Recurse -Force ".\build" }
if (Test-Path ".\dist") { Remove-Item -Recurse -Force ".\dist" }
if (Test-Path ".\VWAR.spec") { Remove-Item -Force ".\VWAR.spec" }
Write-Host "[OK] Cleaned" -ForegroundColor Green
Write-Host ""

# Run PyInstaller
Write-Host "[2/5] Building VWAR.exe with PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take 2-5 minutes..." -ForegroundColor Gray
Write-Host ""

pyinstaller --noconfirm --onefile --windowed `
  --icon=assets/VWAR.ico `
  --manifest=vwar.manifest `
  --name=VWAR `
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
  --hidden-import=tkinter `
  --hidden-import=tkinter.ttk `
  --hidden-import=tkinter.scrolledtext `
  --hidden-import=tkinter.messagebox `
  --hidden-import=tkinter.filedialog `
  --hidden-import=subprocess `
  --hidden-import=ctypes `
  --hidden-import=hashlib `
  --hidden-import=base64 `
  --hidden-import=datetime `
  --hidden-import=json `
  --hidden-import=pathlib `
  --collect-all plyer `
  --collect-all win10toast `
  main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Build completed" -ForegroundColor Green
Write-Host ""

# Create runtime directories
Write-Host "[3/5] Creating runtime directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path ".\dist\quarantine" | Out-Null
New-Item -ItemType Directory -Force -Path ".\dist\scanvault" | Out-Null
New-Item -ItemType Directory -Force -Path ".\dist\data" | Out-Null
Write-Host "[OK] Created quarantine, scanvault, data folders" -ForegroundColor Green
Write-Host ""

# Verify build
Write-Host "[4/5] Verifying build..." -ForegroundColor Yellow

if (Test-Path ".\dist\VWAR.exe") {
    $exe = Get-Item ".\dist\VWAR.exe"
    $sizeMB = [math]::Round($exe.Length / 1MB, 2)
    Write-Host "[OK] VWAR.exe created successfully" -ForegroundColor Green
    Write-Host "  File size: $sizeMB MB" -ForegroundColor Gray
    Write-Host "  Location: $($exe.FullName)" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] VWAR.exe not found!" -ForegroundColor Red
    exit 1
}

if (Test-Path ".\dist\vwar_monitor\vwar_monitor.exe") {
    Write-Host "[OK] C++ monitor included" -ForegroundColor Green
} else {
    Write-Host "[WARNING] C++ monitor not found" -ForegroundColor Yellow
}

if (Test-Path ".\dist\assets\yara") {
    $yaraCount = (Get-ChildItem ".\dist\assets\yara" -Recurse -Filter "*.yar").Count
    Write-Host "[OK] YARA rules included ($yaraCount files)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] YARA rules not found" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "[5/5] Build Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Version: 3.0.0" -ForegroundColor White
Write-Host "Build Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""
Write-Host "New Features Included:" -ForegroundColor White
Write-Host "  [OK] Real-time license validation (30 seconds)" -ForegroundColor Green
Write-Host "  [OK] Auto-renew sync between pages" -ForegroundColor Green
Write-Host "  [OK] 2-device licensing support" -ForegroundColor Green
Write-Host "  [OK] All API endpoints authenticated" -ForegroundColor Green
Write-Host "  [OK] Installation mode exclusions" -ForegroundColor Green
Write-Host "  [OK] Enhanced error handling" -ForegroundColor Green
Write-Host ""
Write-Host "Location: .\dist\VWAR.exe" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
