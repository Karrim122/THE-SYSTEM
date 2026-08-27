"""
Core leveling logic for the Hunter Status Window.

Each stat starts at level 1. Every completion or reduction of a task tagged with
that stat contributes or deducts a fractional "chunk" of progress toward levels:
    - a HARD   task takes  5 completions to grant 1 full level (1/5  = 0.20)
    - a MEDIUM task takes 10 completions to grant 1 full level (1/10 = 0.10)
    - an EASY  task takes 20 completions to grant 1 full level (1/20 = 0.05)
    - a TRIVIAL task takes 30 completions to grant 1 full level (1/30 = ~0.033)

The overall Player Level is the weighted average of the five stat levels,
rounded to the nearest whole number.
"""

STATS = ["Discipline", "Deep Focus", "Activity", "Intelligence", "Hacking"]

# Order matches STATS above: Discipline=5, Deep Focus=4, Activity=1, Intelligence=3, Hacking=5
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

# Habitica stores difficulty as a numeric "priority" field on the task.
PRIORITY_TO_DIFFICULTY = {
    0.1: "trivial",
    1: "easy",
    1.5: "medium",
    2: "hard",
}


def priority_to_difficulty(priority):
    """Converts Habitica numeric priority float to a named difficulty string."""
    return PRIORITY_TO_DIFFICULTY.get(priority, "easy")


def new_stat_block():
    """Initializes a fresh set of stats starting at Level 1, 0.0 progress."""
    return {stat: {"level": 1, "progress": 0.0} for stat in STATS}


def apply_progress(stats_block, stat_name, increment, direction="up"):
    """Adds or subtracts progress for a stat and handles level-ups or level-downs.

    Parameters:
        stats_block (dict): The player's stats dictionary.
        stat_name (str): Name of the stat to modify (must be in STATS).
        increment (float): The base progress amount (e.g. 0.05 for easy).
        direction (str): 'up' for positive habit/task, 'down' for negative habit.

    Returns:
        int: Net change in levels (+N for level ups, -N for level downs, 0 for none).
    """
    if stat_name not in stats_block:
        return 0

    entry = stats_block[stat_name]
    level_change = 0

    # Normalize direction string
    direction = str(direction).strip().lower()

    if direction == "down":
        entry["progress"] = round(entry["progress"] - increment, 6)

        # Handle level demotions
        while entry["progress"] < 0.0:
            if entry["level"] > 1:
                entry["level"] -= 1
                entry["progress"] = round(entry["progress"] + 1.0, 6)
                level_change -= 1
            else:
                # Clamp at Level 1 with 0.0 progress minimum
                entry["progress"] = 0.0
                break
    else:
        entry["progress"] = round(entry["progress"] + increment, 6)

        # Handle level promotions (triggers immediately at >= 1.0)
        while entry["progress"] >= 1.0:
            entry["progress"] = round(entry["progress"] - 1.0, 6)
            entry["level"] += 1
            level_change += 1

    return level_change


def process_habitica_event(stats_block, task_data, tag_id_to_name, direction="up"):
    """Convenience wrapper to process a Habitica task payload directly.

    Parameters:
        stats_block (dict): The player's stats block.
        task_data (dict): Habitica task dictionary (containing 'tags' and 'priority').
        tag_id_to_name (dict): Mapping of tag UUIDs to tag names.
        direction (str): Habit direction ('up' or 'down'). Defaults to task payload direction if present.

    Returns:
        tuple: (stat_name_matched, level_change_int)
    """
    tag_ids = task_data.get("tags", [])
    stat_name = match_stat_from_tags(tag_ids, tag_id_to_name)

    if not stat_name:
        return None, 0

    priority = task_data.get("priority", 1)
    difficulty = priority_to_difficulty(priority)
    increment = DIFFICULTY_INCREMENT[difficulty]

    # Use task payload'direction if provided in task_data
    event_direction = task_data.get("direction", direction)

    level_change = apply_progress(
        stats_block=stats_block,
        stat_name=stat_name,
        increment=increment,
        direction=event_direction,
    )

    return stat_name, level_change


def overall_level(stats_block):
    """Calculates weighted average player level rounded to the nearest integer."""
    total_weight = sum(WEIGHTS.values())
    weighted_sum = sum(stats_block[s]["level"] * WEIGHTS[s] for s in STATS)
    return round(weighted_sum / total_weight)


def normalize_tag_name(name):
    """Normalizes string for case and whitespace insensitive matching."""
    return " ".join(name.strip().lower().split())


def match_stat_from_tags(tag_ids, tag_id_to_name):
    """Given a task's list of tag ids, find the first one that matches
    one of the 5 stat names (case-insensitive, whitespace-insensitive)."""
    normalized_stats = {normalize_tag_name(s): s for s in STATS}
    for tid in tag_ids or []:
        name = tag_id_to_name.get(tid)
        if not name:
            continue
        norm = normalize_tag_name(name)
        if norm in normalized_stats:
            return normalized_stats[norm]
    return None