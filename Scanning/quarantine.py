# # Scanning/quarantine.py

# import os
# import shutil
# import json
# import hashlib
# from datetime import datetime
# import time
# from config import QUARANTINE_FOLDER
# from utils.logger import log_message


# def quarantine_file(file_path, matched_rules=None):
#     """
#     Moves a suspicious file to the quarantine folder and writes a .meta file.

#     Args:
#         file_path (str): Path to the suspicious file.
#         matched_rules (list): List of matched YARA rule names.

#     Returns:
#         str: Path to the quarantined file (not .meta).
#     """
#     if not os.path.exists(file_path):
#         raise RuntimeError(f"File no longer exists: {file_path}")

#     os.makedirs(QUARANTINE_FOLDER, exist_ok=True)

#     try:
#         file_name = os.path.basename(file_path)
#         # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#         timestamp_raw = datetime.now()
#         timestamp_file = timestamp_raw.strftime("%Y%m%d%H%M%S")       # For file name
#         timestamp_human = timestamp_raw.strftime("%Y-%m-%d %H:%M:%S") # For metadata
        

#         # Use SHA-256 hash of the full original path (short & unique)
#         path_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
#         quarantine_filename = f"{file_name}__{timestamp_file}__{path_hash}.quarantined"
#         quarantine_path = os.path.join(QUARANTINE_FOLDER, quarantine_filename)

#         # Move the file to quarantine
#         # shutil.move(file_path, quarantine_path)
#         # Move the file with retry in case the file is temporarily locked or renamed
#         for attempt in range(3):
#             if os.path.exists(file_path):
#                 try:
#                     shutil.move(file_path, quarantine_path)
#                     break  # ✅ success, exit retry loop
#                 except Exception as e:
#                     if attempt == 2:
#                         raise RuntimeError(f"Move failed after 3 attempts: {e}")
#                     time.sleep(0.3)
#             else:
#                 time.sleep(0.3)
#         else:
#             raise RuntimeError(f"File no longer exists after waiting: {file_path}")

#         # Write metadata
#         meta_path = quarantine_path + ".meta"
#         metadata = {
#             "original_path": file_path,
#             "quarantined_path": quarantine_path,
#             "timestamp": timestamp_human,
#             "matched_rules": matched_rules or [],
#         }

#         with open(meta_path, "w", encoding="utf-8") as meta_file:
#             json.dump(metadata, meta_file, indent=4)

#         log_message(f"[QUARANTINED] {file_path} → {quarantine_path}")
#         return quarantine_path

#     except Exception as e:
#         raise RuntimeError(f"Failed to quarantine {file_path}: {e}")


# import os
# import shutil
# import json
# import hashlib
# import time
# from datetime import datetime

# from config import QUARANTINE_FOLDER
# from utils.logger import log_message


# def quarantine_file(file_path, matched_rules=None):
#     """
#     Moves a suspicious file to the quarantine folder and writes a .meta file,
#     but only if the file is successfully moved.

#     Args:
#         file_path (str): Path to the suspicious file.
#         matched_rules (list): List of matched YARA rule names.

#     Returns:
#         str: Path to the quarantined file (not .meta).
#     """
#     if not os.path.exists(file_path):
#         raise RuntimeError(f"File no longer exists: {file_path}")

#     os.makedirs(QUARANTINE_FOLDER, exist_ok=True)

#     try:
#         file_name = os.path.basename(file_path)

#         # Generate timestamp and hash
#         timestamp_raw = datetime.now()
#         timestamp_file = timestamp_raw.strftime("%Y%m%d%H%M%S")
#         timestamp_human = timestamp_raw.strftime("%Y-%m-%d %H:%M:%S")
#         path_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]

#         quarantine_filename = f"{file_name}__{timestamp_file}__{path_hash}.quarantined"
#         quarantine_path = os.path.join(QUARANTINE_FOLDER, quarantine_filename)

#         # Move the file with retries
#         for attempt in range(3):
#             if os.path.exists(file_path):
#                 try:
#                     shutil.move(file_path, quarantine_path)
#                     break  # Success
#                 except Exception as e:
#                     if attempt == 2:
#                         raise RuntimeError(f"Move failed after 3 attempts: {e}")
#                     time.sleep(0.3)
#             else:
#                 time.sleep(0.3)
#         else:
#             raise RuntimeError(f"File no longer exists after waiting: {file_path}")

#         # Write metadata only if the file was successfully moved
#         if os.path.exists(quarantine_path):
#             meta_path = quarantine_path + ".meta"
#             metadata = {
#                 "original_path": file_path,
#                 "quarantined_path": quarantine_path,
#                 "timestamp": timestamp_human,
#                 "matched_rules": matched_rules or [],
#             }

#             with open(meta_path, "w", encoding="utf-8") as f:
#                 json.dump(metadata, f, indent=4)

#             # log_message(f"[QUARANTINED] {file_path} → {quarantine_path}")
#             print(f"line 147 qurainte.py [QUARANTINED] {file_path} → {quarantine_path}")
#             return quarantine_path
#         else:
#             raise RuntimeError(f"Quarantined file unexpectedly missing: {quarantine_path}")

#     except Exception as e:
#         raise RuntimeError(f"Failed to quarantine {file_path}: {e}")


import os
import shutil
import json
import hashlib
import time
from datetime import datetime

from config import QUARANTINE_FOLDER
from utils.logger import log_message


def quarantine_file(file_path, matched_rules=None):
    """
    Moves a suspicious file to the quarantine folder and writes a .meta file,
    but only if the file is successfully moved.

    Args:
        file_path (str): Path to the suspicious file.
        matched_rules (list): List of matched YARA rule names.

    Returns:
        str: Path to the quarantined file (not .meta).
    """
    if not os.path.exists(file_path):
        raise RuntimeError(f"File no longer exists: {file_path}")

    os.makedirs(QUARANTINE_FOLDER, exist_ok=True)

    try:
        file_name = os.path.basename(file_path)

        # Generate timestamp and hash
        timestamp_raw = datetime.now()
        timestamp_file = timestamp_raw.strftime("%Y%m%d%H%M%S")
        timestamp_human = timestamp_raw.strftime("%Y-%m-%d %H:%M:%S")
        path_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]

        quarantine_filename = f"{file_name}__{timestamp_file}__{path_hash}.quarantined"
        quarantine_path = os.path.join(QUARANTINE_FOLDER, quarantine_filename)

        # Move the file with retries
        for attempt in range(3):
            if os.path.exists(file_path):
                try:
                    shutil.move(file_path, quarantine_path)
                    break  # Success
                except Exception as e:
                    if attempt == 2:
                        raise RuntimeError(f"Move failed after 3 attempts: {e}")
                    time.sleep(0.3)
            else:
                time.sleep(0.3)
        else:
            raise RuntimeError(f"File no longer exists after waiting: {file_path}")

        # Write metadata only if the file was successfully moved
        if os.path.exists(quarantine_path):
            meta_path = quarantine_path + ".meta"
            normalized_path = os.path.abspath(file_path).replace("\\", "/").lower()
            metadata = {
                "original_path": normalized_path,
                "quarantined_path": quarantine_path,
                "timestamp": timestamp_human,
                "matched_rules": matched_rules or [],
            }

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)

            # log_message(f"[QUARANTINED] {file_path} → {quarantine_path}")
            # print(f"line 225 quraintine[QUARANTINED] {file_path} → {quarantine_path}")
            return quarantine_path
        else:
            raise RuntimeError(f"Quarantined file unexpectedly missing: {quarantine_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to quarantine {file_path}: {e}")
