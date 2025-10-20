# import os
# import json
# import requests
# import tkinter as tk
# from tkinter import messagebox
# from activation.hwid import get_processor_info, get_motherboard_info
# from config import ACTIVATION_FILE, API_GET, API_POST
# from app_main import VWARScannerGUI
# from datetime import datetime
# from config import ICON_PATH
# from cryptography.fernet import Fernet
# import base64, hashlib

# def generate_fernet_key_from_string(secret_string):
#     sha256 = hashlib.sha256(secret_string.encode()).digest()
#     return base64.urlsafe_b64encode(sha256)

# SECRET_KEY = generate_fernet_key_from_string("VWAR@BIFIN")
# fernet = Fernet(SECRET_KEY)

# # def show_activation_window():
# #     """Launch the activation GUI window."""
# #     root = tk.Tk()
# #     root.title("Activate VWAR Scanner")
# #     root.geometry("400x250")
# #     root.configure(bg="#1e1e1e")
# #     root.resizable(False, False)

# #     tk.Label(root, text="Enter Activation Key", bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=(30, 5))

# #     key_entry = tk.Entry(root, font=("Arial", 12), width=30, justify="center")
# #     key_entry.pack(pady=10)

# #     tk.Button(
# #         root, text="Activate", bg="#28a745", fg="white", font=("Arial", 12),
# #         command=lambda: activate(key_entry.get(), root)
# #     ).pack(pady=20)

# #     root.mainloop()



# def show_activation_window(reason=None):
#     """Launch the activation GUI window and display the reason if provided."""
#     root = tk.Tk()
#     root.title("Activate VWAR Scanner")
#     root.geometry("400x250")
#     root.configure(bg="#1e1e1e")
#     # root.iconbitmap(ICON_PATH)
#     root.resizable(False, False)

#     # Optional reason label
#     if reason:
#         tk.Label(root, text=reason, fg="red", bg="#1e1e1e", font=("Arial", 11, "bold")).pack(pady=(20, 5))

#     tk.Label(root, text="Enter Activation Key", bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=(10 if reason else 30, 5))

#     key_entry = tk.Entry(root, font=("Arial", 12), width=30, justify="center")
#     key_entry.pack(pady=10)

#     tk.Button(
#         root, text="Activate", bg="#28a745", fg="white", font=("Arial", 12),
#         command=lambda: activate(key_entry.get(), root)
#     ).pack(pady=20)

#     root.mainloop()


# def activate(license_key, root):
#     """Handles the activation process: check key, match hardware, and activate."""
#     if not license_key:
#         messagebox.showwarning("Empty Field", "Please enter a license key.")
#         return
    
#     try:
#         response = requests.get(API_GET)
#         records = response.json().get("data", [])
        
#     except Exception as e:
#         messagebox.showerror("API Error", f"Failed to connect to activation server {e}")
#         return

#     current_cpu = get_processor_info()
#     current_mobo = get_motherboard_info()

#     if not current_cpu or not current_mobo:
#         messagebox.showerror("Hardware Error", "Failed to retrieve hardware information.")
#         return



#     found = None
#     for record in records:
#         if record.get("password") == license_key:
#             found = record
#             break

#     if not found:
#         messagebox.showerror("Invalid Key", "The license key entered is not valid.")
#         return

#     server_cpu = found.get("processor_id")
#     server_mobo = found.get("motherboard_id")

#     # Already activated on this PC
#     if current_cpu == server_cpu and current_mobo == server_mobo:
        
#                 # Step: Check expiration before allowing access
#         valid_till = found.get("valid_till")
#         try:
#             expiry = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
#             if datetime.now() > expiry:
#                 messagebox.showerror("Expired Key", "This license key has expired.")
#                 return
#         except Exception as e:
#             messagebox.showerror("Invalid Date", f"Failed to validate license expiry:\n{e}")
#             return
        
        
        
#         _store_activation(found, current_cpu, current_mobo)
#         messagebox.showinfo("Re-Activation", "VWAR Scanner is already activated on this system.")
#         _launch_app(root)
#         return

#     # Key is in use on another system
#     elif server_cpu and server_mobo:
#         # print(f"{license_key} empty ")
#     # if (server_cpu is None or server_cpu == "") and (server_mobo is None or server_mobo == ""):
#         messagebox.showerror("Key In Use", "This key is already activated on another system.")
#         return

#     # Key is valid but not yet activated → POST to bind
#     try:
#         bind_payload = {
#             "id": found["id"],
#             "processor_id": current_cpu,
#             "motherboard_id": current_mobo
#         }
        
#         bind_response = requests.post(API_POST, json=bind_payload)
#         a= bind_response.json()
#         print(a['status'])
        

#         if a['status'] == "success":
#             _store_activation(found, current_cpu, current_mobo)
#             messagebox.showinfo("Activated", "Activation successful!")
#             _launch_app(root)
#             return
#         else:
#             messagebox.showerror("Activation Failed", "Server rejected activation attempt.")
#             return

#     except Exception as e:
#         messagebox.showerror("POST Error", f"Failed to bind activation:\n{e}")
#         return


# def _store_activation(record, cpu, mobo):
#     """Save activation info locally to activation.json."""
#     try:
#         os.makedirs(os.path.dirname(ACTIVATION_FILE), exist_ok=True)
#         data = {
#             "id": record["id"],
#             "username": record["username"],
#             "password": record["password"],
#             "processor_id": cpu,
#             "motherboard_id": mobo,
#             "valid_till": record["valid_till"],
#             "created_at": record.get("created_at", "")
#         }
#         json_str = json.dumps(data).encode("utf-8")
#         encrypted = fernet.encrypt(json_str)
#         with open(ACTIVATION_FILE, "wb") as f:
#             f.write(encrypted)
#         # with open(ACTIVATION_FILE, "w", encoding="utf-8") as f:
#         #     json.dump(data, f, indent=4)
        
#         print("[INFO] Activation info stored.")
#     except Exception as e:
#         print(f"[ERROR] Failed to store activation: {e}")


# def _launch_app(root):
#     """Close activation window and launch the main VWAR app."""
#     root.destroy()
#     app_root = tk.Tk()
#     VWARScannerGUI(app_root)
#     app_root.mainloop()




import os
import json
import requests
import tkinter as tk
from tkinter import messagebox
from activation.hwid import get_processor_info, get_motherboard_info
from config import ACTIVATION_FILE, API_GET, API_POST
from app_main import VWARScannerGUI
from datetime import datetime
from config import ICON_PATH
from cryptography.fernet import Fernet
import base64, hashlib
# from liences_utils import _store_activation  # ✅ now imported from liences_utils
from activation.license_utils import _store_activation  # ✅ now imported from license_utils


def generate_fernet_key_from_string(secret_string):
    sha256 = hashlib.sha256(secret_string.encode()).digest()
    return base64.urlsafe_b64encode(sha256)

SECRET_KEY = generate_fernet_key_from_string("VWAR@BIFIN")
fernet = Fernet(SECRET_KEY)


def show_activation_window(reason=None):
    """Launch the activation GUI window and display the reason if provided."""
    root = tk.Tk()
    root.title("Activate VWAR Scanner")
    root.geometry("400x250")
    root.configure(bg="#1e1e1e")
    # root.iconbitmap(ICON_PATH)
    root.resizable(False, False)

    # Optional reason label
    if reason:
        tk.Label(root, text=reason, fg="red", bg="#1e1e1e", font=("Arial", 11, "bold")).pack(pady=(20, 5))

    tk.Label(root, text="Enter Activation Key", bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=(10 if reason else 30, 5))

    key_entry = tk.Entry(root, font=("Arial", 12), width=30, justify="center")
    key_entry.pack(pady=10)

    tk.Button(
        root, text="Activate", bg="#28a745", fg="white", font=("Arial", 12),
        command=lambda: activate(key_entry.get(), root)
    ).pack(pady=20)

    root.mainloop()


def activate(license_key, root):
    """Handles the activation process: check key, match hardware, and activate."""
    if not license_key:
        messagebox.showwarning("Empty Field", "Please enter a license key.")
        return
    
    try:
        response = requests.get(API_GET)
        records = response.json().get("data", [])
        
    except Exception as e:
        messagebox.showerror("API Error", f"Failed to connect to activation server {e}")
        return

    current_cpu = get_processor_info()
    current_mobo = get_motherboard_info()

    if not current_cpu or not current_mobo:
        messagebox.showerror("Hardware Error", "Failed to retrieve hardware information.")
        return

    found = None
    for record in records:
        if record.get("password") == license_key:
            found = record
            break

    if not found:
        messagebox.showerror("Invalid Key", "The license key entered is not valid.")
        return

    server_cpu = found.get("processor_id")
    server_mobo = found.get("motherboard_id")

    # Already activated on this PC
    if current_cpu == server_cpu and current_mobo == server_mobo:
        # Step: Check expiration before allowing access
        valid_till = found.get("valid_till")
        try:
            expiry = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expiry:
                messagebox.showerror("Expired Key", "This license key has expired. Please renew your license. \n contact us on : \n https://bitss.one/contact")
                return
        except Exception as e:
            messagebox.showerror("Invalid Date", f"Failed to validate license expiry:\n{e}")
            return

        _store_activation(found, current_cpu, current_mobo)
        messagebox.showinfo("Re-Activation", "VWAR Scanner is already activated on this system.")
        _launch_app(root)
        return

    # Key is in use on another system
    elif server_cpu and server_mobo:
        messagebox.showerror("Key In Use", "This key is already activated on another system.")
        return

    # Key is valid but not yet activated → POST to bind
    try:
        bind_payload = {
            "id": found["id"],
            "processor_id": current_cpu,
            "motherboard_id": current_mobo
        }
        
        bind_response = requests.post(API_POST, json=bind_payload)
        a = bind_response.json()
        print(a['status'])
        
        if a['status'] == "success":
            _store_activation(found, current_cpu, current_mobo)
            messagebox.showinfo("Activated", "Activation successful!")
            _launch_app(root)
            return
        else:
            messagebox.showerror("Activation Failed", "Server rejected activation attempt.")
            return

    except Exception as e:
        messagebox.showerror("POST Error", f"Failed to bind activation:\n{e}")
        return


def _launch_app(root):
    """Close activation window and launch the main VWAR app."""
    root.destroy()
    app_root = tk.Tk()
    VWARScannerGUI(app_root)
    app_root.mainloop()
