import streamlit as st
import stats_engine
import habitica_api

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

st.markdown(
    """
    <style>
    /* Top margin spacing fix */
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
    
    /* Header Card Banner */
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

# ---------------------------------------------------------
# Live Data Fetching via Streamlit Secrets
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_live_data():
    try:
        user_id = st.secrets["HABITICA_USER_ID"]
        api_token = st.secrets["HABITICA_API_TOKEN"]
        raw_data = habitica_api.fetch_user_data(user_id, api_token)
        return stats_engine.calculate_stats(raw_data)
    except Exception:
        # Fallback to local data store if secrets or API call fails
        import data_store
        return data_store.load_data()["stats"]

stats_block = load_live_data()

# Calculate Overall Player Level and Rank
current_overall_level = stats_engine.overall_level(stats_block)
player_rank = get_rank(current_overall_level)

# ---------------------------------------------------------
# Header & Player Level Banner
# ---------------------------------------------------------
st.markdown(
    f"""<div class="status-card"><div class="status-title">SYSTEM STATUS</div><div class="status-level">LVL {current_overall_level:02d}</div><div class="status-rank">[{player_rank}]</div></div>""",
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">ATTRIBUTES</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Compact Grid using Streamlit Columns (Single-Line HTML)
# ---------------------------------------------------------
cols = st.columns(2)

for idx, stat_name in enumerate(stats_engine.STATS):
    stat_info = stats_block[stat_name]
    level = stat_info["level"]
    
    color = STAT_COLORS.get(stat_name, "#00d2ff")
    display_name = STAT_DISPLAY_NAMES.get(stat_name, stat_name)

    single_line_card = f'<div class="stat-card-square" style="border: 1px solid {color};"><div class="stat-card-name" style="color: {color};">◈ {display_name}</div><div class="stat-card-level" style="color: {color};">LVL {level:02d}</div></div>'

    with cols[idx % 2]:
        st.markdown(single_line_card, unsafe_allow_html=True)
