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
from datetime import datetime
from config import ACTIVATION_FILE, API_GET
from activation.hwid import get_processor_info, get_motherboard_info
from cryptography.fernet import Fernet
import base64, hashlib

def generate_fernet_key_from_string(secret_string):
    sha256 = hashlib.sha256(secret_string.encode()).digest()
    return base64.urlsafe_b64encode(sha256)

SECRET_KEY = generate_fernet_key_from_string("VWAR@BIFIN")
fernet = Fernet(SECRET_KEY)


def _store_activation(record, cpu, mobo):
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
            "created_at": record.get("created_at", "")
        }
        json_str = json.dumps(data).encode("utf-8")
        encrypted = fernet.encrypt(json_str)
        with open(ACTIVATION_FILE, "wb") as f:
            f.write(encrypted)
        print("[INFO] Activation info stored.")
    except Exception as e:
        print(f"[ERROR] Failed to store activation: {e}")


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
                response = requests.get(API_GET, timeout=5)
                records = response.json().get("data", [])
                found = next((r for r in records if r.get("password") == data.get("password")), None)

                if found:
                    server_valid_till = found.get("valid_till")
                    if server_valid_till:
                        server_end = datetime.strptime(server_valid_till, "%Y-%m-%d %H:%M:%S")
                        if now <= server_end:
                            # ✅ Renewed on server → update local license
                            _store_activation(found, current_cpu, current_mobo)
                            return True, None

                return False, "License expired. \n This license key has expired. Please renew your license.\n contact us on : \n https://bitss.one/contact"

            except Exception as e:
                return False, f"License expired. Failed to check renewal server: {e}"

        # Still valid locally
        return True, None

    except Exception as e:
        return False, f"Failed to validate activation: {e}"
