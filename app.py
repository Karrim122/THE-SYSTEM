import time
import streamlit as st
import data_store
import stats_engine
from habitica_api import HabiticaClient, HabiticaError

# ---------------------------------------------------------
# Page Configuration & Styling
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

# Load current app state
app_data = data_store.load_data()

# ---------------------------------------------------------
# Habitica Data Processing via stats_engine
# ---------------------------------------------------------
def sync_habitica():
    try:
        user_id = st.secrets.get("HABITICA_USER_ID")
        api_token = st.secrets.get("HABITICA_API_TOKEN")

        if not user_id or not api_token:
            st.error("Missing Habitica API credentials in Streamlit Secrets!")
            return

        client = HabiticaClient(user_id, api_token)
        user_info = client.get_user()
        stats = user_info.get("stats", {})

        # Extract Habitica Stats
        app_data["hp"] = float(stats.get("hp", 50))
        app_data["max_hp"] = float(stats.get("maxHP", 50))

        user_lvl = stats.get("lvl", 1)
        user_exp = stats.get("exp", 0)
        to_next = max(1, stats.get("toNextLevel", 100))
        exp_progress = min(max(user_exp / to_next, 0.0), 1.0)

        # Map Habitica primary attributes (STR, INT, PER, CON) to custom stats
        str_val = stats.get("str", 0)
        int_val = stats.get("int", 0)
        per_val = stats.get("per", 0)
        con_val = stats.get("con", 0)

        # Derive dynamic individual levels using stats_engine logic
        app_data["stats"]["Discipline"]["level"] = max(1, int(con_val) if con_val > 0 else user_lvl)
        app_data["stats"]["Discipline"]["progress"] = exp_progress

        app_data["stats"]["Deep Focus"]["level"] = max(1, int(per_val) if per_val > 0 else user_lvl)
        app_data["stats"]["Deep Focus"]["progress"] = exp_progress

        app_data["stats"]["Activity"]["level"] = max(1, int(str_val) if str_val > 0 else user_lvl)
        app_data["stats"]["Activity"]["progress"] = exp_progress

        app_data["stats"]["Intelligence"]["level"] = max(1, int(int_val) if int_val > 0 else user_lvl)
        app_data["stats"]["Intelligence"]["progress"] = exp_progress

        app_data["stats"]["Hacking"]["level"] = max(1, int((int_val + per_val) / 2) if (int_val or per_val) else user_lvl)
        app_data["stats"]["Hacking"]["progress"] = exp_progress

        data_store.add_log(app_data, "Recalculated stats via stats_engine.")
        data_store.save_data(app_data)
        st.success("Stats successfully recalculated!")

    except HabiticaError as err:
        st.error(f"Sync failed: {err}")
    except Exception as e:
        st.error(f"Sync error: {e}")

# Initial load sync
if app_data.get("last_synced") is None:
    sync_habitica()

# ---------------------------------------------------------
# Header & System Status Banner (Clean - No 'Last Synced')
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

# Vitality Display
hp_ratio = min(max(app_data["hp"] / app_data["max_hp"], 0.0), 1.0)
st.caption(f"VITALITY (HP): {app_data['hp']:.1f} / {app_data['max_hp']:.0f}")
st.progress(hp_ratio)

st.subheader("Attributes")

# ---------------------------------------------------------
# Render Calculated Attributes
# ---------------------------------------------------------
for stat_name in stats_engine.STATS:
    stat_info = app_data["stats"][stat_name]
    level = stat_info["level"]
    progress = stat_info["progress"]

    st.markdown(
        f"""
        <div class="stat-box">
            <div class="stat-header">
                <span class="stat-name">{stat_name}</span>
                <span class="stat-level-text">Lvl {level}</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(min(max(progress, 0.0), 1.0))

# ---------------------------------------------------------
# Logs
# ---------------------------------------------------------
with st.expander("System Logs"):
    if app_data.get("log"):
        for log_entry in app_data["log"][:15]:
            st.text(log_entry)
    else:
        st.caption("No system events recorded.")
