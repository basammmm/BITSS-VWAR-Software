# import os
# import json
# from datetime import datetime
# from config import ACTIVATION_FILE
# from activation.hwid import get_processor_info, get_motherboard_info
# from cryptography.fernet import Fernet
# import base64, hashlib


# def generate_fernet_key_from_string(secret_string):
#     sha256 = hashlib.sha256(secret_string.encode()).digest()
#     return base64.urlsafe_b64encode(sha256)

# SECRET_KEY = generate_fernet_key_from_string("VWAR@BIFIN")
# fernet = Fernet(SECRET_KEY)

# def is_activated():
#     """
#     Return (True, None) if activated.
#     Return (False, reason) if not.
#     """
#     if not os.path.exists(ACTIVATION_FILE):
#         return False, "Activation file not found."

#     try:
#         # with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
#         #     data = json.load(f)
        
        
#         with open(ACTIVATION_FILE, "rb") as f:
#             encrypted = f.read()
            
#             decrypted = fernet.decrypt(encrypted)
#             data = json.loads(decrypted.decode("utf-8"))
            
#             # print("69 lincensse", data)

#         valid_till = data.get("valid_till")
#         cpu = data.get("processor_id")
#         mobo = data.get("motherboard_id")

#         if not (valid_till and cpu and mobo):
#             return False, "Activation data is incomplete."

#         # expiry = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
#         # if datetime.now() > expiry:
#         #     return False, "License expired."
        
#         created_at = data.get("created_at")

#         if not created_at:
#             return False, "Activation start date missing."

#         try:
#             start = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
#             end = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
#             now = datetime.now()

#             if not (start <= now <= end):
#                 return False, "License has expired."

#         except Exception as e:
#             return False, f"Failed to parse license dates: {e}"


#         current_cpu = get_processor_info()
#         current_mobo = get_motherboard_info()

#         if cpu != current_cpu or mobo != current_mobo:
#             return False, "Activation bound to another system."

#         return True, None

#     except Exception as e:
#         return False, f"Failed to validate activation: {e}"



import os
import requests
import json
import threading
import time
from datetime import datetime, timedelta
from config import (
    ACTIVATION_FILE, 
    API_LICENSE_FETCH, 
    API_LICENSE_FETCH_KEY,
    LICENSE_VALIDATION_INTERVAL
)
from activation.hwid import get_processor_info, get_motherboard_info
from cryptography.fernet import Fernet
import base64, hashlib

def generate_fernet_key_from_string(secret_string):
    sha256 = hashlib.sha256(secret_string.encode()).digest()
    return base64.urlsafe_b64encode(sha256)

SECRET_KEY = generate_fernet_key_from_string("VWAR@BIFIN")
fernet = Fernet(SECRET_KEY)


def _store_activation(record, cpu, mobo, auto_renew=False):
    """Save activation info locally to encrypted activation file."""
    try:
        os.makedirs(os.path.dirname(ACTIVATION_FILE), exist_ok=True)
        data = {
            "id": record["id"],
            "username": record["username"],
            "password": record["password"],
            "processor_id": cpu,
            "motherboard_id": mobo,
            "valid_till": record["valid_till"],
            "created_at": record.get("created_at", ""),
            "auto_renew": auto_renew
        }
        json_str = json.dumps(data).encode("utf-8")
        encrypted = fernet.encrypt(json_str)
        with open(ACTIVATION_FILE, "wb") as f:
            f.write(encrypted)
        print("[INFO] Activation info stored.")
    except Exception as e:
        print(f"[ERROR] Failed to store activation: {e}")


def get_auto_renew_status():
    """Get the current auto-renew status from local activation file."""
    try:
        if not os.path.exists(ACTIVATION_FILE):
            return False
        
        with open(ACTIVATION_FILE, "rb") as f:
            encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            data = json.loads(decrypted.decode("utf-8"))
        
        return data.get("auto_renew", False)
    except Exception as e:
        print(f"[ERROR] Failed to get auto-renew status: {e}")
        return False


def update_auto_renew_status(enabled):
    """
    Update auto-renew status locally and sync with server.
    
    Args:
        enabled (bool): Whether auto-renew should be enabled
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from config import API_AUTO_RENEW, API_AUTO_RENEW_KEY
    
    try:
        # Load current activation data
        if not os.path.exists(ACTIVATION_FILE):
            return False, "Activation file not found. Please activate first."
        
        with open(ACTIVATION_FILE, "rb") as f:
            encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            data = json.loads(decrypted.decode("utf-8"))
        
        license_id = data.get("id")
        if not license_id:
            return False, "License ID not found in activation data."
        
        # Update auto-renew on server
        # Database expects "YES" or "NO" strings
        payload = {
            "id": license_id,
            "auto_renew": "YES" if enabled else "NO"
        }
        
        headers = {
            "X-API-Key": API_AUTO_RENEW_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(API_AUTO_RENEW, json=payload, headers=headers, timeout=10)
        
        # Check if response is valid JSON
        try:
            result = response.json()
        except json.JSONDecodeError:
            return False, f"Server returned invalid response (Status: {response.status_code}). Please check API endpoint."
        
        if result.get("status") == "success":
            # Update local file
            data["auto_renew"] = enabled
            json_str = json.dumps(data).encode("utf-8")
            encrypted = fernet.encrypt(json_str)
            with open(ACTIVATION_FILE, "wb") as f:
                f.write(encrypted)
            
            status_text = "enabled" if enabled else "disabled"
            return True, f"Auto-renew {status_text} successfully."
        else:
            error_msg = result.get("message", result.get("error", "Server rejected auto-renew update."))
            return False, f"Failed to update auto-renew: {error_msg}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {e}"
    except json.JSONDecodeError as e:
        return False, f"Invalid server response. API may not be configured correctly."
    except Exception as e:
        return False, f"Error updating auto-renew: {e}"


def is_activated():
    """
    Return (True, None) if activated.
    Return (False, reason) if not.
    """
    if not os.path.exists(ACTIVATION_FILE):
        return False, "Activation file not found."

    try:
        # Load and decrypt local activation file
        with open(ACTIVATION_FILE, "rb") as f:
            encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            data = json.loads(decrypted.decode("utf-8"))

        valid_till = data.get("valid_till")
        created_at = data.get("created_at")
        cpu = data.get("processor_id")
        mobo = data.get("motherboard_id")

        if not (valid_till and created_at and cpu and mobo):
            return False, "Activation data is incomplete."

        # Get current hardware info early
        current_cpu = get_processor_info()
        current_mobo = get_motherboard_info()

        if cpu != current_cpu or mobo != current_mobo:
            return False, "Activation bound to another system."

        # Check dates
        start = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        if now < start:
            return False, "Activation start date is in the future."

        if now > end:
            # Local license expired → check server for renewal
            try:
                headers = {
                    "X-API-Key": API_LICENSE_FETCH_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "processor_id": current_cpu,
                    "motherboard_id": current_mobo
                }
                response = requests.post(API_LICENSE_FETCH, json=payload, headers=headers, timeout=5)
                records = response.json().get("data", [])
                found = next((r for r in records if r.get("password") == data.get("password")), None)

                if found:
                    server_valid_till = found.get("valid_till")
                    
                    # Verify device is still authorized (check both device slots)
                    device1_cpu = found.get("processor_id")
                    device1_mobo = found.get("motherboard_id")
                    device2_cpu = found.get("processor_id_2")
                    device2_mobo = found.get("motherboard_id_2")
                    
                    # Check if current device matches either slot
                    is_device1 = (current_cpu == device1_cpu and current_mobo == device1_mobo)
                    is_device2 = (current_cpu == device2_cpu and current_mobo == device2_mobo)
                    
                    if not (is_device1 or is_device2):
                        return False, "Device no longer authorized. This device has been removed from the license."
                    
                    if server_valid_till:
                        server_end = datetime.strptime(server_valid_till, "%Y-%m-%d %H:%M:%S")
                        if now <= server_end:
                            # ✅ Renewed on server → update local license
                            _store_activation(found, current_cpu, current_mobo)
                            return True, None

                return False, "License expired.\nThis license key has expired. Please renew your license.\nContact us at: https://bitss.one/contact"

            except Exception as e:
                return False, f"License expired. Failed to check renewal server: {e}"

        # Still valid locally
        return True, None

    except Exception as e:
        return False, f"Failed to validate activation: {e}"


# === Real-Time License Validation System ===

class LicenseValidator:
    """Background thread for real-time license validation.
    
    Features:
    - Periodic validation every 1 hour
    - Time-jump detection (>1 hour backward)
    - 7-day expiry warning notifications
    - Graceful degradation to view-only mode on expiry
    """
    
    def __init__(self, on_invalid_callback=None, on_expiry_warning_callback=None, on_valid_callback=None, app_instance=None):
        """Initialize license validator.
        
        Args:
            on_invalid_callback: Function to call when license becomes invalid
            on_expiry_warning_callback: Function to call for expiry warnings (days_left)
            on_valid_callback: Function to call when license becomes valid again (after renewal)
            app_instance: Reference to VWARScannerGUI app for timer reset
        """
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._last_check_time = None
        self._last_valid_till = None
        self.app = app_instance  # Store app reference for timer reset
        
        # Callbacks
        self.on_invalid = on_invalid_callback
        self.on_expiry_warning = on_expiry_warning_callback
        self.on_valid = on_valid_callback
        
    # Configuration
    # Use configurable interval (default set in config.py). This controls how often
    # the client syncs with the server to enforce server-side expiry.
        self.check_interval = LICENSE_VALIDATION_INTERVAL
        self.warning_days = 7  # Warn when 7 days or less remaining
        self.time_jump_threshold = 30  # 1 hour backward = suspicious
        
        # State tracking
        self.is_valid = True
        self.last_validation_time = None
        self.days_until_expiry = None
        
    def start(self):
        """Start background validation thread."""
        if self._running:
            return
        
        self._running = True
        self._last_check_time = time.time()
        
        # Perform initial validation
        self._validate()
        
        # Start background thread
        self._thread = threading.Thread(target=self._validation_loop, daemon=True, name="LicenseValidator")
        self._thread.start()
        
        print("[LICENSE] Real-time validation started (30 second intervals)")
    
    def stop(self):
        """Stop background validation thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        print("[LICENSE] Real-time validation stopped")
    
    def _validation_loop(self):
        """Main validation loop - runs every 1 hour."""
        while self._running:
            try:
                current_time = time.time()
                time_since_last_check = current_time - self._last_check_time
                
                # Detect time jump backward (system clock manipulation)
                if time_since_last_check < -self.time_jump_threshold:
                    print(f"[LICENSE] Time jump detected: {-time_since_last_check:.0f}s backward")
                    print("[LICENSE] Possible system clock manipulation - forcing validation")
                    self._validate()
                    self._last_check_time = current_time
                
                # Periodic validation every 1 hour
                elif time_since_last_check >= self.check_interval:
                    print("[LICENSE] Periodic validation check (30-Seconds interval)")
                    self._validate()
                    self._last_check_time = current_time
                
                # Sleep for 1 minute between checks
                time.sleep(60)
                
            except Exception as e:
                print(f"[LICENSE] Validation loop error: {e}")
                time.sleep(60)
    
    def _validate(self):
        """Perform license validation and trigger callbacks."""
        with self._lock:
            try:
                # Reset UI timer when validation starts
                if self.app and hasattr(self.app, 'reset_license_check_timer'):
                    try:
                        self.app.reset_license_check_timer()
                    except Exception as e:
                        print(f"[LICENSE] Failed to reset UI timer: {e}")
                
                activated, reason = is_activated()
                self.last_validation_time = datetime.now()
                
                if not activated:
                    # License is invalid
                    print(f"[LICENSE] Validation FAILED: {reason}")
                    self.is_valid = False
                    
                    # Trigger callback for invalid license
                    if self.on_invalid:
                        try:
                            self.on_invalid(reason)
                        except Exception as e:
                            print(f"[LICENSE] Callback error: {e}")
                    
                else:
                    # License is valid locally - perform a server sync to enforce
                    # server-side expiry/changes so that server updates are reflected
                    # in near-real-time.
                    print("[LICENSE] Validation PASSED (local); performing server sync")
                    self.is_valid = True

                    # Server synchronization: fetch authoritative record for this license
                    try:
                        # Read local activation to get the identifying password/hash
                        with open(ACTIVATION_FILE, "rb") as f:
                            encrypted = f.read()
                            decrypted = fernet.decrypt(encrypted)
                            data = json.loads(decrypted.decode("utf-8"))

                        local_password = data.get("password")
                        local_valid_till = data.get("valid_till")
                        
                        # Get current hardware info for POST request
                        current_cpu = get_processor_info()
                        current_mobo = get_motherboard_info()
                        
                        # Query server (API_LICENSE_FETCH requires POST with hardware info)
                        try:
                            headers = {
                                "X-API-Key": API_LICENSE_FETCH_KEY,
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "processor_id": current_cpu,
                                "motherboard_id": current_mobo
                            }
                            resp = requests.post(API_LICENSE_FETCH, json=payload, headers=headers, timeout=8)
                            records = resp.json().get("data", [])
                            server_record = next((r for r in records if r.get("password") == local_password), None)
                        except Exception as e:
                            server_record = None
                            print(f"[LICENSE] Server sync failed: {e}")

                        if server_record:
                            server_valid_till = server_record.get("valid_till")
                            if server_valid_till:
                                server_end = datetime.strptime(server_valid_till, "%Y-%m-%d %H:%M:%S")
                                now = datetime.now()
                                # If server has expired the license -> invalidate now
                                if now > server_end:
                                    print("[LICENSE] Server reports license expired -> invalidating")
                                    self.is_valid = False
                                    
                                    # Update local file with expired date so UI can show it
                                    try:
                                        current_cpu = get_processor_info()
                                        current_mobo = get_motherboard_info()
                                        _store_activation(server_record, current_cpu, current_mobo)
                                        print("[LICENSE] Local activation updated with expired date from server")
                                    except Exception as e:
                                        print(f"[LICENSE] Failed to update local activation: {e}")
                                    
                                    if self.on_invalid:
                                        try:
                                            self.on_invalid("License expired on server")
                                        except Exception as e:
                                            print(f"[LICENSE] on_invalid callback error: {e}")
                                    return
                                # If server extended validity beyond local, update local file
                                try:
                                    local_end = datetime.strptime(local_valid_till, "%Y-%m-%d %H:%M:%S") if local_valid_till else None
                                except Exception:
                                    local_end = None

                                if local_end is None or server_end > local_end:
                                    # Update local activation to match server authoritative record
                                    try:
                                        current_cpu = get_processor_info()
                                        current_mobo = get_motherboard_info()
                                        _store_activation(server_record, current_cpu, current_mobo)
                                        print("[LICENSE] Local activation updated from server record")
                                        
                                        # If we were invalid before but now license is extended/renewed and valid
                                        if not self.is_valid and now <= server_end:
                                            print("[LICENSE] License renewed/extended - restoring from view-only mode")
                                            self.is_valid = True
                                            if self.on_valid:
                                                try:
                                                    self.on_valid()
                                                except Exception as e:
                                                    print(f"[LICENSE] on_valid callback error: {e}")
                                    except Exception as e:
                                        print(f"[LICENSE] Failed to update local activation from server: {e}")

                    except Exception as e:
                        print(f"[LICENSE] Server sync error: {e}")
                    
                    # Check days until expiry
                    try:
                        with open(ACTIVATION_FILE, "rb") as f:
                            encrypted = f.read()
                            decrypted = fernet.decrypt(encrypted)
                            data = json.loads(decrypted.decode("utf-8"))
                        
                        valid_till = data.get("valid_till")
                        if valid_till:
                            end_date = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
                            days_left = (end_date - datetime.now()).days
                            self.days_until_expiry = days_left
                            
                            # Store for time-jump detection
                            self._last_valid_till = valid_till
                            
                            # Trigger warning if expiring soon
                            if 0 < days_left <= self.warning_days:
                                print(f"[LICENSE] WARNING: License expires in {days_left} days")
                                if self.on_expiry_warning:
                                    try:
                                        self.on_expiry_warning(days_left)
                                    except Exception as e:
                                        print(f"[LICENSE] Warning callback error: {e}")
                            else:
                                print(f"[LICENSE] License valid for {days_left} days")
                    
                    except Exception as e:
                        print(f"[LICENSE] Failed to check expiry date: {e}")
            
            except Exception as e:
                print(f"[LICENSE] Validation error: {e}")
                self.is_valid = False
    
    def force_validate(self):
        """Force immediate validation (can be called from UI)."""
        print("[LICENSE] Force validation requested")
        self._validate()
        return self.is_valid
    
    def get_status(self):
        """Get current license status.
        
        Returns:
            dict: {
                'is_valid': bool,
                'last_check': datetime,
                'days_until_expiry': int or None
            }
        """
        with self._lock:
            return {
                'is_valid': self.is_valid,
                'last_check': self.last_validation_time,
                'days_until_expiry': self.days_until_expiry
            }


# Global validator instance (initialized in main.py)
_license_validator = None

def get_license_validator():
    """Get global license validator instance."""
    return _license_validator

def start_license_validation(on_invalid_callback=None, on_expiry_warning_callback=None):
    """Start global license validation thread.
    
    Args:
        on_invalid_callback: Function(reason) called when license becomes invalid
        on_expiry_warning_callback: Function(days_left) called when license expiring soon
    
    Returns:
        LicenseValidator: The global validator instance
    """
    global _license_validator
    
    if _license_validator is None:
        _license_validator = LicenseValidator(
            on_invalid_callback=on_invalid_callback,
            on_expiry_warning_callback=on_expiry_warning_callback
        )
    
    _license_validator.start()
    return _license_validator

def stop_license_validation():
    """Stop global license validation thread."""
    global _license_validator
    if _license_validator:
        _license_validator.stop()
