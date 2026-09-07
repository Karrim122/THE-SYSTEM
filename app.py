import time
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

# Custom Styling
bg_color = config.THEME.get('backgroundColor', '#030712')
sec_bg = config.THEME.get('secondaryBackgroundColor', '#0b0f19')
text_color = config.THEME.get('textColor', '#f8fafc')
primary_color = config.THEME.get('primaryColor', '#00d2ff')
font_family = config.THEME.get('font', 'sans serif')

st.markdown(f"""
<style>
    body {{ background-color: {bg_color}; color: {text_color}; font-family: '{font_family}'; }}
    .stApp {{ background-color: {bg_color}; }}
    
    .status-card {{
        background-color: {sec_bg};
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 12px;
    }}
    
    .hud-header {{ font-size: 24px; font-weight: bold; color: {primary_color}; letter-spacing: 1px; }}
    .sub-header {{ font-size: 11px; color: #64748b; font-weight: bold; margin-bottom: 15px; }}
    .level-badge {{ font-size: 42px; font-weight: 800; color: {primary_color}; text-shadow: 0 0 10px rgba(0, 210, 255, 0.4); }}
    .rank-text {{ font-size: 16px; font-weight: bold; color: #f59e0b; }}
    .stat-card {{ background-color: #111827; border-radius: 8px; padding: 14px; text-align: center; border: 1px solid #1e293b; }}
    .metric-label {{ font-size: 10px; color: #64748b; font-weight: bold; }}
    .metric-val {{ font-size: 16px; color: {primary_color}; font-weight: bold; }}
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

# Auto-refresh heartbeat every 5 minutes (300,000 ms) to prevent API rate limiting
st_autorefresh(interval=300000, key="habitica_sync_heartbeat")

if "data" not in st.session_state:
    st.session_state.data = data_store.load_data()

if "last_sync_timestamp" not in st.session_state:
    st.session_state.last_sync_timestamp = 0

data = st.session_state.data

st.sidebar.title("⚡ SYSTEM CONTROL")
view_mode = st.sidebar.radio("NAVIGATION", ["🏠 STATUS HUD", "📜 ABILITY LEDGER"])

def execute_sync(force=False):
    current_time = time.time()
    # Cooldown of 300 seconds (5 minutes) unless manually triggered
    if not force and (current_time - st.session_state.last_sync_timestamp < 300):
        return

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
            if not stat:
                continue
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
            if not stat:
                continue
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
            if not stat:
                continue
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
        st.session_state.last_sync_timestamp = current_time
        st.sidebar.success("SYNCHRONIZED WITH HABITICA")
    except HabiticaError as e:
        st.sidebar.error(f"Sync failed: {e}")

if st.sidebar.button("🔄 MANUAL SYNC"):
    execute_sync(force=True)
elif config.HABITICA_USER_ID and config.HABITICA_API_TOKEN:
    execute_sync(force=False)

# Safe level and rank evaluation
raw_level = stats_engine.overall_level(data["stats"]) + data.get("overall_level_offset", 0)
effective_overall = max(1, int(raw_level))

try:
    rank_title = milestones.get_rank_title(effective_overall)
except AttributeError:
    if effective_overall >= 26: rank_title = "S"
    elif effective_overall >= 21: rank_title = "A"
    elif effective_overall >= 16: rank_title = "B"
    elif effective_overall >= 11: rank_title = "C"
    elif effective_overall >= 6: rank_title = "D"
    else: rank_title = "E"

if view_mode == "🏠 STATUS HUD":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="hud-header">[ PLAYER STATUS ]</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">▲ PLAYER LINK: ACTIVE | MIND MONARCH INTERFACE</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div style="text-align: right;"><span class="level-badge">LVL. {effective_overall:02d}</span><br><span class="rank-text">[{rank_title} RANK]</span></div>',
            unsafe_allow_html=True
        )

    hp, max_hp = data.get("hp", 50.0), data.get("max_hp", 50.0)
    st.markdown(f"**[ HP ] VITALITY:** `{hp:.1f} / {max_hp:.0f}`")
    st.progress(max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0)
    st.markdown("---")

    grid_cols = st.columns(3)
    for idx, stat_name in enumerate(stats_engine.STATS):
        entry = data["stats"][stat_name]
        color = STAT_COLORS.get(stat_name, "#00d2ff")
        stat_lvl = int(entry["level"])
        
        try:
            stat_rank = milestones.get_stat_rank(stat_name, stat_lvl)
        except AttributeError:
            stat_rank = f"{rank_title} RANK"

        with grid_cols[idx % 3]:
            st.markdown(f"""
            <div class="stat-card" style="border-top: 3px solid {color};">
                <div style="color: {color}; font-weight: bold;">◈ {STAT_DISPLAY_NAMES.get(stat_name, stat_name).upper()}</div>
                <div style="font-size: 24px; font-weight: bold; color: {color};">LVL {stat_lvl:02d}</div>
                <div style="font-size: 10px; color: #64748b;">[{stat_rank}]</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(1.0, max(0.0, float(entry["progress"]))))

elif view_mode == "📜 ABILITY LEDGER":
    for stat in stats_engine.STATS:
        curr_lvl = int(data["stats"][stat]["level"])
        st.markdown(f"#### ◈ {STAT_DISPLAY_NAMES.get(stat, stat).upper()} (Lv.{curr_lvl})")
        
        try:
            m_list = milestones.milestones_for(stat)
        except AttributeError:
            m_list = milestones.MILESTONES_DATA.get(stat, [])
            
        for lvl, title, desc in m_list:
            unlocked = curr_lvl >= lvl
            st.markdown(f"*{'✅' if unlocked else '🔒'}* **LV {lvl:02d} - {title.upper()}**: {desc}")
