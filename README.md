# Hunter Status Window

A desktop stat-tracker (tkinter GUI) that syncs with your Habitica account and
levels up 5 stats based on your Habits and Dailies:

- **Discipline** (weight 5)
- **Deep Focus** (weight 4)
- **Activity** (weight 1)
- **Intelligence** (weight 3)
- **Hacking** (weight 5)

All 5 stats start at **Level 1**. Your **Overall Player Level** is the
weighted average of the 5 stats (weights above), rounded to the nearest
whole number.

## 1. Install

Requires Python 3.9+.

```bash
cd hunter_status_app
pip install -r requirements.txt
```

## 2. One-time setup in Habitica

This app doesn't guess which stat a task belongs to — you tell it, using
Habitica's built-in **tags**. In the Habitica web/mobile app:

1. Go to a Habit or Daily's edit screen.
2. Create 5 tags named **exactly**: `Discipline`, `Deep Focus`, `Activity`,
   `Intelligence`, `Hacking` (matching is not case-sensitive and ignores
   extra spaces, but the words must match).
3. Attach the relevant tag to each Habit/Daily. E.g. tag "Do 50 pushups"
   with `Activity`, tag "PortSwigger lab" with `Hacking`, tag "Sleep by
   11pm" with `Discipline`, etc.
4. Set each task's difficulty (Trivial / Easy / Medium / Hard) in Habitica
   as normal — this controls how fast it levels the stat (see below).

Untagged tasks, or tasks tagged with something other than these 5 names,
are simply ignored by the sync.

## 3. Run it

```bash
python main.py
```

The first time you run it, it will ask for your Habitica **User ID** and
**API Token** (found in the Habitica web app under Settings > API), unless
`config.json` already has them filled in (it currently does, prefilled from
what you gave me — see the security note below).

Click **Sync with Habitica** any time to pull your latest task completions
and apply stat progress.

## How leveling works

Every time you complete a tagged task, it contributes partial progress
toward that stat's next level, based on difficulty:

| Difficulty | Completions needed for +1 level |
|---|---|
| Hard | 5 |
| Medium | 10 |
| Easy | 20 |
| Trivial | 20 (same as Easy — not specified, so treated this way) |

- **Habits**: the app reads Habitica's own cumulative "counterUp" value for
  each habit, so it correctly counts completions that happened even before
  you had this app open — every sync just adds whatever's new since last
  time.
- **Dailies**: the app credits a completion once per calendar day, the
  first time it sees the Daily marked "completed" (matching how Dailies
  actually work in Habitica — one checkbox per day).

Progress and levels are saved locally in `data.json` so nothing resets
between runs.

## Files

- `main.py` — the GUI app (run this)
- `habitica_api.py` — talks to the Habitica API
- `stats_engine.py` — leveling math (edit `WEIGHTS` or `DIFFICULTY_INCREMENT`
  here if you want to rebalance things later)
- `data_store.py` — loads/saves `data.json` (your saved progress)
- `config.py` / `config.json` — your Habitica credentials
- `requirements.txt` — the one dependency (`requests`)

## ⚠️ Security note

Your Habitica User ID and API Token are saved in plain text in
`config.json` so the app can use them. Treat this file like a password:

- Don't upload this folder anywhere public (e.g. a public GitHub repo).
- Because you pasted your API Token directly in our chat, it's now stored
  in your Anthropic conversation history. It's low-risk (Habitica tokens
  can't touch billing/payment info), but if you want to be safe, you can
  regenerate it any time from Habitica's Settings > API page, then update
  `config.json` with the new value — no other changes needed.
