# 🛡️ VWAR Scanner

**Professional-Grade Real-Time Malware Detection System**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/TM-Mehrab-Hasan/BITSS-VWAR-Software)
[![Python](https://img.shields.io/badge/python-3.11.5+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](https://bitss.one)

VWAR Scanner is an advanced malware detection and prevention system that combines YARA rule-based scanning with real-time file monitoring, providing comprehensive protection against ransomware, spyware, trojans, worms, and APT malware.

**Developed by [Bitss.one](https://bitss.one)**

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Core Components](#-core-components)
- [Usage Guide](#-usage-guide)
- [Configuration](#-configuration)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [License & Support](#-license--support)

---

## ✨ Key Features

### 🛡️ Real-Time Protection
- **C++ Monitor Integration**: High-performance file system monitoring using native Windows APIs
- **Python Watchdog**: Fallback monitoring for comprehensive coverage
- **Multi-Drive Support**: Monitors Downloads, Desktop, Documents, and all non-system drives
- **Instant Threat Detection**: Scans files immediately upon creation or modification
- **Minimal Performance Impact**: <2% CPU usage, ~50-100MB RAM

### 🔍 Advanced Threat Detection
- **YARA Rules Engine**: Industry-standard pattern matching for malware signatures
- **Multiple Threat Categories**: Ransomware, spyware, trojans, worms, APT malware
- **Regular Updates**: Expandable rule sets for emerging threats
- **Low False Positives**: Optimized detection algorithms
- **Customizable Rules**: Add custom YARA rules for specific threats

### 📦 ScanVault System
- **Innovative File Isolation**: Captures files before execution for safe scanning
- **Automated Workflow**: Scan → Restore (if clean) or Quarantine (if threat)
- **Zero-Day Protection**: Prevents malware execution during download
- **Metadata Preservation**: Maintains original file information for restoration
- **Intelligent Handling**: Special treatment for installers and trusted files

### 🔐 Quarantine Management
- **Secure Isolation**: Threats stored in protected quarantine folder
- **Detailed Metadata**: File path, detection time, matched rules preserved
- **Restore Capability**: False positives can be restored with re-scanning
- **Manual Review**: Inspect and manage quarantined items
- **Permanent Deletion**: Safely remove confirmed threats

### ⏰ Flexible Scheduling
- **Multiple Frequencies**: Realtime, Hourly, Twice Daily, Daily, Custom intervals
- **Time Selection**: Intuitive hour/minute spinbox controls
- **Path Configuration**: Scan specific folders and drives
- **Subdirectory Options**: Include/exclude nested folders
- **Background Execution**: Non-intrusive scanning during scheduled times
- **Manual Triggers**: "Run Now" button for immediate execution

### 💾 Backup & Restore
- **Manual Backups**: User-initiated file and folder backups
- **Automatic Backups**: Schedule regular backup tasks
- **Version History**: Multiple backup versions preserved
- **Easy Restoration**: Quick recovery of backed-up files
- **Configurable Storage**: Choose backup destination

### 🔒 Hardware-Locked Activation
- **Secure Licensing**: License bound to CPU + Motherboard IDs
- **Multi-Device Support**: Each license supports up to **2 devices**
- **Smart Device Management**: Automatic slot allocation (Device 1 & Device 2)
- **Online Validation**: Encrypted API communication for verification
- **Real-Time Validation**: Re-validates every 6 hours + time-jump detection
- **Renewal System**: 7-day advance warning before expiration
- **Grace Period**: Warnings before expiration
- **Graceful Degradation**: View quarantine after expiry (scanning disabled)
- **Offline Mode**: Grace period for temporary internet loss

### 🖥️ Modern User Interface
- **Intuitive Design**: Clean, professional Tkinter GUI
- **Color-Coded Theme**: Consistent cyan (#009AA5) and teal (#004d4d) palette
- **System Tray Integration**: Minimize to tray for background operation
- **Tabbed Help System**: Comprehensive documentation built-in
- **Real-Time Status**: Live monitoring indicators and progress displays

### 🔔 Smart Notifications
- **Desktop Alerts**: Toast notifications for critical events (via win10toast)
  - ✅ Scan started/completed notifications
  - ✅ Threat detection alerts with rule names
  - ✅ Scheduled scan completion summaries
- **Dynamic Tray Tooltips**: Real-time status updates in system tray
  - Shows current scanning file during manual scans
  - Updates during scheduled scan operations
  - Resets to idle state when complete
- **In-App Progress Bars**: Visual feedback on scan pages
- **Scheduled Scan Modals**: Detailed progress for automated scans
- **Customizable**: Enable/disable notification types in Settings

### 🔄 Automatic Updates
- **GitHub Integration**: Checks for updates via GitHub releases
- **Version Comparison**: Automatic detection of newer versions
- **Download Links**: Direct access to latest releases
- **Change Logs**: View what's new in updates

---

## 🏗️ Architecture

```
VWAR Scanner Architecture
├── Frontend (Tkinter GUI)
│   ├── Main Window (app_main.py)
│   ├── Scan Page (manual scanning)
│   ├── Backup Pages (backup/restore)
│   ├── Monitor Page (quarantine/scanvault management)
│   ├── Schedule Page (automated scanning)
│   └── Help Page (tabbed documentation)
│
├── Core Scanning Engine
│   ├── YARA Engine (yara_engine.py)
│   ├── Scanner Core (scanner_core.py)
│   ├── ScanVault Processor (scanvault.py, vault_processor.py)
│   └── Quarantine System (quarantine.py)
│
├── Real-Time Monitoring
│   ├── C++ Monitor (vwar_monitor.exe) - Native performance
│   ├── Python Monitor (real_time_monitor.py) - Watchdog integration
│   ├── Pipe Communication (pipe_client.py) - Inter-process messaging
│   └── Event Queue - Asynchronous file processing
│
├── Scheduled Tasks
│   ├── Scheduled Scanner (scheduled_scan.py)
│   ├── Auto Backup (auto_backup.py)
│   └── Configuration Management (JSON-based)
│
├── Licensing & Security
│   ├── Hardware ID (hwid.py) - CPU/Motherboard fingerprinting
│   ├── License Validation (license_utils.py) - Online verification
│   ├── Activation GUI (gui.py) - User activation interface
│   └── Encrypted Storage (Fernet encryption)
│
└── Utilities
    ├── Logging (logger.py) - Event tracking & telemetry
    ├── Notifications (notify.py) - Desktop alerts
    ├── Exclusions (exclusions.py) - Path filtering
    ├── System Tray (tray.py) - Background operation
    ├── Startup Manager (startup.py) - Windows integration
    └── Update Checker (update_checker.py) - Version management
```

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.11.5 or later
- **RAM**: 4 GB
- **Disk Space**: 500 MB (plus space for quarantine and backups)
- **CPU**: Dual-core processor
- **Internet**: Required for activation and updates

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **Python**: 3.11.5+
- **RAM**: 8 GB or more
- **Disk Space**: 2 GB+ (for extensive quarantine storage)
- **CPU**: Quad-core processor or better
- **Internet**: Broadband connection

### Dependencies
See [requirements.txt](requirements.txt) for complete list. Key dependencies:
- `yara-python` - YARA rules engine
- `watchdog` - File system monitoring
- `pywin32` - Windows API integration
- `cryptography` - License encryption
- `requests` - API communication
- `psutil` - System monitoring
- `pillow` - Image handling
- `win10toast` - Desktop notifications

---

## 📥 Installation

### Option 1: Executable (Recommended for End Users)

1. Download the latest `VWAR.exe` from [Releases](https://github.com/TM-Mehrab-Hasan/BITSS-VWAR-Software/releases)
2. Extract to desired location (e.g., `C:\Program Files\VWAR\`)
3. **Right-click** on `VWAR.exe` → **Run as Administrator**
4. Enter your license key when prompted
5. VWAR will start and create a system tray icon

### Option 2: From Source (For Developers)

1. **Clone the repository**
   ```bash
   git clone https://github.com/TM-Mehrab-Hasan/BITSS-VWAR-Software.git
   cd BITSS-VWAR-Software
   ```

2. **Install Python 3.11.5+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure "Add to PATH" is checked during installation

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run VWAR**
   ```bash
   python main.py
   ```
   Or use **Run as Administrator** from PowerShell:
   ```powershell
   Start-Process python -ArgumentList "main.py" -Verb RunAs
   ```

### Option 3: Build Executable (For Distribution)

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build executable:
   ```bash
   pyinstaller VWAR.spec
   ```

3. Executable will be in `dist/` folder

---

## 🚀 Quick Start

### First Launch

1. **Run as Administrator** (required for system-wide monitoring)
2. **Activate License**: Enter license key when prompted
   - ✅ Each license supports **2 devices**
   - 🔹 First activation uses **Device Slot 1**
   - 🔹 Second device uses **Device Slot 2**
   - ⚠️ Third device will be blocked (max 2 devices)
3. **Main Interface Opens**: VWAR starts with real-time protection enabled

### Basic Operations

**Manual Scan:**
1. Go to **Scan** page
2. Click **Browse** to select files/folders
3. Click **Start Scan**
4. Review results and take action on threats

**Schedule Automatic Scans:**
1. Go to **Schedule Scan** page
2. Choose frequency (Hourly, Daily, Custom)
3. Set time using spinbox controls
4. Add paths to scan
5. Click **Save**

**Review Threats:**
1. Go to **Scan Vault** page
2. View quarantined items
3. Select and **Restore** (if false positive) or **Delete** (if confirmed threat)

**System Tray:**
- Click **X** button → Minimize to tray (stays running)
- Right-click tray icon → Quick actions menu
- Use **Quit VWAR** button to exit completely

---

## 🔧 Core Components

### 1. Real-Time Monitoring
**File**: `RMonitoring/real_time_monitor.py`

Monitors file system events and queues files for scanning. Integrates with C++ monitor for performance.

**Key Features:**
- Rename following (handles `.crdownload` → final file)
- File stabilization (waits for download completion)
- Duplicate suppression
- Intelligent exclusions

### 2. YARA Engine
**File**: `Scanning/yara_engine.py`

Compiles and manages YARA rules for threat detection.

**Rule Categories:**
- `ransomware/` - File encryption malware
- `spyware/` - Data theft malware
- `trojans/` - Backdoor access
- `worms/` - Self-replicating malware
- `security/` - Generic malware patterns

### 3. ScanVault System
**Files**: `Scanning/scanvault.py`, `Scanning/vault_processor.py`

Captures files before execution, scans in isolation, then restores or quarantines.

**Process Flow:**
```
File Created → Move to ScanVault → Scan → Clean? → Restore
                                         ↓ Threat
                                    Quarantine
```

### 4. Scheduler
**File**: `Scanning/scheduled_scan.py`

Manages automated scanning with flexible frequency options.

**Frequencies:**
- **Realtime**: Continuous monitoring (always active)
- **Hourly**: Every hour at specified minute
- **Twice Daily**: Two specific times per day
- **Daily**: Once per day at specified time
- **Custom**: User-defined interval in minutes

### 5. License System
**Files**: `activation/license_utils.py`, `activation/hwid.py`, `activation/gui.py`

Hardware-locked licensing with online validation and **multi-device support**.

**Security Features:**
- CPU + Motherboard fingerprinting
- **2-Device License Support**: Each key activates 2 separate devices
- **Smart Slot Allocation**: Auto-assigns Device 1 and Device 2 slots
- **Device Verification**: Checks both slots during validation
- Fernet encryption for local storage
- SHA256 key derivation
- Periodic validation (every 6 hours)
- Time-jump detection (prevents date manipulation)
- 7-day expiry warnings
- Graceful degradation on expiry

---

## 📖 Usage Guide

### Command-Line Arguments

```bash
python main.py [OPTIONS]
```

**Options:**
- `--silent` - Run background services only (no GUI)
- `--tray` - Start minimized to system tray
- `--help` - Show help message and exit

**Examples:**
```bash
# Normal launch with GUI
python main.py

# Start minimized to tray
python main.py --tray

# Background mode (services only)
python main.py --silent
```

### Configuration Files

**Location**: `data/` folder

- `activation.enc` - Encrypted license data
- `scan_schedule.json` - Scheduled scan configuration
- `auto_backup.json` - Auto backup settings
- `vwar.log` - Application log file

### YARA Rules

**Location**: `assets/yara/`

**Adding Custom Rules:**
1. Create `.yar` file in appropriate subfolder
2. Follow YARA syntax guidelines
3. Restart VWAR to load new rules

**Rule Structure:**
```yara
rule MalwareName
{
    meta:
        description = "Description of threat"
        author = "Your Name"
        date = "2025-01-01"
    
    strings:
        $string1 = "suspicious pattern"
        $hex1 = { 4D 5A 90 00 }
    
    condition:
        any of them
}
```

---

## ⚙️ Configuration

### Startup with Windows

1. Go to **Schedule Scan** page
2. Enable **"Start with Windows"** checkbox
3. Optional: **"Start minimized to tray"** for silent startup

### Exclusions

VWAR automatically excludes:
- System folders (Windows, Program Files)
- Recycle Bin
- Temporary files (`.tmp`, `.log`)
- Partial downloads (`.crdownload`, `.part`)
- VWAR's own folders

### Debug Mode

Enable in **Schedule Scan** page:
- **"Enable Debug Logging"** checkbox
- Prints diagnostic messages to console
- Useful for troubleshooting

---

## 👨‍💻 Development

### Project Structure

```
VWAR_exe_2/
├── main.py                 # Entry point
├── app_main.py            # Main GUI application
├── config.py              # Configuration constants
├── requirements.txt       # Python dependencies
├── VWAR.spec             # PyInstaller build spec
│
├── activation/           # License & activation
├── Backup/              # Backup system
├── RMonitoring/         # Real-time monitoring
├── Scanning/            # Core scanning engine
├── utils/               # Utility functions
├── assets/              # YARA rules, icons
├── data/                # User data & config
├── quarantine/          # Quarantined files
├── scanvault/           # ScanVault temporary storage
└── vwar_monitor/        # C++ monitor executable
```

### Building from Source

**Requirements:**
- Visual Studio Build Tools (for C++ monitor)
- Python 3.11.5+
- PyInstaller

**Steps:**
1. Compile C++ monitor:
   ```bash
   cd vwar_monitor
   cl /EHsc vwar_monitor.cpp
   ```

2. Build Python executable:
   ```bash
   pyinstaller VWAR.spec
   ```

3. Test build:
   ```bash
   cd dist
   VWAR.exe
   ```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Testing

Run tests:
```bash
python -m pytest tests/
```

Key test files:
- `tests/test_exclusions.py` - Path exclusion logic
- `tests/test_scheduled_scan.py` - Scheduler functionality

---

## 🐛 Troubleshooting

### Common Issues

**Issue: VWAR won't start**
- Solution: Run as Administrator
- Check: Python 3.11.5+ installed
- Verify: All dependencies installed (`pip install -r requirements.txt`)

**Issue: Real-time monitoring not working**
- Check: Administrator privileges
- Verify: `vwar_monitor.exe` exists
- Look for: Error messages in console

**Issue: License validation failed**
- Check: Internet connection
- Verify: License key is correct
- Contact: support@bobosohomail.com

**Issue: "Device Limit Reached" error**
- Cause: License already activated on 2 other devices
- Solution: Deactivate one existing device first
- Note: Each license supports maximum 2 devices
- Contact: support@bobosohomail.com to manage devices

**Issue: "Device no longer authorized" error**
- Cause: Device was removed from license slots
- Solution: Re-activate with license key (will use available slot)
- Note: Admin may have reassigned device slot to another PC
- Contact: support@bobosohomail.com if unauthorized

**Issue: False positive detection**
- Solution: Restore from Scan Vault page
- Report: Email support with file details
- Note: File will be re-scanned on restore

**Issue: High CPU usage**
- Normal: During active scanning
- Check: Scheduled scan frequency
- Reduce: Number of monitored paths

### Logs

**Console Output:**
- Run from terminal to see real-time logs
- Look for `[ERROR]`, `[WARNING]` messages

**Log File:**
- Location: `data/vwar.log`
- Contains: Scan results, detections, errors

### Getting Help

1. Check **Help** page in application (5 comprehensive tabs)
2. Review **FAQ** and **Troubleshooting** sections
3. Email: support@bobosohomail.com
4. Include: VWAR version, error messages, steps to reproduce

---

## 📄 License & Support

### License

VWAR Scanner is proprietary software developed by **Bitss.one**.

- **License Type**: Hardware-locked, subscription-based
- **Activation Required**: Valid license key needed
- **Renewal**: Contact support before expiration
- **Terms**: See License Terms in application

### Support

**Developer**: Bitss.one  
**Website**: [https://bitss.one](https://bitss.one)  
**Email**: support@bobosohomail.com  
**Support Hours**: Mon-Fri 9AM-6PM GMT, Sat 10AM-4PM GMT

### Contact

- **Sales Inquiries**: support@bobosohomail.com
- **Technical Support**: support@bobosohomail.com
- **Bug Reports**: support@bobosohomail.com
- **Feature Requests**: support@bobosohomail.com

### Acknowledgments

- **YARA**: Pattern matching engine by VirusTotal
- **Python Community**: For excellent libraries and tools
- **Contributors**: All developers who contributed to this project

---

## 📊 Version History

### v1.0.0 (Current - October 2025)
- ✅ Real-time malware detection with C++ monitor
- ✅ YARA-based scanning engine
- ✅ ScanVault file isolation system
- ✅ Flexible scheduled scanning (Hourly/Daily/Custom)
- ✅ System tray integration with minimize-to-tray
- ✅ **2-Device License Support** (NEW!)
- ✅ **Real-Time License Validation** (6-hour checks, time-jump detection)
- ✅ **Enhanced Toast Notifications** (Scan events, threat alerts)
- ✅ **Dynamic Tray Tooltips** (Real-time scan status)
- ✅ Hardware-locked licensing with encryption
- ✅ Backup & restore system
- ✅ Modern tabbed help system with 5 comprehensive tabs
- ✅ Hour/minute time picker spinboxes
- ✅ Comprehensive documentation

### Roadmap (Coming Soon)
- 🔄 Installation Mode toggle for software installers
- 🔄 Multi-threaded ScanVault processing
- 🔄 Custom exclusion lists in Settings
- 🔄 Digital signature verification for trusted publishers
- 🔄 Cloud-based rule updates
- 🔄 Multi-language support
- 🔄 Advanced reporting & analytics

---

## 🌟 Screenshots

*GUI screenshots will be added in future releases*

---

## ⚠️ Disclaimer

VWAR Scanner is designed to complement existing security solutions, not replace them. While we strive for high detection rates, no security software can guarantee 100% protection. Always practice safe computing habits and maintain regular backups.

---

**Made with ❤️ by [Bitss.one](https://bitss.one)**

**© 2025 Bitss.one. All rights reserved.**
