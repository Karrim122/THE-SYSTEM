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
    stat_name = match_stat_from_tags(tag_ids, tag_id_to_name)

    if not stat_name:
        return None, 0

    priority = task_data.get("priority", 1)
    difficulty = priority_to_difficulty(priority)
    increment = DIFFICULTY_INCREMENT[difficulty]

    if is_missed_daily(task_data):
        event_direction = "down"
    else:
        event_direction = task_data.get("direction", direction)

    level_change = apply_progress(
        stats_block=stats_block,
        stat_name=stat_name,
        increment=increment,
        direction=event_direction,
    )

    return stat_name, level_change

def process_daily_misses(stats_block, dailies, tag_id_to_name):
    results = []
    for task_data in dailies:
        if not is_missed_daily(task_data):
            continue

        stat_name, level_change = process_habitica_event(
            stats_block=stats_block,
            task_data=task_data,
            tag_id_to_name=tag_id_to_name,
        )
        if stat_name:
            results.append((task_data.get("id"), stat_name, level_change))

    return results

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
