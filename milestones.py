"""
Milestone / Ability definitions for the Player Window Stats system.
"""

MILESTONES = {
    "Discipline": [
        (10, "C RANK", "I'm able to hold myself to something in writing, not just in words — most people just talk about it."),
        (20, "B RANK", "I'm able to outlast people who quit before I do."),
        (35, "A RANK", "I'm able to keep a promise to myself even when no one's watching, where most people only perform for an audience."),
        (50, "S RANK", "I'm able to commit to something irreversible (a deadline, a paid course, a signed-up event) without the fear of flaking that stops most people."),
        (65, "SS RANK", "I'm able to hold someone else accountable to a commitment, because I've proven I can hold my own — something most people can't do for themselves, let alone others."),
        (80, "SSS RANK", "I'm able to cut out my go-to escape habit (doom-scrolling, snacking, avoidance) entirely, with no external structure needed — no app, no accountability partner, just me."),
        (100, "ANOTHER LEVEL", "I'm on another level in discipline — it's just who I am, not something I practice."),
    ],
    "Deep Focus": [
        (10, "C RANK", "I'm able to sit through a 25-minute focus block, phone in another room, with zero urge to check it, while most people can't last 5 minutes without reaching for theirs."),
        (20, "B RANK", "I'm able to spend 90 minutes on a genuinely hard book or course, undistracted, longer than most people manage in a full day."),
        (35, "A RANK", "I'm able to hold a 3-hour deep work session on a complex project without losing the thread, something most people fragment across a dozen tabs."),
        (50, "S RANK", "I'm able to spend a full day completely offline for thinking, planning, or learning, where most people can't put the phone down for an hour."),
        (65, "SS RANK", "I'm able to run a multi-day focus sprint (hackathon-style) without burning out, where most people tap out after one long day."),
        (80, "SSS RANK", "I'm able to drop into deep focus on command, on demand, for expert-level problems, while most people need the perfect mood and zero distractions just to start."),
        (100, "ANOTHER LEVEL", "I'm on another level in focus — flow state is available at will, almost instantly, whenever the work demands it."),
    ],
    "Activity": [
        (10, "C RANK", "I'm able to say I move my body every day — and I've got the gear to match that identity, unlike most people who buy it and let it collect dust."),
        (20, "B RANK", "I'm able to start a structured program (gym plan, running plan) and trust myself to stick with it, where most people quit by week two."),
        (35, "A RANK ", "I'm able to hit a real physical milestone — first 5k, a strength PR — earned through reps most people never put in."),
        (50, "S RANK", "I'm able to sign up for an actual event (race, hike, competition) and trust my base fitness to carry me, where most people need months of dread first."),
        (65, "SS RANK", "I'm able to hit an advanced feat (10k, a serious lift, whatever's next) that used to feel out of reach — and still feels out of reach for most people."),
        (80, "SSS RANK", "I'm able to coach someone else on fitness or nutrition, because I've lived what most people only read about."),
        (100, "ANOTHER LEVEL", "I'm on another level in fitness — my body and energy are just a baseline now, not something I have to manage."),
    ],
    "Intelligence": [
        (10, "C RANK", "I'm able to say I finished a real book, or played real rated chess games, start to finish, where most people quit halfway."),
        (20, "B RANK", "I'm able to take on denser material — technical nonfiction, a real chess ladder or club — past where most people stop."),
        (35, "A RANK", "I'm able to produce something from what I learned — an essay, notes, a write-up worth sharing — instead of just consuming like most people do."),
        (50, "S RANK", "I'm able to enter a real competition (tournament, quiz, test) and see how I hold up under pressure, where most people avoid ever being tested."),
        (65, "SS RANK", "I'm able to explain a complex idea clearly enough that someone else actually gets it, a skill most people who \"know\" the material don't have."),
        (80, "SSS RANK", "I'm able to go deep enough in a domain that people start asking me for answers instead of the other way around."),
        (100, "ANOTHER LEVEL", "I'm on another level in intelligence — thinking clearly under any condition is just identity now, not a skill I'm building."),
    ],
    "Hacking": [
        (10, "C RANK", "I'm able to hold networking fundamentals down cold (CCNA-level: TCP/IP, routing, subnetting) and I've earned a proper home lab for it, past where most beginners stall out."),
        (20, "B RANK", "I'm able to move from networks into the OS itself — Linux and Windows internals — commanding it instead of just clicking around like most people do."),
        (35, "A RANK", "I'm able to capture my first independent CTF flag, or finish a real cert, solo — proof the fundamentals stuck, where most people never get past tutorials."),
        (50, "S RANK", "I'm able to apply for an internship or junior role, or sit a real certification exam, while most people are still 'getting ready to start.'"),
        (65, "SS RANK", "I'm able to contribute to a real bug bounty or open-source security project, giving back where most people only take."),
        (80, "SSS RANK", "I'm able to perform in an actual cybersecurity role, or pass an advanced cert (OSCP-tier), the tier most people in the field never reach."),
        (100, "ANOTHER LEVEL", "I'm on another level in cybersecurity — this is my career now, not my hobby."),
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
    elif level >= 5;
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
