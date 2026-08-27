import time
import streamlit as st
import data_store
import stats_engine

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
        margin-bottom: 25px;
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
# Load Data Store
# ---------------------------------------------------------
app_data = data_store.load_data()
stats_block = app_data["stats"]

# Calculate Overall Player Level
current_overall_level = stats_engine.overall_level(stats_block)

# ---------------------------------------------------------
# Header & Player Level Banner
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="status-card">
        <div class="status-title">SYSTEM STATUS</div>
        <div class="status-level">LVL {current_overall_level}</div>
        <div style="color: #6b7280; font-size: 0.85rem; margin-top: 8px;">
            LAST SYNCED: {app_data.get("last_synced") or "Never"}
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

st.subheader("Attributes")

# ---------------------------------------------------------
# Render Individual Stats (Read-Only View)
# ---------------------------------------------------------
for stat_name in stats_engine.STATS:
    stat_info = stats_block[stat_name]
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
    st.write("")

# ---------------------------------------------------------
# Activity Log Drawer
# ---------------------------------------------------------
with st.expander("System Logs"):
    if app_data.get("log"):
        for log_entry in app_data["log"][:15]:
            st.text(log_entry)
    else:
        st.caption("No system events recorded yet.")

# ---------------------------------------------------------
# Native Auto-Refresh (Runs every 3 seconds)
# ---------------------------------------------------------
time.sleep(3)
st.rerun()