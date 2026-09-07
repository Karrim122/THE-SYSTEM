import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import date
import data_store
import stats_engine
import milestones
from habitica_api import HabiticaClient, HabiticaError
import config

st.set_page_config(
    page_title="SYSTEM: PLAYER STATUS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
    body {{ background-color: {config.THEME.get('backgroundColor', '#030712')}; color: {config.THEME.get('textColor', '#f8fafc')}; font-family: '{config.THEME.get('font', 'sans serif')}'; }}
    .stApp {{ background-color: {config.THEME.get('backgroundColor', '#030712')}; }}
    
    .status-card {{
        background-color: {config.THEME.get('secondaryBackgroundColor', '#0b0f19')};
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 12px;
    }}
    
    .hud-header {{ font-size: 24px; font-weight: bold; color: {config.THEME.get('primaryColor', '#00d2ff')}; letter-spacing: 1px; }}
    .sub-header {{ font-size: 11px; color: #64748b; font-weight: bold; margin-bottom: 15px; }}
    .level-badge {{ font-size: 42px; font-weight: 800; color: {config.THEME.get('primaryColor', '#00d2ff')}; text-shadow: 0 0 10px rgba(0, 210, 255, 0.4); }}
    .rank-text {{ font-size: 16px; font-weight: bold; color: #f59e0b; }}
    .stat-card {{ background-color: #111827; border-radius: 8px; padding: 14px; text-align: center; border: 1px solid #1e293b; }}
    .metric-label {{ font-size: 10px; color: #64748b; font-weight: bold; }}
    .metric-val {{ font-size: 16px; color: {config.THEME.get('primaryColor', '#00d2ff')}; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

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

st_autorefresh(interval=15000, key="habitica_sync_heartbeat")

if "data" not in st.session_state:
    st.session_state.data = data_store.load_data()

data = st.session_state.data

st.sidebar.title("⚡ SYSTEM CONTROL")
view_mode = st.sidebar.radio("NAVIGATION", ["🏠 STATUS HUD", "📜 ABILITY LEDGER", "📜 SYSTEM LOGS"])

def execute_sync():
    if not config.HABITICA_USER_ID or not config.HABITICA_API_TOKEN:
        st.sidebar.error("Credentials missing in config.json")
        return

    try:
        client = HabiticaClient(config.HABITICA_USER_ID, config.HABITICA_API_TOKEN)
        user_data = client.get_user()
        stats_data = user_data.get("stats", {})
        data["hp"] = float(stats_data.get("hp", 50))
        data["max_hp"] = float(stats_data.get("maxHP", 50))

        tags = client.get_tags()
        tag_id_to_name = {t["id"]: t["name"] for t in tags}

        habits = client.get_tasks("habits")
        dailies = client.get_tasks("dailys")
        todos = client.get_tasks("todos") + client.get_tasks("completedTodos")

        today_str = date.today().isoformat()

        # Habits
        for task in habits:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat: continue
            task_id = task["id"]
            counter_up = task.get("counterUp", 0) or 0
            counter_down = task.get("counterDown", 0) or 0
            prev = data["tasks"].get(task_id, {"counterUp": 0, "counterDown": 0})

            new_up = max(0, counter_up - prev.get("counterUp", 0))
            if new_up > 0:
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))] * new_up
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                data_store.add_log(data, f"Action '{task.get('text','?')}' x{new_up} -> +{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")

            new_down = max(0, counter_down - prev.get("counterDown", 0))
            if new_down > 0:
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))] * new_down
                stats_engine.apply_progress(data["stats"], stat, inc, direction="down")
                data_store.add_log(data, f"Penalty '{task.get('text','?')}' x{new_down} -> -{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")

            data["tasks"][task_id] = {"counterUp": counter_up, "counterDown": counter_down}

        # Dailies
        for task in dailies:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat: continue
            task_id = task["id"]
            prev = data["tasks"].get(task_id, {})
            if task.get("completed") and prev.get("lastCreditedDate") != today_str:
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))]
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                data_store.add_log(data, f"Daily '{task.get('text','?')}' cleared -> +{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")
                prev["lastCreditedDate"] = today_str
            data["tasks"][task_id] = prev

        # Todos
        for task in todos:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat: continue
            task_id = task["id"]
            prev = data["tasks"].get(task_id, {})
            if task.get("completed") and not prev.get("credited", False):
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))]
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                data_store.add_log(data, f"Quest '{task.get('text','?')}' cleared -> +{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")
                prev["credited"] = True
            data["tasks"][task_id] = prev

        data["last_synced"] = today_str
        data_store.save_data(data)
        st.sidebar.success("SYNCHRONIZED WITH HABITICA")
    except HabiticaError as e:
        st.sidebar.error(f"Sync failed: {e}")

if config.HABITICA_USER_ID and config.HABITICA_API_TOKEN:
    execute_sync()

effective_overall = max(1, stats_engine.overall_level(data["stats"]) + data.get("overall_level_offset", 0))

if view_mode == "🏠 STATUS HUD":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="hud-header">[ PLAYER STATUS ]</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div style="text-align: right;"><span class="level-badge">LVL. {effective_overall:02d}</span><br><span class="rank-text">[{milestones.get_rank_title(effective_overall)} RANK]</span></div>', unsafe_allow_html=True)

    hp, max_hp = data.get("hp", 50.0), data.get("max_hp", 50.0)
    st.markdown(f"**[ HP ] VITALITY:** `{hp:.1f} / {max_hp:.0f}`")
    st.progress(max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0)
    st.markdown("---")

    grid_cols = st.columns(3)
    for idx, stat_name in enumerate(stats_engine.STATS):
        entry = data["stats"][stat_name]
        color = STAT_COLORS.get(stat_name, "#00d2ff")
        with grid_cols[idx % 3]:
            st.markdown(f"""
            <div class="stat-card" style="border-top: 3px solid {color};">
                <div style="color: {color}; font-weight: bold;">◈ {STAT_DISPLAY_NAMES.get(stat_name, stat_name).upper()}</div>
                <div style="font-size: 24px; font-weight: bold; color: {color};">LVL {entry['level']:02d}</div>
                <div style="font-size: 10px; color: #64748b;">[{milestones.get_stat_rank(stat_name, entry['level'])}]</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(1.0, max(0.0, entry["progress"])))

elif view_mode == "📜 ABILITY LEDGER":
    for stat in stats_engine.STATS:
        curr_lvl = data["stats"][stat]["level"]
        st.markdown(f"#### ◈ {STAT_DISPLAY_NAMES.get(stat, stat).upper()} (Lv.{curr_lvl})")
        for lvl, title, desc in milestones.milestones_for(stat):
            unlocked = curr_lvl >= lvl
            st.markdown(f"*{'✅' if unlocked else '🔒'}* **LV {lvl:02d} - {title.upper()}**: {desc}")

elif view_mode == "📜 SYSTEM LOGS":
    for l in data.get("log", [])[:30]:
        st.code(l, language="text")
