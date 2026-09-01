"""
Core leveling logic for the Hunter Status Window.

Loads baseline level state from data.json and applies live API updates seamlessly.
"""

import json
import os

STATS = ["Discipline", "Deep Focus", "Activity", "Intelligence", "Hacking"]

WEIGHTS = {
    "Discipline": 5,
    "Deep Focus": 5,
    "Activity": 1,
    "Intelligence": 3,
    "Hacking": 4,
}

DIFFICULTY_INCREMENT = {
    "trivial": 1 / 30,
    "easy": 1 / 20,
    "medium": 1 / 10,
    "hard": 1 / 5,
}

PRIORITY_TO_DIFFICULTY = {
    0.1: "trivial",
    1: "easy",
    1.5: "medium",
    2: "hard",
}


def priority_to_difficulty(priority):
    return PRIORITY_TO_DIFFICULTY.get(priority, "easy")


def new_stat_block():
    return {stat: {"level": 1, "progress": 0.0} for stat in STATS}


def load_base_stats():
    """Loads recorded baseline stats from data.json."""
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r") as f:
                data = json.load(f)
                if "stats" in data:
                    return data["stats"]
        except Exception:
            pass
    return new_stat_block()


def overall_level(stats_block):
    total_weight = sum(WEIGHTS.values())
    weighted_sum = sum(stats_block[s]["level"] * WEIGHTS[s] for s in STATS)
    return round(weighted_sum / total_weight)


def calculate_stats(raw_data):
    """
    Returns baseline stats stored in data.json.
    If raw_data contains processed stats from desktop local state, returns those directly.
    """
    # 1. Check if raw_data already contains a computed stats block
    if isinstance(raw_data, dict) and "stats" in raw_data and isinstance(raw_data["stats"], dict):
        return raw_data["stats"]

    # 2. Otherwise load saved snapshot from data.json
    return load_base_stats()
