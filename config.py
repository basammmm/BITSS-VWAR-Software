
# ACTIVATION_FILE = "data/activation.json"
# ICON_PATH = "assets/VWAR.ico"
# YARA_RULE_FOLDER = "assets/yara/"
# QUARANTINE_FOLDER = "quarantine"
# BACKUP_FOLDER = "VWARbackup"
CURRENT_VERSION = "3.0.0"

import os
from utils.path_utils import resource_path


API_GET = "https://bitts.fr/vwar_windows/getAPI.php"
API_POST = "https://bitts.fr/vwar_windows/postAPI.php"
# API endpoint for toggling or updating auto-renew setting on server
API_AUTO_RENEW = "https://bitts.fr/vwar_windows/autoReNew.php"
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

