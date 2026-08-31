import json
import os

import stats_engine

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "stats": stats_engine.new_stat_block(),
            "tasks": {},  # task_id -> {"counterUp": int, "lastCreditedDate": "YYYY-MM-DD"}
            "last_synced": None,
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Backfill any keys that might be missing
    data.setdefault("stats", stats_engine.new_stat_block())
    data.setdefault("tasks", {})
    data.setdefault("last_synced", None)
    for stat in stats_engine.STATS:
        data["stats"].setdefault(stat, {"level": 1, "progress": 0.0})
    return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
