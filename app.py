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
    /* Remove extra Streamlit vertical padding on mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    .stApp {
        background-color: #030712;
        color: #f8fafc;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Compact Header Banner */
    .status-card {
        background: linear-gradient(135deg, #111827 0%, #0b0f19 100%);
        border: 1.5px solid #00d2ff;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 0 12px rgba(0, 210, 255, 0.15);
        margin-bottom: 12px;
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

    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #94a3b8;
        margin-bottom: 8px;
        letter-spacing: 1px;
    }

    /* Mobile 2-column Grid */
    .mobile-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
    }
    
    /* Compact Square Stat Box */
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
        <div style="color: #64748b; font-size: 0.75rem; margin-top: 4px;">
            LAST SYNCED: {app_data.get("last_synced") or "Never"}
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">ATTRIBUTES</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Compact Mobile Grid
# ---------------------------------------------------------
grid_html = '<div class="mobile-grid">'

for stat_name in stats_engine.STATS:
    stat_info = stats_block[stat_name]
    level = stat_info["level"]
    
    color = STAT_COLORS.get(stat_name, "#00d2ff")
    display_name = STAT_DISPLAY_NAMES.get(stat_name, stat_name)

    grid_html += f"""
        <div class="stat-card-square" style="border: 1px solid {color};">
            <div class="stat-card-name" style="color: {color};">◈ {display_name}</div>
            <div class="stat-card-level" style="color: {color};">LVL {level:02d}</div>
        </div>
    """

grid_html += "</div>"

st.markdown(grid_html, unsafe_allow_html=True)
