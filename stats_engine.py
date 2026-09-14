"""
Core leveling logic for the Hunter Status Window.
"""

STATS = ["Discipline", "Deep Focus", "Activity", "Intelligence", "Hacking"]

WEIGHTS = {
    "Discipline": 4,
    "Deep Focus": 3,
    "Activity": 1,
    "Intelligence": 2,
    "Hacking": 5,
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

def apply_progress(stats_block, stat_name, increment, direction="up"):
    if stat_name not in stats_block:
        return 0

    entry = stats_block[stat_name]
    level_change = 0
    direction = str(direction).strip().lower()

    if direction == "down":
        entry["progress"] = round(entry["progress"] - increment, 6)
        while entry["progress"] < 0.0:
            if entry["level"] > 1:
                entry["level"] -= 1
                entry["progress"] = round(entry["progress"] + 1.0, 6)
                level_change -= 1
            else:
                entry["progress"] = 0.0
                break
    else:
        entry["progress"] = round(entry["progress"] + increment, 6)
        while entry["progress"] >= 1.0:
            entry["progress"] = round(entry["progress"] - 1.0, 6)
            entry["level"] += 1
            level_change += 1

    return level_change

def is_missed_daily(task_data):
    if task_data.get("type") != "daily":
        return False
    if task_data.get("completed", True):
        return False
    is_due = task_data.get("isDue", task_data.get("isDueToday", True))
    return bool(is_due)

def process_habitica_event(stats_block, task_data, tag_id_to_name, direction="up"):
    tag_ids = task_data.get("tags", [])
    stat_names = match_stats_from_tags(tag_ids, tag_id_to_name)

    if not stat_names:
        return {}

    priority = task_data.get("priority", 1)
    difficulty = priority_to_difficulty(priority)
    increment = DIFFICULTY_INCREMENT[difficulty]

    if is_missed_daily(task_data):
        event_direction = "down"
    else:
        event_direction = task_data.get("direction", direction)

    changes = {}
    for stat_name in stat_names:
        level_change = apply_progress(
            stats_The modified `stats_engine.py` script now collects all valid tags on a task and applies the increment or decrement logic to every matched stat[cite: 1]. 

**Key Changes**
* `match_stats_from_tags` replaces `match_stat_from_tags` to return a `list` of all unique matched stats instead of stopping at the first match[cite: 1].
* `process_habitica_event` iterates over all matched stats and returns a dictionary of `{stat_name: level_change}` pairs instead of a single `(stat_name, level_change)` tuple[cite: 1].
* `process_daily_misses` is updated to unpack the new dictionary format, appending a separate tuple to the `results` list for each modified stat[cite: 1].

**Required Updates in Your External Files**
Because `process_habitica_event` now returns a dictionary of multiple stats instead of a single tuple, you will need to update the file that calls it (such as your CustomTkinter window or Streamlit dashboard backend). 
* **Old format:** `stat_name, level_change = process_habitica_event(...)`
* **New format:** `level_changes = process_habitica_event(...)` followed by a loop: `for stat_name, level_change in level_changes.items():`

**stats_engine.py**
```python
"""
Core leveling logic for the Hunter Status Window.
"""

STATS = ["Discipline", "Deep Focus", "Activity", "Intelligence", "Hacking"]

WEIGHTS = {
    "Discipline": 4,
    "Deep Focus": 3,
    "Activity": 1,
    "Intelligence": 2,
    "Hacking": 5,
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

def apply_progress(stats_block, stat_name, increment, direction="up"):
    if stat_name not in stats_block:
        return 0

    entry = stats_block[stat_name]
    level_change = 0
    direction = str(direction).strip().lower()

    if direction == "down":
        entry["progress"] = round(entry["progress"] - increment, 6)
        while entry["progress"] < 0.0:
            if entry["level"] > 1:
                entry["level"] -= 1
                entry["progress"] = round(entry["progress"] + 1.0, 6
