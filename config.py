
# ACTIVATION_FILE = "data/activation.json"
# ICON_PATH = "assets/VWAR.ico"
# YARA_RULE_FOLDER = "assets/yara/"
# QUARANTINE_FOLDER = "quarantine"
# BACKUP_FOLDER = "VWARbackup"
CURRENT_VERSION = "3.0.0"

import os
from utils.path_utils import resource_path


# ============================================================
# API ENDPOINTS - All endpoints now require authentication
# ============================================================

# License API
API_LICENSE_FETCH = "https://bitts.fr/vwar_windows/license-fetch"
API_LICENSE_FETCH_KEY = "FDD56B7B7C46658IBAD28EDCC83CE"

API_HW_INFO_INSERT = "https://bitts.fr/vwar_windows/hw-info-insert"
API_HW_INFO_INSERT_KEY = "E246F159FBC2B3F39227394CBBD76"

API_AUTO_RENEW = "https://bitts.fr/vwar_windows/autoReNew.php"
API_AUTO_RENEW_KEY = "E246F159FBC2B3F39227394CBBD76"

# Library API (YARA Rules)
API_YARA_INSERT = "https://library.bitss.one/vwar_windows/insert-rule"
API_YARA_INSERT_KEY = "93B78A8977A6617EB2BEDF4235848"

API_YARA_FETCH = "https://bitts.fr/vwar_windows/license-fetch"
API_YARA_FETCH_KEY = "7A6D317B24AAE34DD74B9B8E35E5F"

# Legacy endpoints (deprecated - use authenticated endpoints above)
API_GET = API_LICENSE_FETCH  # For backward compatibility
API_POST = API_HW_INFO_INSERT  # For backward compatibility

# Update URL - point to your repository's update info
UPDATE_URL = "https://raw.githubusercontent.com/TM-Mehrab-Hasan/BITSS-VWAR-Software/main/update_info.json"

# License validation polling interval (seconds)
# Set to 900 (15 minutes) for near-real-time enforcement. Adjust as needed to balance
# immediacy vs server load. Set to 60 for 1-minute checks (more aggressive).
LICENSE_VALIDATION_INTERVAL = 900



AUTO_BACKUP_CONFIG_PATH = "data/auto_backup.json"
SCHEDULED_SCAN_CONFIG_PATH = "data/scan_schedule.json"

# === General App Settings ===
APP_NAME = "VWAR Scanner"



# ICON_PATH = resource_path("assets/VWAR.ico")
ICON_PATH = "assets/VWAR.ico"

# === Activation ===
ACTIVATION_FILE = os.path.join("data", "activation.enc")

# === YARA Rule Handling ===
YARA_FOLDER = os.path.join("assets", "yara")

# === Quarantine ===
QUARANTINE_FOLDER = "quarantine"
SCANVAULT_FOLDER = "scanvault"

# === Backup Settings ===
BACKUP_FOLDER = "VWARbackup"
BACKUP_INTERVAL_SECONDS = 30

# === Auto Scan Settings ===
MONITOR_PATHS = [
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop")
]

# === Log File (optional future use) ===
LOG_FILE = os.path.join("data", "vwar.log")

# === Debug switches ===
# When True, logs old -> new path when following renames (.crdownload/.part to final)
RENAME_FOLLOW_DEBUG = True

# === ScanVault post-restore recheck ===
# Delay (in seconds) before re-scanning the restored file; keep small for faster feedback
POST_RESTORE_RECHECK_DELAY = 4

