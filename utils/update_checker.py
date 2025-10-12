# 📁 File: utils/update_checker.py

import requests
import json
import os
from tkinter import messagebox
# from config import CURRENT_VERSION, UPDATE_URL
import webbrowser
import urllib.request


# update_status = {
#     "latest_version": "1.0.0",
#     "changelog": "",
#     "download_url": ""
# }

CURRENT_VERSION = "1.0.0"


def up_to():
    try:
        url = "https://raw.githubusercontent.com/AnindhaxNill/VWAR-release/master/update_info.json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            # print(data)
        
        latest = data["latest_version"]
        
        # update_status["changelog"]
        # update_status["download_url"]
        
        
        
        if latest != CURRENT_VERSION:
            return 1
    except Exception as e:
            print(f"[ERROR] Failed to check for updates: {e}")

def check_for_updates():
    try:
        url = "https://raw.githubusercontent.com/AnindhaxNill/VWAR-release/master/update_info.json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

        # print(data)
        latest = data["latest_version"]
        download_url = data["download_url"]
        notes = data.get("changelog", "")
        
        # update_status["changelog"]
        # update_status["download_url"]

        
        
        if latest != CURRENT_VERSION:
            if messagebox.askyesno("Update Available",
                f"A new version {latest} is available.\n\nChangelog:\n{notes}\n\nDo you want to update now?"):
                webbrowser.open(download_url)
                
                
        print("[Active status updeate _cheacker]active checked up to date")
            
    except Exception as e:
        print(f"[ERROR] Failed to check for updates: {e}")
