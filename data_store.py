import streamlit as st
from datetime import datetime

def get_default_data():
    """Returns a baseline status data structure."""
    return {
        "hp": 50.0,
        "max_hp": 50.0,
        "last_synced": None,
        "stats": {
            "Discipline": {"level": 1, "progress": 0.0},
            "Deep Focus": {"level": 1, "progress": 0.0},
            "Activity": {"level": 1, "progress": 0.0},
            "Intelligence": {"level": 1, "progress": 0.0},
            "Hacking": {"level": 1, "progress": 0.0},
        },
        "log": []
    }

def load_data():
    """Loads state from Streamlit Session State instead of local JSON file."""
    if "app_data" not in st.session_state:
        st.session_state["app_data"] = get_default_data()
    return st.session_state["app_data"]

def save_data(data):
    """Updates session state cache."""
    st.session_state["app_data"] = data

def add_log(data, message):
    """Appends a timestamped log entry to the in-memory log list."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    data["log"].insert(0, log_entry)
    data["log"] = data["log"][:50]  # Keep latest 50 entries
