"""
Milestone / Ability definitions for the Player Window Stats system.

Each stat has a fixed set of milestone levels. When the player's level in a
stat reaches or passes a milestone level, that milestone becomes "unlocked"
and represents a real-life ability or privilege the player has earned.

This data is presented on the Abilities page, which shows every milestone
for every stat, with unlocked ones highlighted and locked ones dimmed.
"""

# List of (level, rank_title, ability_text) tuples per stat, in ascending order.
MILESTONES = {
    "Discipline": [
        (10, "Novice",
         "Wake up at the time I set, without negotiating with myself, for a full week straight."),
        (20, "Apprentice",
         "Take on a hard voluntary challenge (cold showers, fasting, a no-sugar week) and finish it."),
        (35, "Adept",
         "Announce a goal publicly and know I won't back out of it."),
        (50, "Expert",
         "Commit to something irreversible (a deadline, a paid course, a signed-up event) without fear of flaking."),
        (65, "Master",
         "Hold someone else accountable to a commitment, because I've proven I can hold my own."),
        (80, "Grandmaster",
         "Cut out my go-to escape habit (doom-scrolling, snacking, avoidance) entirely, with no external structure needed."),
        (100, "Legend — Iron Will",
         "Trust my own word completely — discipline is just who I am, not something I practice."),
    ],
    "Deep Focus": [
        (10, "Novice",
         "Sit through a 25-minute focus block, phone in another room, with zero urge to check it."),
        (20, "Apprentice",
         "Spend 90 minutes on a genuinely hard book or course, undistracted."),
        (35, "Adept",
         "Hold a 3-hour deep work session on a complex project without losing the thread."),
        (50, "Expert",
         "Spend a full day completely offline for thinking, planning, or learning."),
        (65, "Master",
         "Run a multi-day focus sprint (hackathon-style) without burning out."),
        (80, "Grandmaster",
         "Drop into deep focus on command, on demand, for expert-level problems."),
        (100, "Legend — Flow Mastery",
         "Enter flow state at will, almost instantly, whenever the work demands it."),
    ],
    "Activity": [
        (10, "Novice",
         "Say I move my body every day — and buy real gear to match that identity."),
        (20, "Apprentice",
         "Start a structured program (gym plan, running plan) trusting I'll stick to it."),
        (35, "Adept",
         "Hit a real physical milestone — first 5k, a strength PR — that I earned through reps."),
        (50, "Expert",
         "Sign up for an actual event (race, hike, competition) and trust my base fitness to carry me."),
        (65, "Master",
         "Hit an advanced feat (10k, a serious lift, whatever's next) that used to feel out of reach."),
        (80, "Grandmaster",
         "Coach someone else on fitness or nutrition, because I've lived what I'd teach."),
        (100, "Legend — Peak Condition",
         "Rely on my body and energy as a baseline, not something I have to manage."),
    ],
    "Intelligence": [
        (10, "Novice",
         "Say I finished a real book, or played real rated chess games, start to finish."),
        (20, "Apprentice",
         "Take on denser material — technical nonfiction, a real chess ladder or club."),
        (35, "Adept",
         "Produce something from what I learned — an essay, notes, a write-up worth sharing."),
        (50, "Expert",
         "Enter a real competition (tournament, quiz, test) and see how I hold up under pressure."),
        (65, "Master",
         "Explain a complex idea clearly enough that someone else actually gets it."),
        (80, "Grandmaster",
         "Go deep enough in a domain that people start asking me for answers."),
        (100, "Legend — Renaissance Mind",
         "Think clearly under any condition — it's identity, not a skill I'm building anymore."),
    ],
    "Hacking": [
        (10, "Novice",
         "Finish intro rooms (TryHackMe/PicoCTF) and earn a proper home lab setup for it."),
        (20, "Apprentice",
         "Start a real cert track (Security+, eJPT) and know I can carry it through."),
        (35, "Adept",
         "Capture my first independent CTF flag, or finish a cert, solo."),
        (50, "Expert",
         "Apply for an internship or junior role, or sit a real certification exam."),
        (65, "Master",
         "Contribute to a real bug bounty or open-source security project."),
        (80, "Grandmaster",
         "Perform in an actual cybersecurity role, or pass an advanced cert (OSCP-tier)."),
        (100, "Legend — Ghost in the Shell",
         "Call this my career, not my hobby."),
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