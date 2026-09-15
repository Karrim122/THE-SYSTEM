"""
Milestone / Ability definitions for the Player Window Stats system.
"""

MILESTONES = {
    "Discipline": [
        (5, "D RANK", "you started to know what is Discipline"),
        (10, "C RANK", "You mastered the skill of [just start it], and now you started to be disciplined for the first time"),
        (20, "B RANK", "you mastered [wake up], [close your eyes] and now your sleep schedule is fixed also [no distraction] no more distracted, and self controled"),
        (35, "A RANK", "you now make a [Day plan], and commit to it, so everything is planned by time and can handle everything in life"),
        (50, "S RANK", "you apply the [session target (ALA)], and make a target for each session or task to achieve, so that you make the highest results ever, and now you start to become elite"),
        (65, "SS RANK", "you mastered everything, and can [add habits] and commit to them easily"),
        (80, "SSS RANK", "congratualations!, you changed and became a disciplined, nothing in life is hard now"),
        (100, "ANOTHER LEVEL", "You are on ANOTHER LEVEL! in discipline — it's just who you are, not something you practice."),
    ],
    "Deep Focus": [
        (5, "D RANK", "You started to know what is Deep focus"),
        (10, "C RANK", "you mastered the skill of [start a timer],  [meditation], [scrolling limit], brain rotting started to vanish"),
        (20, "B RANK", "you started to mater [pomodoro session], and focus time increased, no more brain rotting"),
        (35, "A RANK", "you mastered [reading], and became a reader, now your focus and deep understanding increased"),
        (50, "S RANK", "you mastered focus and [consciousness regain], whenever getting distracted, you regain focus and thinking quickly"),
        (65, "SS RANK", "you mastered the habits [meditation] more and more, and[pomodoro sessions] increased"),
        (80, "SSS RANK", "congratulations!, you changed and became a deep thinker, you easily think well and deeply in anything in life now"),
        (100, "ANOTHER LEVEL", "You are on ANOTHER LEVEL! in deep focus — it's just who you are, not something you practice."),
    ],
    "Activity": [
        (5, "D RANK", "You started to know what is Activity"),
        (10, "C RANK", "you mastered [activity], and became active in daily life"),
        (20, "B RANK", "you started exercising [exercise], and started to become stronger"),
        (35, "A RANK ", "you take care of [Nutrition], and eat less sugar and junk, just healthy nutrition"),
        (50, "S RANK", "you mastered physical increasing [exercise], and body changed"),
        (65, "SS RANK", "you now mastered every habit and started to see high results"),
        (80, "SSS RANK", "congratulations!, you changed and became strong and healthy"),
        (100, "ANOTHER LEVEL", "You are on ANOTHER LEVEL! in Physical — it's just who you are, not something you practice."),
    ],
    "Intelligence": [
        (5, "D RANK", "You started to know what is Intelligence"),
        (10, "C RANK", "you improved at [chess] elo increased, and improved your [language learning]"),
        (20, "B RANK", "you improved [puzzles and calculation], and your mental abilities increased"),
        (35, "A RANK", "you stared to use[ALA consciouss thinkin] in almost everhting in life"),
        (50, "S RANK", "you mastered all the mental skills and stareted to see results in life learning and studying"),
        (65, "SS RANK", "you mastered [chess], learned a [language], and mastered all mental abilities, and became a fast learner"),
        (80, "SSS RANK", "congratulations!, you changed and became a genius"),
        (100, "ANOTHER LEVEL", "You are on ANOTHER LEVEL! in discipline — it's just who you are, not something you practice."),
    ],
    "Hacking": [
        (5, "D RANK", "You started to know what is career"),
        (10, "C RANK", "you gained some knowledge in [career], a first step in cybersecurity"),
        (20, "B RANK", "you are able to move from networks into the OS itself — Linux and Windows internals — commanding it instead of just clicking around like most people do."),
        (35, "A RANK", "you are able to capture my first independent CTF flag, or finish a real cert, solo — proof the fundamentals stuck, where most people never get past tutorials."),
        (50, "S RANK", "you are able to apply for an internship or junior role, or sit a real certification exam, while most people are still 'getting ready to start.'"),
        (65, "SS RANK", "you are able to contribute to a real bug bounty or open-source security project, giving back where most people only take."),
        (80, "SSS RANK", "you are able to perform in an actual cybersecurity role, or pass an advanced cert (OSCP-tier), the tier most people in the field never reach."),
        (100, "ANOTHER LEVEL", "You are on ANOTHER LEVEL! in cybersecurity — it's just who you are, not something you practice."),
    ],
}


def milestones_for(stat_name):
    """Returns the ordered list of (level, title, text) milestones for a stat."""
    return MILESTONES.get(stat_name, [])


def next_milestone(stat_name, current_level):
    """Returns the (level, title, text) tuple of the next locked milestone above
    current_level, or None if every milestone has been unlocked."""
    for lvl, title, text in milestones_for(stat_name):
        if current_level < lvl:
            return (lvl, title, text)
    return None


def get_rank_title(level):
    """Returns rank title based on level threshold."""
    if level >= 100:
        return "ANOTHER LEVEL"
    elif level >= 80:
        return "SSS RANK"
    elif level >= 65:
        return "SS RANK"
    elif level >= 50:
        return "S RANK"
    elif level >= 35:
        return "A RANK"
    elif level >= 20:
        return "B RANK"
    elif level >= 10:
        return "C RANK"
    elif level >= 5:
        return "D RANK"
    return "E RANK"


def get_stat_rank(stat_name, level):
    """Returns the current rank title for a given stat level."""
    active_rank = "E RANK"
    for lvl, title, _ in milestones_for(stat_name):
        if level >= lvl:
            active_rank = title.strip()
        else:
            break
    return active_rank
