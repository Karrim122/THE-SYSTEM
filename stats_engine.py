"""
Core leveling logic for the Hunter Status Window.

Calculates stats dynamically from Habitica API data.
Every run starts from base level 1 to prevent double-counting saved files.
"""

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


def overall_level(stats_block):
    total_weight = sum(WEIGHTS.values())
    weighted_sum = sum(stats_block[s]["level"] * WEIGHTS[s] for s in STATS)
    return round(weighted_sum / total_weight)


def normalize_tag_name(name):
    return " ".join(name.strip().lower().split())


def match_stat_from_tags(tag_ids, tag_id_to_name):
    normalized_stats = {normalize_tag_name(s): s for s in STATS}
    for tid in tag_ids or []:
        name = tag_id_to_name.get(tid)
        if not name:
            continue
        norm = normalize_tag_name(name)
        if norm in normalized_stats:
            return normalized_stats[norm]
    return None


def calculate_stats(raw_data):
    """Calculates full stat block dynamically starting from fresh Lvl 1 base."""
    # Always start fresh at Level 1
    stats_block = new_stat_block()

    tags = raw_data.get("tags", [])
    tag_id_to_name = {t["id"]: t["name"] for t in tags}

    # Process Habits (counterUp / counterDown)
    for task in raw_data.get("habits", []):
        stat = match_stat_from_tags(task.get("tags"), tag_id_to_name)
        if not stat:
            continue
        difficulty = priority_to_difficulty(task.get("priority", 1))

        counter_up = task.get("counterUp", 0) or 0
        counter_down = task.get("counterDown", 0) or 0

        if counter_up > 0:
            apply_progress(stats_block, stat, DIFFICULTY_INCREMENT[difficulty] * counter_up, "up")
        if counter_down > 0:
            apply_progress(stats_block, stat, DIFFICULTY_INCREMENT[difficulty] * counter_down, "down")

    # Process Completed Dailies
    for task in raw_data.get("dailies", []):
        if task.get("completed"):
            stat = match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if stat:
                difficulty = priority_to_difficulty(task.get("priority", 1))
                apply_progress(stats_block, stat, DIFFICULTY_INCREMENT[difficulty], "up")

    # Process Completed To-Dos
    for task in raw_data.get("todos", []):
        if task.get("completed"):
            stat = match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if stat:
                difficulty = priority_to_difficulty(task.get("priority", 1))
                apply_progress(stats_block, stat, DIFFICULTY_INCREMENT[difficulty], "up")

    return stats_block
