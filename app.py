import os
import json
import streamlit as st
import habitica_api

try:
    import stats_engine
except ImportError:
    stats_engine = None

st.set_page_config(
    page_title="Hunter Status Window",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

STATS = ["Discipline", "Deep Focus", "Activity", "Intelligence", "Hacking"]

STAT_WEIGHTS = {
    "Discipline": 5,
    "Deep Focus": 4,
    "Activity": 1,
    "Intelligence": 3,
    "Hacking": 5,
}

STAT_COLORS = {
    "Discipline": "#f43f5e",
    "Deep Focus": "#a855f7",
    "Activity": "#10b981",
    "Intelligence": "#3b82f6",
    "Hacking": "#f59e0b",
}

STAT_DISPLAY_NAMES = {
    "Activity": "Physical",
    "Hacking": "Career",
}

TAG_ALIAS = {
    "physical": "Activity",
    "activity": "Activity",
    "career": "Hacking",
    "hacking": "Hacking",
    "discipline": "Discipline",
    "deep focus": "Deep Focus",
    "intelligence": "Intelligence",
}

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    .stApp {
        background-color: #030712;
        color: #f8fafc;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    .status-card {
        background: linear-gradient(135deg, #111827 0%, #0b0f19 100%);
        border: 1.5px solid #00d2ff;
        border-radius: 10px;
        padding: 14px 12px;
        text-align: center;
        box-shadow: 0 0 12px rgba(0, 210, 255, 0.15);
        margin-top: 4px;
        margin-bottom: 14px;
        overflow: hidden;
    }
    
    .status-title {
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 700;
    }
    
    .status-level {
        font-size: 2.2rem;
        font-weight: 800;
        color: #00d2ff;
        text-shadow: 0 0 8px rgba(0, 210, 255, 0.4);
        margin: 2px 0;
        line-height: 1;
    }

    .status-rank {
        color: #38bdf8;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-top: 4px;
        text-transform: uppercase;
    }

    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #94a3b8;
        margin-bottom: 8px;
        letter-spacing: 1px;
    }
    
    .stat-card-square {
        background-color: #111827;
        border-radius: 8px;
        height: 85px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 6px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .stat-card-name {
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    
    .stat-card-level {
        font-size: 1.3rem;
        font-weight: 800;
        line-height: 1;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def get_credentials():
    user_id = None
    api_token = None

    try:
        user_id = st.secrets.get("HABITICA_USER_ID") or st.secrets.get("habitica_user_id")
        api_token = st.secrets.get("HABITICA_API_TOKEN") or st.secrets.get("habitica_api_token")
    except Exception:
        pass

    if not user_id or not api_token:
        try:
            import config
            cfg = config.load_config()
            user_id = user_id or cfg.get("habitica_user_id")
            api_token = api_token or cfg.get("habitica_api_token")
        except Exception:
            pass

    if not user_id or not api_token:
        try:
            cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    user_id = user_id or cfg.get("habitica_user_id")
                    api_token = api_token or cfg.get("habitica_api_token")
        except Exception:
            pass

    return user_id, api_token


def get_rank(level: int) -> str:
    if level < 5:
        return "E RANK"
    elif level <= 9:
        return "D RANK"
    elif level <= 19:
        return "C RANK"
    elif level <= 34:
        return "B RANK"
    elif level <= 49:
        return "A RANK"
    elif level <= 64:
        return "S RANK"
    elif level <= 79:
        return "SS RANK"
    elif level <= 99:
        return "SSS RANK"
    else:
        return "ANOTHER LEVEL"


def calculate_stats_from_habitica(raw_data):
    tags_data = raw_data.get("tags", [])
    tag_map = {}
    for tag in tags_data:
        tname = tag.get("name", "").strip().lower()
        if tname in TAG_ALIAS:
            tag_map[tag["id"]] = TAG_ALIAS[tname]

    stat_progress = {s: 0.0 for s in STATS}
    all_tasks = (
        raw_data.get("habits", []) +
        raw_data.get("dailies", []) +
        raw_data.get("todos", [])
    )

    for task in all_tasks:
        task_tags = task.get("tags", [])
        matching_stats = {tag_map[tid] for tid in task_tags if tid in tag_map}

        if not matching_stats:
            continue

        priority = task.get("priority", 1)
        if priority == 2:
            increment = 0.20
        elif priority == 1.5:
            increment = 0.10
        else:
            increment = 0.05

        completions = 0
        ttype = task.get("type", "")
        if ttype == "habit":
            completions = task.get("counterUp", 0) - task.get("counterDown", 0)
        elif ttype == "daily":
            if task.get("completed", False):
                completions = 1
            history = task.get("history", [])
            if history:
                completed_history = [h for h in history if h.get("completed", False) or h.get("value", 0) > 0]
                completions = max(completions, len(completed_history))
        elif ttype == "todo":
            if task.get("completed", False):
                completions = 1

        if completions > 0:
            total_exp = completions * increment
            for stat_name in matching_stats:
                stat_progress[stat_name] += total_exp

    stats_block = {}
    for s in STATS:
        total_val = stat_progress[s]
        lvl = 1 + int(total_val)
        prog = total_val - int(total_val)
        stats_block[s] = {"level": max(1, lvl), "progress": round(prog, 2)}

    return stats_block


def calculate_overall_level(stats_block):
    if stats_engine and hasattr(stats_engine, "overall_level"):
        try:
            return stats_engine.overall_level(stats_block)
        except Exception:
            pass

    total_weight = sum(STAT_WEIGHTS.values())
    weighted_sum = sum(stats_block[s]["level"] * STAT_WEIGHTS.get(s, 1) for s in STATS if s in stats_block)
    return max(1, round(weighted_sum / total_weight))


def display_dashboard():
    user_id, api_token = get_credentials()
    stats_block = None

    if user_id and api_token:
        try:
            raw_data = habitica_api.fetch_user_data(user_id, api_token)
            if stats_engine and hasattr(stats_engine, "calculate_stats"):
                try:
                    stats_block = stats_engine.calculate_stats(raw_data)
                except Exception:
                    pass
            if not stats_block:
                stats_block = calculate_stats_from_habitica(raw_data)
        except Exception as e:
            st.error(f"Sync error: {e}")

    if not stats_block:
        if stats_engine and hasattr(stats_engine, "new_stat_block"):
            stats_block = stats_engine.new_stat_block()
        else:
            stats_block = {s: {"level": 1, "progress": 0.0} for s in STATS}

    current_overall_level = calculate_overall_level(stats_block)
    player_rank = get_rank(current_overall_level)

    st.markdown(
        f"""<div class="status-card">
                <div class="status-title">SYSTEM STATUS</div>
                <div class="status-level">LVL {current_overall_level:02d}</div>
                <div class="status-rank">[{player_rank}]</div>
            </div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">ATTRIBUTES</div>', unsafe_allow_html=True)

    cols = st.columns(2)
    for idx, stat_name in enumerate(STATS):
        stat_info = stats_block.get(stat_name, {"level": 1, "progress": 0.0})
        level = stat_info["level"]

        color = STAT_COLORS.get(stat_name, "#00d2ff")
        display_name = STAT_DISPLAY_NAMES.get(stat_name, stat_name)

        single_line_card = (
            f'<div class="stat-card-square" style="border: 1px solid {color};">'
            f'<div class="stat-card-name" style="color: {color};">◈ {display_name}</div>'
            f'<div class="stat-card-level" style="color: {color};">LVL {level:02d}</div>'
            f"</div>"
        )

        with cols[idx % 2]:
            st.markdown(single_line_card, unsafe_allow_html=True)


if hasattr(st, "fragment"):
    @st.fragment(run_every=3)
    def live_dashboard():
        display_dashboard()
    live_dashboard()
else:
    display_dashboard()
