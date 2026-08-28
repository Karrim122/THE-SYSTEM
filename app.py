import time
from datetime import date
import streamlit as st
import data_store
import stats_engine
from habitica_api import HabiticaClient, HabiticaError

# ---------------------------------------------------------
# Page Configuration & Visual Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hunter Status Window",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    .status-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        margin-bottom: 20px;
    }
    .status-title {
        font-size: 0.9rem;
        letter-spacing: 2px;
        color: #9ca3af;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .status-level {
        font-size: 3.5rem;
        font-weight: 800;
        color: #60a5fa;
        text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
        margin: 0;
        line-height: 1;
    }
    .stat-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 8px;
    }
    .stat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stat-name {
        font-weight: 700;
        font-size: 1.1rem;
        color: #f3f4f6;
    }
    .stat-level-text {
        font-weight: bold;
        color: #3b82f6;
        font-size: 1.1rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Load existing state
app_data = data_store.load_data()

# ---------------------------------------------------------
# Habitica Sync Processing via stats_engine
# ---------------------------------------------------------
def sync_habitica():
    try:
        user_id = st.secrets.get("HABITICA_USER_ID")
        api_token = st.secrets.get("HABITICA_API_TOKEN")

        if not user_id or not api_token:
            st.error("Missing Habitica API credentials in Streamlit Secrets!")
            return

        client = HabiticaClient(user_id, api_token)

        # Capture overall level prior to calculation
        old_overall = stats_engine.overall_level(app_data["stats"])

        # Update HP
        user_info = client.get_user()
        user_stats = user_info.get("stats", {})
        app_data["hp"] = float(user_stats.get("hp", 50))
        app_data["max_hp"] = float(user_stats.get("maxHP", 50))

        tags = client.get_tags()
        tag_id_to_name = {t["id"]: t["name"] for t in tags}

        habits = client.get_tasks("habits")
        dailies = client.get_tasks("dailys")
        active_todos = client.get_tasks("todos")
        completed_todos = client.get_tasks("completedTodos")
        todos = active_todos + completed_todos

        today_str = date.today().isoformat()

        # 1. Process Habits
        for task in habits:
            stat_name = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat_name:
                continue

            task_id = task["id"]
            counter_up = task.get("counterUp", 0) or 0
            counter_down = task.get("counterDown", 0) or 0

            prev = app_data["tasks"].get(task_id, {"counterUp": 0, "counterDown": 0})
            prev_up = prev.get("counterUp", 0)
            prev_down = prev.get("counterDown", 0)

            new_up = counter_up - prev_up if counter_up >= prev_up else counter_up
            if new_up > 0:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty] * new_up
                lvl_change = stats_engine.apply_progress(app_data["stats"], stat_name, increment, direction="up")
                log_msg = f"Quest Action '{task.get('text')}' x{new_up} -> +{stat_name} EXP"
                if lvl_change > 0:
                    log_msg += f" [LEVEL UP! {stat_name} is now Lv.{app_data['stats'][stat_name]['level']}]"
                data_store.add_log(app_data, log_msg)

            new_down = counter_down - prev_down if counter_down >= prev_down else counter_down
            if new_down > 0:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty] * new_down
                lvl_change = stats_engine.apply_progress(app_data["stats"], stat_name, increment, direction="down")
                log_msg = f"Penalty Action '{task.get('text')}' x{new_down} -> -{stat_name} EXP"
                if lvl_change < 0:
                    log_msg += f" [LEVEL DOWN! {stat_name} is now Lv.{app_data['stats'][stat_name]['level']}]"
                data_store.add_log(app_data, log_msg)

            app_data["tasks"][task_id] = {"counterUp": counter_up, "counterDown": counter_down}

        # 2. Process Dailies
        for task in dailies:
            stat_name = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat_name:
                continue

            task_id = task["id"]
            completed = bool(task.get("completed"))
            prev = app_data["tasks"].get(task_id, {})

            if completed and prev.get("lastCreditedDate") != today_str:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty]
                lvl_change = stats_engine.apply_progress(app_data["stats"], stat_name, increment, direction="up")
                log_msg = f"Daily Quest '{task.get('text')}' cleared -> +{stat_name} EXP"
                if lvl_change > 0:
                    log_msg += f" [LEVEL UP! {stat_name} is now Lv.{app_data['stats'][stat_name]['level']}]"
                data_store.add_log(app_data, log_msg)
                prev["lastCreditedDate"] = today_str

            app_data["tasks"][task_id] = prev

        # 3. Process To-Dos
        for task in todos:
            stat_name = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat_name:
                continue

            task_id = task["id"]
            completed = bool(task.get("completed"))
            prev = app_data["tasks"].get(task_id, {})

            if completed and not prev.get("credited", False):
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty]
                lvl_change = stats_engine.apply_progress(app_data["stats"], stat_name, increment, direction="up")
                log_msg = f"Quest Objective '{task.get('text')}' cleared -> +{stat_name} EXP"
                if lvl_change > 0:
                    log_msg += f" [LEVEL UP! {stat_name} is now Lv.{app_data['stats'][stat_name]['level']}]"
                data_store.add_log(app_data, log_msg)
                prev["credited"] = True

            app_data["tasks"][task_id] = prev

        app_data["last_synced"] = today_str
        data_store.save_data(app_data)

        # Trigger Pop-up Message on Level-Up
        new_overall = stats_engine.overall_level(app_data["stats"])
        if new_overall > old_overall:
            st.toast("⚡ You leveled up!", icon="🎉")
            st.balloons()
            st.success(f"You leveled up! Reached Overall Level {new_overall}!")
        else:
            st.success("Synchronized with Habitica!")

    except HabiticaError as err:
        st.error(f"Sync failed: {err}")
    except Exception as e:
        st.error(f"Sync error: {e}")

# ---------------------------------------------------------
# UI Rendering
# ---------------------------------------------------------
col1, col2 = st.columns([3, 1])
with col1:
    current_overall = stats_engine.overall_level(app_data["stats"])
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-title">SYSTEM STATUS</div>
            <div class="status-level">LVL {current_overall}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col2:
    st.write("")
    if st.button("🔄 SYNC", use_container_width=True):
        sync_habitica()
        st.rerun()

# Health Display
hp_ratio = min(max(app_data["hp"] / app_data["max_hp"], 0.0), 1.0)
st.caption(f"VITALITY (HP): {app_data['hp']:.1f} / {app_data['max_hp']:.0f}")
st.progress(hp_ratio)

st.subheader("Attributes")

# Render Attributes with explicit percentage labels
for stat_name in stats_engine.STATS:
    stat_info = app_data["stats"][stat_name]
    level = stat_info["level"]
    progress = stat_info["progress"]

    pct_display = int(progress * 100)

    st.markdown(
        f"""
        <div class="stat-box">
            <div class="stat-header">
                <span class="stat-name">{stat_name}</span>
                <span class="stat-level-text">Lvl {level} ({pct_display}%)</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(min(max(progress, 0.0), 1.0))

# System Logs
with st.expander("System Logs"):
    if app_data.get("log"):
        for log_entry in app_data["log"][:15]:
            st.text(log_entry)
    else:
        st.caption("No system events recorded.")
