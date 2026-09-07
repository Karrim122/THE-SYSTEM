import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading data.json: {e}")
    return {
        "stats": {
            "Discipline": {"level": 1, "progress": 0.0},
            "Deep Focus": {"level": 1, "progress": 0.0},
            "Activity": {"level": 1, "progress": 0.0},
            "Intelligence": {"level": 1, "progress": 0.0},
            "Hacking": {"level": 1, "progress": 0.0}
        },
        "tasks": {},
        "log": [],
        "last_synced": None,
        "overall_level_offset": 0,
        "hp": 50.0,
        "max_hp": 50.0
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving data.json: {e}")

def add_log(data, message):
    today_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"[{today_str}] {message}"
    if "log" not in data:
        data["log"] = []
    data["log"].insert(0, entry)
