import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import date
import data_store
import stats_engine
import milestones
from habitica_api import HabiticaClient, HabiticaError

# Page Config
st.set_page_config(
    page_title="SYSTEM: PLAYER STATUS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Theme CSS (Cyberpunk/Solo Leveling Aesthetic)
st.markdown("""
<style>
    body { background-color: #030712; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
    .stApp { background-color: #030712; }
    
    .status-card {
        background-color: #0b0f19;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 12px;
    }
    
    .hud-header {
        font-size: 24px;
        font-weight: bold;
        color: #00d2ff;
        letter-spacing: 1px;
    }
    
    .sub-header {
        font-size: 11px;
        color: #64748b;
        font-weight: bold;
        margin-bottom: 15px;
    }
    
    .level-badge {
        font-size: 42px;
        font-weight: 800;
        color: #00d2ff;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.4);
    }
    
    .rank-text {
        font-size: 16px;
        font-weight: bold;
        color: #f59e0b;
    }

    .stat-card {
        background-color: #111827;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
        border: 1px solid #1e293b;
    }

    .metric-label { font-size: 10px; color: #64748b; font-weight: bold; }
    .metric-val { font-size: 16px; color: #00d2ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Colors & Mappings matching main.py
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

# Auto-refresh app every 15 seconds for real-time mobile sync
st_autorefresh(interval=15000, key="habitica_sync_heartbeat")

# Load session/stored data
if "data" not in st.session_state:
    st.session_state.data = data_store.load_data()

data = st.session_state.data

# Sidebar Settings for Habitica Credentials
st.sidebar.title("⚡ SYSTEM CONTROL")
user_id = st.sidebar.text_input("PLAYER USER ID", value=st.secrets.get("HABITICA_USER_ID", ""), type="password")
api_token = st.sidebar.text_input("SYSTEM SECRET KEY", value=st.secrets.get("HABITICA_API_TOKEN", ""), type="password")

st.sidebar.markdown("---")
view_mode = st.sidebar.radio("NAVIGATION", ["🏠 STATUS HUD", "📜 ABILITY LEDGER", "📜 SYSTEM LOGS"])

# Sync Engine Function
def execute_sync():
    if not user_id or not api_token:
        st.sidebar.error("Enter Habitica credentials to sync.")
        return

    try:
        client = HabiticaClient(user_id, api_token)
        prev_overall = max(1, stats_engine.overall_level(data["stats"]) + data.get("overall_level_offset", 0))

        user_data = client.get_user()
        stats_data = user_data.get("stats", {})
        data["hp"] = float(stats_data.get("hp", 50))
        data["max_hp"] = float(stats_data.get("maxHP", 50))

        if data["hp"] <= 0:
            if "Discipline" in data["stats"] and data["stats"]["Discipline"]["level"] > 1:
                data["stats"]["Discipline"]["level"] -= 1
            if "Deep Focus" in data["stats"] and data["stats"]["Deep Focus"]["level"] > 1:
                data["stats"]["Deep Focus"]["level"] -= 1
            data["overall_level_offset"] = data.get("overall_level_offset", 0) - 1
            data_store.add_log(data, "⚠️ PENALTY ZONE ENFORCED! HP Depleted: Stats Regressed.")

        tags = client.get_tags()
        tag_id_to_name = {t["id"]: t["name"] for t in tags}

        habits = client.get_tasks("habits")
        dailies = client.get_tasks("dailys")
        active_todos = client.get_tasks("todos")
        completed_todos = client.get_tasks("completedTodos")
        todos = active_todos + completed_todos

        today_str = date.today().isoformat()

        # 1. HABITS
        for task in habits:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            counter_up = task.get("counterUp", 0) or 0
            counter_down = task.get("counterDown", 0) or 0
            prev = data["tasks"].get(task_id, {"counterUp": 0, "counterDown": 0})

            new_up = counter_up - prev.get("counterUp", 0) if counter_up >= prev.get("counterUp", 0) else counter_up
            if new_up > 0:
                diff = stats_engine.priority_to_difficulty(task.get("priority", 1))
                inc = stats_engine.DIFFICULTY_INCREMENT[diff] * new_up
                levels = stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                disp = STAT_DISPLAY_NAMES.get(stat, stat)
                data_store.add_log(data, f"Action '{task.get('text','?')}' x{new_up} -> +{disp} EXP")

            new_down = counter_down - prev.get("counterDown", 0) if counter_down >= prev.get("counterDown", 0) else counter_down
            if new_down > 0:
                diff = stats_engine.priority_to_difficulty(task.get("priority", 1))
                inc = stats_engine.DIFFICULTY_INCREMENT[diff] * new_down
                levels = stats_engine.apply_progress(data["stats"], stat, inc, direction="down")
                disp = STAT_DISPLAY_NAMES.get(stat, stat)
                data_store.add_log(data, f"Penalty '{task.get('text','?')}' x{new_down} -> -{disp} EXP")

            data["tasks"][task_id] = {"counterUp": counter_up, "counterDown": counter_down}

        # 2. DAILIES
        for task in dailies:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            completed = bool(task.get("completed"))
            prev = data["tasks"].get(task_id, {})
            if completed and prev.get("lastCreditedDate") != today_str:
                diff = stats_engine.priority_to_difficulty(task.get("priority", 1))
                inc = stats_engine.DIFFICULTY_INCREMENT[diff]
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                disp = STAT_DISPLAY_NAMES.get(stat, stat)
                data_store.add_log(data, f"Daily '{task.get('text','?')}' cleared -> +{disp} EXP")
                prev["lastCreditedDate"] = today_str
            data["tasks"][task_id] = prev

        # 3. TODOS
        for task in todos:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            completed = bool(task.get("completed"))
            prev = data["tasks"].get(task_id, {})
            if completed and not prev.get("credited", False):
                diff = stats_engine.priority_to_difficulty(task.get("priority", 1))
                inc = stats_engine.DIFFICULTY_INCREMENT[diff]
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                disp = STAT_DISPLAY_NAMES.get(stat, stat)
                data_store.add_log(data, f"Quest '{task.get('text','?')}' cleared -> +{disp} EXP")
                prev["credited"] = True
            data["tasks"][task_id] = prev

        data["last_synced"] = today_str
        data_store.save_data(data)
        st.sidebar.success("SYNCHRONIZED WITH HABITICA")
    except HabiticaError as e:
        st.sidebar.error(f"Sync failed: {e}")

# Run Sync on Load / Heartbeat
if user_id and api_token:
    execute_sync()

# Header & Stats Calculation
base_overall = stats_engine.overall_level(data["stats"])
effective_overall = max(1, base_overall + data.get("overall_level_offset", 0))
overall_rank = milestones.get_rank_title(effective_overall)

# UI Layout
if view_mode == "🏠 STATUS HUD":
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.markdown('<div class="hud-header">[ PLAYER STATUS ]</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">▲ PLAYER LINK: ACTIVE | MIND MONARCH INTERFACE</div>', unsafe_allow_html=True)
    with col_head2:
        st.markdown(f'<div style="text-align: right;"><span class="level-badge">LVL. {effective_overall:02d}</span><br><span class="rank-text">[{overall_rank} RANK]</span></div>', unsafe_allow_html=True)

    # Health Bar
    hp = data.get("hp", 50.0)
    max_hp = data.get("max_hp", 50.0)
    hp_pct = max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0
    st.markdown(f"**[ HP ] VITALITY STATUS:** `{hp:.1f} / {max_hp:.0f}`")
    st.progress(hp_pct)

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### [ CORE ATTRIBUTES ]")
        grid_cols = st.columns(2)
        idx = 0
        for stat_name in stats_engine.STATS:
            entry = data["stats"][stat_name]
            disp_name = STAT_DISPLAY_NAMES.get(stat_name, stat_name)
            color = STAT_COLORS.get(stat_name, "#00d2ff")
            rank = milestones.get_stat_rank(stat_name, entry["level"])

            with grid_cols[idx % 2]:
                st.markdown(f"""
                <div class="stat-card" style="border-top: 3px solid {color};">
                    <div style="color: {color}; font-weight: bold; font-size: 14px;">◈ {disp_name.upper()}</div>
                    <div style="font-size: 28px; font-weight: bold; color: {color};">LVL {entry['level']:02d}</div>
                    <div style="font-size: 11px; color: #64748b;">[{rank}]</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(1.0, max(0.0, entry["progress"])))
            idx += 1

    with col_right:
        st.markdown("### [ SYSTEM ANALYTICS ]")

        levels = {s: data["stats"][s]["level"] for s in stats_engine.STATS}
        highest = max(levels, key=levels.get)
        lowest = min(levels, key=levels.get)
        total_pts = sum(levels.values())
        ratio = (levels[lowest] / levels[highest] * 100) if levels[highest] > 0 else 100

        st.markdown(f"""
        <div class="status-card">
            <div class="metric-label">TOTAL ATTRIBUTE POINTS</div>
            <div class="metric-val">{total_pts} PTS</div>
            <br>
            <div class="metric-label">HIGHEST ATTRIBUTE</div>
            <div class="metric-val" style="color: {STAT_COLORS.get(highest)};">{STAT_DISPLAY_NAMES.get(highest, highest).upper()} (LVL {levels[highest]})</div>
            <br>
            <div class="metric-label">LOWEST ATTRIBUTE</div>
            <div class="metric-val" style="color: {STAT_COLORS.get(lowest)};">{STAT_DISPLAY_NAMES.get(lowest, lowest).upper()} (LVL {levels[lowest]})</div>
            <br>
            <div class="metric-label">ATTRIBUTE BALANCE RATIO</div>
            <div class="metric-val">{ratio:.1f}% CONVERGENCE</div>
            <br>
            <div class="metric-label">LAST SYSTEM SYNC</div>
            <div class="metric-val" style="font-size: 12px; color: #64748b;">{data.get('last_synced', 'NOT SYNCED')}</div>
        </div>
        """, unsafe_allow_html=True)

elif view_mode == "📜 ABILITY LEDGER":
    st.markdown("### [ ABILITY LEDGER ]")
    st.caption("MILESTONE REWARDS EARNED THROUGH LEVELING")

    for stat in stats_engine.STATS:
        curr_lvl = data["stats"][stat]["level"]
        color = STAT_COLORS.get(stat, "#00d2ff")
        disp_name = STAT_DISPLAY_NAMES.get(stat, stat)

        st.markdown(f"#### <span style='color:{color};'>◈ {disp_name.upper()}</span> (Current: Lv.{curr_lvl})", unsafe_allow_html=True)

        for lvl, title, desc in milestones.milestones_for(stat):
            unlocked = curr_lvl >= lvl
            status_icon = "✅" if unlocked else "🔒"
            text_color = "#f8fafc" if unlocked else "#64748b"

            st.markdown(f"""
            <div style="background-color: #0b0f19; border-left: 4px solid {color if unlocked else '#1e293b'}; padding: 10px; margin-bottom: 6px; border-radius: 4px;">
                <span style="color: {text_color}; font-weight: bold;">{status_icon} LV {lvl:02d} - {title.upper()}</span><br>
                <span style="color: {text_color}; font-size: 13px;">I will be able to {desc}</span>
            </div>
            """, unsafe_allow_html=True)

elif view_mode == "📜 SYSTEM LOGS":
    st.markdown("### [ SYSTEM ACTION LOGS ]")
    logs = data.get("log", [])
    if not logs:
        st.info("No system activity recorded yet.")
    for l in logs[:30]:
        st.code(l, language="text")
