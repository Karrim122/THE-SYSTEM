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

# Stat Colors and Display Name Maps matching desktop UI
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

st.markdown(
    """
    <style>
    .stApp {
        background-color: #030712;
        color: #f8fafc;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    .status-card {
        background: linear-gradient(135deg, #111827 0%, #0b0f19 100%);
        border: 2px solid #00d2ff;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.2);
        margin-bottom: 25px;
    }
    
    .status-title {
        font-size: 0.9rem;
        letter-spacing: 2px;
        color: #64748b;
        text-transform: uppercase;
        margin-bottom: 4px;
        font-weight: 700;
    }
    
    .status-level {
        font-size: 3.5rem;
        font-weight: 800;
        color: #00d2ff;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.4);
        margin: 0;
        line-height: 1;
    }

    /* Square stat box styling */
    .stat-card-square {
        background-color: #111827;
        border-radius: 12px;
        aspect-ratio: 1 / 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    .stat-card-name {
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 1px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    
    .stat-card-level {
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.1;
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
        <div class="status-level">LVL {current_overall_level:02d}</div>
        <div style="color: #64748b; font-size: 0.85rem; margin-top: 8px;">
            LAST SYNCED: {app_data.get("last_synced") or "Never"}
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

st.subheader("Attributes")

# ---------------------------------------------------------
# Render Square Attribute Blocks via Streamlit Columns
# ---------------------------------------------------------
cols = st.columns(2)

for idx, stat_name in enumerate(stats_engine.STATS):
    stat_info = stats_block[stat_name]
    level = stat_info["level"]
    
    color = STAT_COLORS.get(stat_name, "#00d2ff")
    display_name = STAT_DISPLAY_NAMES.get(stat_name, stat_name)

    card_html = f"""<div class="stat-card-square" style="border: 1.5px solid {color};"><div class="stat-card-name" style="color: {color};">◈ {display_name}</div><div class="stat-card-level" style="color: {color};">LVL {level:02d}</div></div>"""

    # Alternate between left and right column
    with cols[idx % 2]:
        st.markdown(card_html, unsafe_allow_html=True)
