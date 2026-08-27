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

# ---------------------------------------------------------
# Data Store Initialization
# ---------------------------------------------------------
app_data = data_store.load_data()

# ---------------------------------------------------------
# Habitica Synchronization Function
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
        stats_data = user_info.get("stats", {})

        app_data["hp"] = float(stats_data.get("hp", 50))
        app_data["max_hp"] = float(stats_data.get("maxHP", 50))
        app_data["last_synced"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Map Habitica Experience / Level to Player Attributes
        user_lvl = stats_data.get("lvl", 1)
        exp_pct = stats_data.get("exp", 0) / max(1, stats_data.get("toNextLevel", 100))

        for stat in stats_engine.STATS:
            app_data["stats"][stat]["level"] = max(1, user_lvl)
            app_data["stats"][stat]["progress"] = min(max(exp_pct, 0.0), 1.0)

        data_store.add_log(app_data, f"Synced telemetry from Habitica. User Level: {user_lvl}")
        data_store.save_data(app_data)
        st.success("Successfully synchronized with Habitica!")
    except HabiticaError as err:
        st.error(f"Sync failed: {err}")
    except Exception as e:
        st.error(f"Unexpected error during sync: {e}")

# Automatically sync on initial session load
if app_data.get("last_synced") is None:
    sync_habitica()

# ---------------------------------------------------------
# Header & Actions
# ---------------------------------------------------------
col1, col2 = st.columns([3, 1])
with col1:
    current_overall = stats_engine.overall_level(app_data["stats"])
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-title">SYSTEM STATUS</div>
            <div class="status-level">LVL {current_overall}</div>
            <div style="color: #6b7280; font-size: 0.85rem; margin-top: 8px;">
                LAST SYNCED: {app_data.get("last_synced") or "Never"}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col2:
    st.write("")
    st.write("")
    if st.button("🔄 SYNC", use_container_width=True):
        sync_habitica()
        st.rerun()

# Vitality (HP) Display
hp_ratio = min(max(app_data["hp"] / app_data["max_hp"], 0.0), 1.0)
st.caption(f"VITALITY (HP): {app_data['hp']:.1f} / {app_data['max_hp']:.0f}")
st.progress(hp_ratio)

st.subheader("Attributes")

# ---------------------------------------------------------
# Render Attributes
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
# System Logs
# ---------------------------------------------------------
with st.expander("System Logs"):
    if app_data.get("log"):
        for log_entry in app_data["log"][:15]:
            st.text(log_entry)
    else:
        st.caption("No system events recorded yet.")
