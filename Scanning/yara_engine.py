import os
import yara
import requests

from config import YARA_FOLDER
from utils.logger import log_message


def fetch_and_generate_yara_rules(log_func=print):
    """Fetch categorized YARA rules from remote and store locally."""
    try:
        url = "https://library.bitss.one/windows.php"
        response = requests.get(url)
        response.raise_for_status()

        json_data = response.json()
        if not json_data:
            log_func("[WARNING] No YARA rules found.")
            return

        for rule in json_data:
            category = rule.get("categoryname", "uncategorized")
            rule_name = rule.get("rulename", "unknown_rule")
            rule_content = rule.get("conditions", [{}])[0].get("string", "")

            category_dir = os.path.join(YARA_FOLDER, category)
            os.makedirs(category_dir, exist_ok=True)

            file_path = os.path.join(category_dir, f"{rule_name}.yar")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(rule_content)

        log_func("[INFO] YARA rules categorized and saved successfully.")

    except Exception as e:
        log_func(f"[ERROR] Failed to fetch YARA rules: {e}")


def compile_yara_rules(rule_folder=YARA_FOLDER, log_func=print):
    """Compile all valid .yar rule files and return a compiled ruleset."""
    valid_rule_files = {}
    failed_files = []

    try:
        for root, _, files in os.walk(rule_folder):
            for file in files:
                if file.endswith(".yar"):
                    full_path = os.path.join(root, file)
                    try:
                        yara.compile(filepath=full_path)
                        valid_rule_files[file] = full_path
                    except Exception as e:
                        failed_files.append(f"{file}: {e}")

        if not valid_rule_files:
            log_func("[ERROR] No valid YARA rules found.")
            return None

        rules = yara.compile(filepaths=valid_rule_files)
        log_func(f"[INFO] Compiled {len(valid_rule_files)} YARA rule files.")
        return rules

    except Exception as e:
        log_func(f"[ERROR] Failed to compile YARA rules: {e}")
        return None
