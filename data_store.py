import streamlit as st
from datetime import datetime
import stats_engine

def get_default_data():
    """Returns baseline Hunter Status data initialized with user historical state."""
    return {
        "hp": 50.0,
        "max_hp": 50.0,
        "last_synced": "2026-08-27",
        "overall_level_offset": 0,
        "stats": {
            "Discipline": {"level": 2, "progress": 0.70},
            "Deep Focus": {"level": 2, "progress": 0.55},
            "Activity": {"level": 2, "progress": 0.25},
            "Intelligence": {"level": 2, "progress": 0.90},
            "Hacking": {"level": 1, "progress": 0.85},
        },
        "tasks": {
            "FEB09B1D-FC93-4F33-BEB5-06C74A04B0E1": {"counterUp": 0, "counterDown": 0},
            "F4E27784-E590-455C-BFA9-5EFC39EF2540": {"counterUp": 0, "counterDown": 0},
            "BF7C9479-1D73-42F3-A08F-B4126234BB70": {"counterUp": 0, "counterDown": 0},
            "256E3D37-CB81-4446-B4A7-547003193C14": {"counterUp": 0, "counterDown": 0},
            "D7F892D9-A902-4B6D-8328-56124AC2E1C5": {"counterUp": 1, "counterDown": 1},
            "72CC76EF-3E6B-4170-814E-D439FCABCF08": {"counterUp": 0, "counterDown": 0},
            "BFF9B6C7-57AD-4A67-84B7-E86714E17233": {"counterUp": 1, "counterDown": 0},
            "C3385CC9-B50F-4AFD-9AEC-2E7B3D84EB2C": {"lastCreditedDate": "2026-08-26"},
            "C6AE746D-4718-4E50-880D-97D4BA7D34D5": {"lastCreditedDate": "2026-08-22"},
            "69C64F73-8718-482E-9A88-A34473CC168A": {"lastCreditedDate": "2026-08-27"},
            "DCA47410-FBB4-409F-9C67-354085D81392": {"lastCreditedDate": "2026-08-25"},
            "AB21F5F3-FEB3-4475-B178-7ED49FD32912": {"lastCreditedDate": "2026-08-27"},
            "5113397C-0D9D-4476-944C-F68A551AD32C": {"lastCreditedDate": "2026-08-27"},
            "9720ED88-37D7-4992-9D83-C9D5FC4ABF25": {"lastCreditedDate": "2026-08-24"},
            "7E9D708E-2CE1-4491-95EA-0F79606A41DE": {"counterUp": 0, "counterDown": 1},
            "D9734A07-936E-4C56-AE8B-4B2378BD53C8": {},
            "6FD5E78C-DC68-4E19-800B-0511BAEA5925": {"counterUp": 1, "counterDown": 1},
            "0F740F65-03A4-43A5-A05B-D683A40DD2AB": {"counterUp": 0, "counterDown": 0},
            "EBEE55F6-79AF-470E-ABD8-FB0458494A05": {"lastCreditedDate": "2026-08-25"},
            "B134D6B8-CE54-4A52-9C8C-0DEDC89AB646": {},
            "27A1EEE4-F84B-4CC6-B976-F4C3A583F2A1": {"credited": True},
            "E4DC822B-6591-4533-B28A-525FCFB76BCE": {"credited": True},
            "D9962B0B-738D-4E47-B3E8-B008CF6ECADC": {"credited": True},
            "103520E4-509C-4121-9B59-78B1326CAED9": {"credited": True},
            "E92AD913-41E2-4D8D-9955-02D02D4D28C2": {"credited": True},
            "6FC70EEA-DF2A-4193-81FF-142AF219B1A8": {"credited": True},
            "4c14bc46-8707-403b-ba83-efb3d148677d": {},
            "A4A43DE9-49FF-4DA0-BF77-CC0D6900371C": {"credited": True},
            "9771E965-63A2-4A96-983C-7011C2D383B8": {"credited": True},
            "6C2CCAF7-AA14-4676-BAA9-C73AC94A4D19": {},
            "16F710B5-8C38-4773-9E8E-0F6772A08C72": {"credited": True},
            "A19DD946-2941-4801-A392-B84163018363": {"credited": True},
            "816066D1-B90B-4160-9552-B1FCF22B969A": {},
            "CC0EAD87-7EDE-44FE-829C-A3386F2C6502": {"credited": True},
            "745c802a-3060-43f4-9562-b9d65be3474a": {},
            "DDD86489-B239-49DD-87EF-74968E3C0CD9": {"counterUp": 0, "counterDown": 0},
            "8b453e25-df4f-4a96-b372-4ee540ec33e8": {},
            "E30D7B03-3A1B-4677-A734-2912CDB79FF9": {"credited": True},
            "4fa7851b-0cc8-41a3-af66-da485068703a": {"credited": True},
        },
        "log": [
            "[2026-08-27] Quest Objective 'git hub' cleared -> +Deep Focus EXP",
            "[2026-08-27] Quest Action '🔴Distraction ' x1 -> +Discipline EXP",
            "[2026-08-27] Quest Objective 'التكيف' cleared -> +Discipline EXP",
            "[2026-08-27] Daily Quest '♟️Chess' cleared -> +Intelligence EXP",
            "[2026-08-27] Daily Quest '🏃Activity ' cleared -> +Activity EXP",
            "[2026-08-27] Daily Quest '⏳Focus block' cleared -> +Deep Focus EXP",
            "[2026-08-27] Penalty Action '🥗Nutrition' x1 -> -Activity EXP",
            "[2026-08-27] Quest Action '🥗Nutrition' x1 -> +Activity EXP",
            "[2026-08-26] Quest Objective 'Linkedin' cleared -> +Hacking EXP",
            "[2026-08-26] Daily Quest '🏃Activity ' cleared -> +Activity EXP [LEVEL UP! Activity is now Lv.2]",
            "[2026-08-26] Penalty Action '📱Scrolling' x1 -> -Deep Focus EXP",
            "[2026-08-26] Penalty Action '🔴Distraction ' x2 -> -Discipline EXP",
            "[2026-08-26] Quest Action '🔴Distraction ' x1 -> +Discipline EXP",
            "[2026-08-26] Penalty Action '🥗Nutrition' x2 -> -Activity EXP",
            "[2026-08-26] Quest Action '🥗Nutrition' x1 -> +Activity EXP",
            "[2026-08-26] Quest Objective 'جد استخدام للstats' cleared -> +Intelligence EXP",
            "[2026-08-26] Daily Quest '⏳Focus block' cleared -> +Deep Focus EXP",
            "[2026-08-26] Daily Quest '☀️Wake up early' cleared -> +Discipline EXP",
            "[2026-08-25] Quest Action '❇️Just start it ⌚' x1 -> +Discipline EXP",
            "[2026-08-25] Daily Quest '🏃Activity ' cleared -> +Activity EXP",
            "[2026-08-25] Penalty Action '🥗Nutrition' x1 -> -Activity EXP",
            "[2026-08-25] Quest Action '🥗Nutrition' x1 -> +Activity EXP",
            "[2026-08-25] Quest Objective 'Blitz elo 1620' cleared -> +Intelligence EXP",
            "[2026-08-25] Daily Quest '👨‍💻Web pentest course' cleared -> +Hacking EXP",
            "[2026-08-25] Penalty Action '🥗Nutrition' x1 -> -Activity EXP",
            "[2026-08-25] Quest Action '🥗Nutrition' x1 -> +Activity EXP",
            "[2026-08-25] Quest Action '⏰Pomodoro' x1 -> +Deep Focus EXP",
            "[2026-08-25] Daily Quest '♟️Chess' cleared -> +Intelligence EXP",
            "[2026-08-25] Quest Objective 'Test' cleared -> +Intelligence EXP",
            "[2026-08-25] Quest Objective 'Update the system' cleared -> +Intelligence EXP",
            "[2026-08-25] Daily Quest '🛒CCNA course' cleared -> +Hacking EXP",
            "[2026-08-25] Daily Quest '⏳Focus block' cleared -> +Deep Focus EXP",
            "[2026-08-25] Daily Quest '☀️Wake up early' cleared -> +Discipline EXP",
        ],
    }

def load_data():
    """Loads state from Streamlit Session State, using user initial data as baseline."""
    if "app_data" not in st.session_state:
        st.session_state["app_data"] = get_default_data()
    return st.session_state["app_data"]

def save_data(data):
    """Updates session state cache."""
    st.session_state["app_data"] = data

def add_log(data, message):
    """Appends a timestamped log entry to the in-memory log list."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_entry = f"[{timestamp}] {message}"
    data["log"].insert(0, log_entry)
    data["log"] = data["log"][:50]
