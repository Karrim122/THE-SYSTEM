import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import date
import data_store
import stats_engine
import milestones
from habitica_api import HabiticaClient, HabiticaError
import config

st.set_page_config(
    page_title="SYSTEM: PLAYER STATUS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Styling
bg_color = config.THEME.get('backgroundColor', '#030712')
sec_bg = config.THEME.get('secondaryBackgroundColor', '#0b0f19')
text_color = config.THEME.get('textColor', '#f8fafc')
primary_color = config.THEME.get('primaryColor', '#00d2ff')
font_family = config.THEME.get('font', 'sans serif')

st.markdown(f"""
<style>
    body {{ background-color: {bg_color}; color: {text_color}; font-family: '{font_family}'; }}
    .stApp {{ background-color: {bg_color}; }}
    
    /* Hide Streamlit default sidebar completely */
    [data-testid="stSidebarNav"], [data-testid="collapsedControl"] {{ display: none !important; }}
    
    /* Small Control Buttons */
    div.stButton > button {{
        width: 100%;
        background-color: {sec_bg};
        color: {primary_color};
        border: 1px solid #1e293b;
        border-radius: 6px;
        font-weight: bold;
        font-size: 11px;
        letter-spacing: 0.5px;
        padding: 8px 6px;
        margin-bottom: 6px;
        transition: all 0.2s ease;
    }}
    div.stButton > button:hover {{
        border-color: {primary_color};
        box-shadow: 0 0 8px rgba(0, 210, 255, 0.3);
        color: #ffffff;
        background-color: #111827;
    }}
    div.stButton > button:active, div.stButton > button:focus {{
        background-color: #111827;
        border-color: {primary_color};
    }}

    .status-card {{
        background-color: {sec_bg};
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
    }}
    
    .hud-header {{ font-size: 24px; font-weight: bold; color: {primary_color}; letter-spacing: 1px; }}
    .sub-header {{ font-size: 11px; color: #64748b; font-weight: bold; margin-bottom: 15px; }}
    .level-badge {{ font-size: 42px; font-weight: 800; color: {primary_color}; text-shadow: 0 0 10px rgba(0, 210, 255, 0.4); }}
    .rank-text {{ font-size: 16px; font-weight: bold; color: #f59e0b; }}
    .stat-card {{ background-color: #111827; border-radius: 8px; padding: 14px; text-align: center; border: 1px solid #1e293b; transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }}
    
    /* Interactive Clickable Stat Card Container & Glow Animations */
    .stat-card-container {{
        position: relative;
        margin-bottom: 6px;
        cursor: pointer;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .stat-card-container:hover {{
        transform: translateY(-4px) scale(1.02);
    }}
    .stat-card-container:active {{
        transform: translateY(-1px) scale(0.98);
    }}

    div[class*="st-key-stat_card_"]:hover .stat-card-container {{
        transform: translateY(-4px) scale(1.02);
    }}
    div[class*="st-key-stat_card_"]:active .stat-card-container {{
        transform: translateY(-1px) scale(0.98);
    }}

    div[class*="st-key-stat_card_"]:hover .interactive-card-discipline .stat-card {{
        box-shadow: 0 8px 25px rgba(244, 63, 94, 0.35), 0 0 15px rgba(244, 63, 94, 0.3);
        border-color: #f43f5e;
    }}
    div[class*="st-key-stat_card_"]:hover .interactive-card-deep-focus .stat-card {{
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.35), 0 0 15px rgba(168, 85, 247, 0.3);
        border-color: #a855f7;
    }}
    div[class*="st-key-stat_card_"]:hover .interactive-card-activity .stat-card {{
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.35), 0 0 15px rgba(16, 185, 129, 0.3);
        border-color: #10b981;
    }}
    div[class*="st-key-stat_card_"]:hover .interactive-card-intelligence .stat-card {{
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.35), 0 0 15px rgba(59, 130, 246, 0.3);
        border-color: #3b82f6;
    }}
    div[class*="st-key-stat_card_"]:hover .interactive-card-hacking .stat-card {{
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.35), 0 0 15px rgba(245, 158, 11, 0.3);
        border-color: #f59e0b;
    }}

    /* Seamless Overlay Button (Makes the whole card clickable, with no visible extra button) */
    div[class*="st-key-stat_card_"] {{
        position: relative;
    }}
    div[class*="st-key-stat_card_"] div[data-testid="stButton"],
    div[class*="st-key-stat_card_"] div.stButton {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 10 !important;
    }}
    div[class*="st-key-stat_card_"] div[data-testid="stButton"] > button,
    div[class*="st-key-stat_card_"] div.stButton > button {{
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    /* Vertical Control Panel Divider */
    .right-panel-container {{
        border-left: 2px solid #1e293b;
        padding-left: 15px;
        margin-left: 5px;
        height: 100%;
    }}

    .metric-label {{ font-size: 11px; color: #64748b; font-weight: bold; letter-spacing: 0.5px; margin-bottom: 6px; text-transform: uppercase; }}
    .metric-val {{ font-size: 20px; color: {primary_color}; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

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

st_autorefresh(interval=300000, key="habitica_sync_heartbeat")

if "data" not in st.session_state:
    st.session_state.data = data_store.load_data()

if "last_sync_timestamp" not in st.session_state:
    st.session_state.last_sync_timestamp = 0

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "🏠 HUD"

if "selected_stat" not in st.session_state:
    st.session_state.selected_stat = "Discipline"

data = st.session_state.data

# Initialize Daily Gains Tracking
today_date_str = date.today().isoformat()
if "today_date" not in data or data.get("today_date") != today_date_str:
    data["today_date"] = today_date_str
    data["today_gains"] = {s: 0.0 for s in stats_engine.STATS}
elif "today_gains" not in data:
    data["today_gains"] = {s: 0.0 for s in stats_engine.STATS}

def execute_sync(force=False):
    current_time = time.time()
    if not force and (current_time - st.session_state.last_sync_timestamp < 300):
        return

    if not config.HABITICA_USER_ID or not config.HABITICA_API_TOKEN:
        st.error("Credentials missing in config.json")
        return

    try:
        client = HabiticaClient(config.HABITICA_USER_ID, config.HABITICA_API_TOKEN)
        user_data = client.get_user()
        stats_data = user_data.get("stats", {})
        data["hp"] = float(stats_data.get("hp", 50))
        data["max_hp"] = float(stats_data.get("maxHP", 50))

        tags = client.get_tags()
        tag_id_to_name = {t["id"]: t["name"] for t in tags}

        habits = client.get_tasks("habits")
        dailies = client.get_tasks("dailys")
        todos = client.get_tasks("todos") + client.get_tasks("completedTodos")

        today_str = date.today().isoformat()
        
        # Habits
        for task in habits:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            counter_up = task.get("counterUp", 0) or 0
            counter_down = task.get("counterDown", 0) or 0
            prev = data["tasks"].get(task_id, {"counterUp": 0, "counterDown": 0})

            new_up = max(0, counter_up - prev.get("counterUp", 0))
            if new_up > 0:
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))] * new_up
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                data["today_gains"][stat] = data.get("today_gains", {}).get(stat, 0.0) + inc
                data_store.add_log(data, f"Action '{task.get('text','?')}' x{new_up} -> +{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")

            new_down = max(0, counter_down - prev.get("counterDown", 0))
            if new_down > 0:
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))] * new_down
                stats_engine.apply_progress(data["stats"], stat, inc, direction="down")
                data["today_gains"][stat] = data.get("today_gains", {}).get(stat, 0.0) - inc
                data_store.add_log(data, f"Penalty '{task.get('text','?')}' x{new_down} -> -{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")

            data["tasks"][task_id] = {"counterUp": counter_up, "counterDown": counter_down}

        # Dailies
        for task in dailies:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            prev = data["tasks"].get(task_id, {})
            if task.get("completed") and prev.get("lastCreditedDate") != today_str:
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))]
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                data["today_gains"][stat] = data.get("today_gains", {}).get(stat, 0.0) + inc
                data_store.add_log(data, f"Daily '{task.get('text','?')}' cleared -> +{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")
                prev["lastCreditedDate"] = today_str
            data["tasks"][task_id] = prev

        # Todos
        for task in todos:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            prev = data["tasks"].get(task_id, {})
            if task.get("completed") and not prev.get("credited", False):
                inc = stats_engine.DIFFICULTY_INCREMENT[stats_engine.priority_to_difficulty(task.get("priority", 1))]
                stats_engine.apply_progress(data["stats"], stat, inc, direction="up")
                data["today_gains"][stat] = data.get("today_gains", {}).get(stat, 0.0) + inc
                data_store.add_log(data, f"Quest '{task.get('text','?')}' cleared -> +{STAT_DISPLAY_NAMES.get(stat, stat)} EXP")
                prev["credited"] = True
            data["tasks"][task_id] = prev

        data["last_synced"] = today_str
        data_store.save_data(data)
        st.session_state.last_sync_timestamp = current_time
        if force:
            st.toast("⚡ SYNCHRONIZED WITH HABITICA")
    except HabiticaError as e:
        st.error(f"Sync failed: {e}")

if config.HABITICA_USER_ID and config.HABITICA_API_TOKEN:
    execute_sync(force=False)

view_mode = st.session_state.view_mode

raw_level = stats_engine.overall_level(data["stats"]) + data.get("overall_level_offset", 0)
effective_overall = max(1, int(raw_level))

# --- Level Up Notification Logic ---
if "previous_overall_level" not in st.session_state:
    st.session_state.previous_overall_level = effective_overall
elif effective_overall > st.session_state.previous_overall_level:
    st.toast("🎉 You leveled up!", icon="⚡")
    st.session_state.previous_overall_level = effective_overall
# -----------------------------------

try:
    rank_title = milestones.get_rank_title(effective_overall)
except AttributeError:
    rank_title = "E RANK"

def render_stat_card(stat_name):
    entry = data["stats"][stat_name]
    color = STAT_COLORS.get(stat_name, "#00d2ff")
    stat_lvl = int(entry["level"])
    
    try:
        stat_rank = milestones.get_stat_rank(stat_name, stat_lvl)
    except AttributeError:
        stat_rank = f"{rank_title}"

    stat_class = f"interactive-card-{stat_name.lower().replace(' ', '-')}"
    card_key = f"stat_card_{stat_name.lower().replace(' ', '_')}"

    with st.container(key=card_key):
        st.markdown(f"""
        <div class="stat-card-container {stat_class}">
            <div class="stat-card" style="border-top: 3px solid {color};">
                <div style="color: {color}; font-weight: bold;">◈ {STAT_DISPLAY_NAMES.get(stat_name, stat_name).upper()}</div>
                <div style="font-size: 24px; font-weight: bold; color: {color};">LVL {stat_lvl:02d}</div>
                <div style="font-size: 10px; color: #64748b;">[{stat_rank}]</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("", key=f"click_card_{stat_name}", use_container_width=True):
            st.session_state.selected_stat = stat_name
            st.session_state.view_mode = "STAT_LEDGER"
            st.rerun()

    st.progress(min(1.0, max(0.0, float(entry["progress"]))))

if view_mode == "🏠 HUD":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="hud-header">[ PLAYER STATUS ]</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">▲ PLAYER LINK: ACTIVE | MIND MONARCH INTERFACE</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div style="text-align: right;"><span class="level-badge">LVL. {effective_overall:02d}</span><br><span class="rank-text">[{rank_title}]</span></div>',
            unsafe_allow_html=True
        )

    hp, max_hp = data.get("hp", 50.0), data.get("max_hp", 50.0)
    st.markdown(f"**[ HP ] VITALITY:** `{hp:.1f} / {max_hp:.0f}`")
    st.progress(max(0.0, min(1.0, hp / max_hp)) if max_hp > 0 else 0)
    st.markdown("---")

    # Main Grid Layout with Right Separator Column for Buttons
    main_grid, right_panel = st.columns([5.2, 0.8])

    with main_grid:
        # Row 1: Discipline, Deep Focus (narrowed using spacer columns)
        spacer_l1, r1_col1, r1_col2, spacer_r1 = st.columns([1, 2.5, 2.5, 1])
        with r1_col1:
            render_stat_card("Discipline")
        with r1_col2:
            render_stat_card("Deep Focus")

        # Row 2: Career (Hacking) in the middle (narrowed using spacer columns)
        spacer_l2, r2_col2, spacer_r2 = st.columns([2.25, 2.5, 2.25])
        with r2_col2:
            render_stat_card("Hacking")  # Displays as "Career"

        # Row 3: Intelligence, Physical (Activity) (narrowed using spacer columns)
        spacer_l3, r3_col1, r3_col2, spacer_r3 = st.columns([1, 2.5, 2.5, 1])
        with r3_col1:
            render_stat_card("Intelligence")
        with r3_col2:
            render_stat_card("Activity")  # Displays as "Physical"

    with right_panel:
        st.markdown('<div class="right-panel-container">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 10px; color: #64748b; font-weight: bold; margin-bottom: 8px; text-align: center;">SYSTEM</div>', unsafe_allow_html=True)

        if st.button("📊 STATS", use_container_width=True):
            st.session_state.view_mode = "📊 STATS"
            st.rerun()

        if st.button("🔄 SYNC", use_container_width=True):
            execute_sync(force=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

else:
    if view_mode == "STAT_LEDGER":
        selected_stat = st.session_state.get("selected_stat", "Discipline")
        stat_color = STAT_COLORS.get(selected_stat, primary_color)
        display_stat_name = STAT_DISPLAY_NAMES.get(selected_stat, selected_stat).upper()
        entry = data["stats"][selected_stat]
        curr_lvl = int(entry["level"])

        try:
            stat_rank = milestones.get_stat_rank(selected_stat, curr_lvl)
        except AttributeError:
            stat_rank = f"{rank_title}"

        col_back, col_blank = st.columns([1, 4])
        with col_back:
            if st.button("🔙 BACK TO HUD", use_container_width=True):
                st.session_state.view_mode = "🏠 HUD"
                st.rerun()

        st.markdown(f"""
        <div style="border-left: 4px solid {stat_color}; background-color: {sec_bg}; padding: 20px; border-radius: 8px; margin-top: 15px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); border-top: 1px solid #1e293b; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 11px; color: #64748b; font-weight: bold; letter-spacing: 1px;">SYSTEM // ABILITY LEDGER</div>
                    <div style="font-size: 28px; font-weight: 800; color: {stat_color}; letter-spacing: 1px; margin-top: 4px;">◈ {display_stat_name}</div>
                    <div style="font-size: 12px; color: #f59e0b; font-weight: bold; margin-top: 4px;">RANK: [{stat_rank}]</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 38px; font-weight: 800; color: {stat_color}; text-shadow: 0 0 12px {stat_color}60;">LVL {curr_lvl:02d}</div>
                    <div style="font-size: 11px; color: #94a3b8; font-weight: bold; margin-top: 2px;">EXP PROGRESS: {entry['progress']*100:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(1.0, max(0.0, float(entry["progress"]))))

        st.markdown('<div style="font-size: 13px; font-weight: bold; color: #64748b; letter-spacing: 1px; margin-top: 25px; margin-bottom: 15px; text-transform: uppercase;">ATTRIBUTE MILESTONES & CAPABILITIES</div>', unsafe_allow_html=True)

        try:
            m_list = milestones.milestones_for(selected_stat)
        except AttributeError:
            m_list = getattr(milestones, "MILESTONES", {}).get(selected_stat, [])

        if not m_list:
            st.info("No milestone records available for this stat.")
        else:
            for lvl, title, desc in m_list:
                unlocked = curr_lvl >= lvl
                status_icon = "⚡ UNLOCKED" if unlocked else "🔒 LOCKED"
                card_bg = "#111827" if unlocked else "#0b0f19"
                border_style = f"1px solid {stat_color}60" if unlocked else "1px solid #1e293b"
                title_color = text_color if unlocked else "#64748b"
                badge_bg = f"{stat_color}20" if unlocked else "#1e293b"
                badge_color = stat_color if unlocked else "#475569"

                st.markdown(f"""
                <div style="background-color: {card_bg}; border: {border_style}; border-radius: 8px; padding: 16px; margin-bottom: 12px; transition: all 0.2s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="background-color: {badge_bg}; color: {badge_color}; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">REQ: LVL {lvl:02d}</span>
                        <span style="font-size: 11px; font-weight: bold; color: {'#10b981' if unlocked else '#64748b'};">{status_icon}</span>
                    </div>
                    <div style="font-size: 16px; font-weight: bold; color: {title_color}; margin-bottom: 4px;">{title.upper()}</div>
                    <div style="font-size: 13px; color: {'#94a3b8' if unlocked else '#475569'}; line-height: 1.4;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

    elif view_mode == "📊 STATS":
        if st.button("🔙 BACK TO HUD"):
            st.session_state.view_mode = "🏠 HUD"
            st.rerun()

        st.markdown('<div class="hud-header" style="margin-bottom: 10px;">[ SYSTEM OVERVIEW ]</div>', unsafe_allow_html=True)

        # 2-column layout to prevent vertical scrolling
        stats_left, stats_right = st.columns([1, 1.2])

        with stats_left:
            st.markdown('<div style="font-size: 14px; font-weight: bold; color: #64748b; letter-spacing: 1px; margin-bottom: 10px;">ANALYTICS</div>', unsafe_allow_html=True)
            
            total_pts = sum(int(data["stats"][s]["level"]) for s in stats_engine.STATS)
            
            highest_stat = max(stats_engine.STATS, key=lambda s: data["stats"][s]["level"])
            highest_lvl = int(data["stats"][highest_stat]["level"])
            highest_display = STAT_DISPLAY_NAMES.get(highest_stat, highest_stat).upper()
            highest_color = STAT_COLORS.get(highest_stat, primary_color)
            
            lowest_stat = min(stats_engine.STATS, key=lambda s: data["stats"][s]["level"])
            lowest_lvl = int(data["stats"][lowest_stat]["level"])
            lowest_display = STAT_DISPLAY_NAMES.get(lowest_stat, lowest_stat).upper()
            lowest_color = STAT_COLORS.get(lowest_stat, primary_color)

            balance_ratio = (lowest_lvl / highest_lvl * 100.0) if highest_lvl > 0 else 100.0
            sync_date = data.get("last_synced", date.today().isoformat())

            # Compacted margin and padding for Analytics cards
            st.markdown(f"""
            <div class="status-card" style="padding: 10px; margin-bottom: 8px;">
                <div class="metric-label" style="margin-bottom: 2px;">TOTAL ATTRIBUTE POINTS</div>
                <div class="metric-val" style="font-size: 16px;">{total_pts} PTS</div>
            </div>
            <div class="status-card" style="padding: 10px; margin-bottom: 8px;">
                <div class="metric-label" style="margin-bottom: 2px;">HIGHEST ATTRIBUTE</div>
                <div class="metric-val" style="font-size: 16px; color: {highest_color};">{highest_display} (LVL {highest_lvl})</div>
            </div>
            <div class="status-card" style="padding: 10px; margin-bottom: 8px;">
                <div class="metric-label" style="margin-bottom: 2px;">LOWEST ATTRIBUTE</div>
                <div class="metric-val" style="font-size: 16px; color: {lowest_color};">{lowest_display} (LVL {lowest_lvl})</div>
            </div>
            <div class="status-card" style="padding: 10px; margin-bottom: 8px;">
                <div class="metric-label" style="margin-bottom: 2px;">ATTRIBUTE BALANCE RATIO</div>
                <div class="metric-val" style="font-size: 16px;">{balance_ratio:.1f}% CONVERGENCE</div>
            </div>
            <div class="status-card" style="padding: 10px; margin-bottom: 8px;">
                <div class="metric-label" style="margin-bottom: 2px;">SYSTEM SYNC DATE</div>
                <div class="metric-val" style="font-size: 16px;">{sync_date}</div>
            </div>
            """, unsafe_allow_html=True)

        with stats_right:
            st.markdown('<div style="font-size: 14px; font-weight: bold; color: #64748b; letter-spacing: 1px; margin-bottom: 10px;">DAILY EXP YIELD</div>', unsafe_allow_html=True)
            gains = data.get("today_gains", {})
            max_gain = max([gains.get(s, 0.0) for s in stats_engine.STATS] + [0.01])
            
            for stat in stats_engine.STATS:
                gain = gains.get(stat, 0.0)
                if gain < 0: 
                    gain = 0.0 
                color = STAT_COLORS.get(stat, primary_color)
                display = STAT_DISPLAY_NAMES.get(stat, stat).upper()
                pct = min(100, int((gain / max_gain) * 100))
                
                # Compacted Daily EXP bars
                st.markdown(f'''
                <div style="margin-bottom: 8px; background-color: {sec_bg}; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; color: {color}; margin-bottom: 4px;">
                        <span>◈ {display}</span>
                        <span>+{gain:.2f} EXP</span>
                    </div>
                    <div style="width: 100%; background-color: #111827; border-radius: 4px; height: 8px;">
                        <div style="width: {pct}%; background-color: {color}; height: 100%; border-radius: 4px; box-shadow: 0 0 6px {color}80;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
