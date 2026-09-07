import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading config.json: {e}")
    return {}

CONFIG = load_config()
HABITICA_USER_ID = CONFIG.get("HABITICA_USER_ID", "1a9bae15-8e7f-40f4-a4b7-d841a89e90ca")
HABITICA_API_TOKEN = CONFIG.get("HABITICA_API_TOKEN", "c90748f7-cc6f-4c1e-8728-5c31c7acd87d")
THEME = CONFIG.get("THEME", {})
