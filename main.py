"""
Player Window Stats - Solo Leveling System Interface
A gamified stat-tracker desktop app that syncs with your Habitica account.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date

import config
import data_store
import stats_engine
import milestones
from habitica_api import HabiticaClient, HabiticaError

APP_TITLE = "SYSTEM: PLAYER STATUS"

# ---- Palette (Solo Leveling System Interface Theme) ----------------
BG = "#030712"               # Deep obsidian void background
PANEL = "#0b0f19"            # Sleek dark slate glass panel fill
PANEL_ALT = "#111827"        # Alternate row / highlighted panel
ACCENT = "#00d2ff"           # Electric System Blue (Shadow Monarch Energy)
ACCENT_GLOW = "#38bdf8"      # Bright aura outline color
ACCENT_2 = "#6366f1"         # Arcane violet accent
GOLD = "#f59e0b"             # System Quest Gold / Rank S Aura
TEXT_MAIN = "#f8fafc"        # High-contrast crisp UI white
TEXT_DIM = "#64748b"         # Muted steel HUD grey
BORDER = "#1e293b"           # Sleek dark structural frame edge
DANGER = "#ef4444"           # System Penalty Red

# Stat colors updated for high-energy glowing HUD contrast
STAT_COLORS = {
    "Discipline": "#f43f5e",
    "Deep Focus": "#a855f7",
    "Activity": "#10b981",
    "Intelligence": "#3b82f6",
    "Hacking": "#f59e0b",
}


class HunterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=BG)

        # Launch Streamlit server background process automatically
        self._launch_streamlit_server()

        # Force fullscreen for 1920x1080 displays
        self._is_fullscreen = True
        try:
            self.attributes("-fullscreen", True)
        except tk.TclError:
            self.geometry("1920x1080")

        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)

        self.cfg = config.load_config()
        self.data = data_store.load_data()

        if "overall_level_offset" not in self.data:
            self.data["overall_level_offset"] = 0

        self.hp = float(self.data.get("hp", 50.0))
        self.max_hp = float(self.data.get("max_hp", 50.0))

        # Auto-sync state
        self._sync_in_progress = False
        self._auto_sync_remaining_s = self._auto_sync_interval_s()
        self._shutting_down = False

        self._ensure_credentials()
        self._build_ui()
        self._refresh_ui()
        self._trigger_sync(is_auto=True)
        self._start_auto_sync_heartbeat()

    def _launch_streamlit_server(self):
        """Starts Streamlit web server in a non-blocking background process."""
        app_path = os.path.join(os.path.dirname(__file__), "app.py")
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            app_path,
            "--server.headless=true",
            "--server.address=0.0.0.0",
            "--server.port=8501",
        ]
        subprocess.Popen(cmd)

    def _toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)

    def _exit_fullscreen(self, event=None):
        self._is_fullscreen = False
        self.attributes("-fullscreen", False)

    def _on_exit(self):
        self._shutting_down = True
        self.destroy()

    def _ensure_credentials(self):
        if self.cfg.get("habitica_user_id") and self.cfg.get("habitica_api_token"):
            return
        user_id = simpledialog.askstring("SYSTEM REGISTRATION", "ENTER PLAYER USER ID:", parent=self)
        api_token = simpledialog.askstring("SYSTEM REGISTRATION", "ENTER SYSTEM SECRET KEY:", parent=self, show="*")
        self.cfg["habitica_user_id"] = (user_id or "").strip()
        self.cfg["habitica_api_token"] = (api_token or "").strip()
        config.save_config(self.cfg)

    def _draw_bar(self, canvas, pct, fill_color, border_color=BORDER):
        """Draws a custom glowing progress bar on a Tkinter canvas."""
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1:
            w = 400
        if h <= 1:
            h = 12

        # Outer border line
        canvas.create_rectangle(0, 0, w - 1, h - 1, outline=border_color, width=1, fill="#070a12")
        
        # Inner active bar fill
        fill_w = max(0, int((w - 4) * (pct / 100.0)))
        if fill_w > 0:
            canvas.create_rectangle(2, 2, 2 + fill_w, h - 3, fill=fill_color, outline="")

    def _build_ui(self):
        font_family = "Segoe UI"
        title_font = (font_family, 24, "bold")
        subtitle_font = (font_family, 10, "bold")
        stat_font = (font_family, 12, "bold")
        small_font = (font_family, 10)
        tiny_font = (font_family, 9, "bold")

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=100, pady=25)

        # Header Section
        header = tk.Frame(content, bg=BG)
        header.pack(fill="x", pady=(0, 20))

        title_wrap = tk.Frame(header, bg=BG)
        title_wrap.pack(side="left")
        
        tk.Label(title_wrap, text="[ PLAYER STATS ]", font=title_font, fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(title_wrap, text="▲ PLAYER LINK: ACTIVE | MIND MONARCH INTERFACE", font=subtitle_font,
                 fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(2, 0))

        self.exit_btn = tk.Button(
            header, text="✕ DISCONNECT", command=self._on_exit,
            bg=PANEL, fg=DANGER, activebackground=DANGER, activeforeground=BG,
            font=("Segoe UI", 9, "bold"), relief="flat", padx=18, pady=6, cursor="hand2",
            bd=0, highlightthickness=1, highlightbackground=DANGER, highlightcolor=DANGER,
        )
        self.exit_btn.pack(side="right", anchor="n")

        self.nav_btn = tk.Button(
            header, text="📜 ABILITIES", command=self._toggle_page,
            bg=PANEL, fg=GOLD, activebackground=GOLD, activeforeground=BG,
            font=("Segoe UI", 9, "bold"), relief="flat", padx=18, pady=6, cursor="hand2",
            bd=0, highlightthickness=1, highlightbackground=GOLD, highlightcolor=GOLD,
        )
        self.nav_btn.pack(side="right", anchor="n", padx=(0, 10))

        # Player Rank / Overall Level Wrap
        level_wrap = tk.Frame(header, bg=BG)
        level_wrap.pack(side="right", padx=(0, 40))
        
        tk.Label(level_wrap, text="PLAYER RANK", font=tiny_font, fg=TEXT_DIM, bg=BG).pack(anchor="e")
        self.overall_label = tk.Label(
            level_wrap, text="LVL. 01", font=(font_family, 30, "bold"),
            fg=ACCENT, bg=BG
        )
        self.overall_label.pack(anchor="e")

        # Pulsing text color animation loop
        self._glow_step = 0
        self._glow_colors = [
            "#00d2ff", "#18daff", "#38bdf8", "#60a5fa",
            "#818cf8", "#60a5fa", "#38bdf8", "#18daff"
        ]
        self._animate_glow()

        # Page container: swaps between the main HUD page and the Abilities page
        self.page_container = tk.Frame(content, bg=BG)
        self.page_container.pack(fill="both", expand=True)

        self.hud_page = tk.Frame(self.page_container, bg=BG)
        self.hud_page.pack(fill="both", expand=True)

        self.abilities_page = tk.Frame(self.page_container, bg=BG)
        # Not packed yet - hidden until the player opens the Abilities page.

        self._current_page = "hud"

        # Health Bar Section
        hp_frame = tk.Frame(self.hud_page, bg=BG)
        hp_frame.pack(fill="x", pady=(0, 16))

        hp_top = tk.Frame(hp_frame, bg=BG)
        hp_top.pack(fill="x", pady=(0, 4))

        tk.Label(hp_top, text="[ HP ] VITALITY STATUS", font=("Segoe UI", 10, "bold"), fg=DANGER, bg=BG).pack(side="left")
        self.hp_val_lbl = tk.Label(hp_top, text="50.0 / 50.0", font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=BG)
        self.hp_val_lbl.pack(side="right")

        self.hp_canvas = tk.Canvas(hp_frame, height=12, bg=BG, bd=0, highlightthickness=0)
        self.hp_canvas.pack(fill="x")

        # System Controls Panel
        controls = tk.Frame(self.hud_page, bg=PANEL, highlightthickness=1,
                            highlightbackground=BORDER, highlightcolor=BORDER, padx=20, pady=10)
        controls.pack(fill="x", pady=(0, 18))

        self.status_lbl = tk.Label(controls, text="SYSTEM STANDBY", font=small_font, fg=TEXT_DIM, bg=PANEL)
        self.status_lbl.pack(side="left")

        self.auto_sync_btn = tk.Button(
            controls, text="AUTO-SYNC", command=self._toggle_auto_sync,
            bg=PANEL_ALT, fg=ACCENT, activebackground=ACCENT, activeforeground=BG,
            font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=6, cursor="hand2",
            bd=0, highlightthickness=1, highlightbackground=ACCENT, highlightcolor=ACCENT,
        )
        self.auto_sync_btn.pack(side="left", padx=(0, 12))

        self.auto_sync_status_lbl = tk.Label(controls, text="", font=tiny_font, fg=TEXT_DIM, bg=PANEL)
        self.auto_sync_status_lbl.pack(side="left")

        hint_lbl = tk.Label(controls, text="ESC: WINDOWED  |  F11: FULLSCREEN",
                             font=tiny_font, fg=TEXT_DIM, bg=PANEL)
        hint_lbl.pack(side="right")

        self._update_auto_sync_btn()

        # Player Stats Section
        self.stat_frame = tk.Frame(self.hud_page, bg=BG)
        self.stat_frame.pack(fill="x")

        self.stat_widgets = {}
        for stat in stats_engine.STATS:
            color = STAT_COLORS.get(stat, ACCENT)

            card = tk.Frame(self.stat_frame, bg=PANEL, highlightthickness=1,
                             highlightbackground=BORDER, highlightcolor=BORDER)
            card.pack(fill="x", pady=4)

            accent_strip = tk.Frame(card, bg=color, width=4)
            accent_strip.pack(side="left", fill="y")

            inner = tk.Frame(card, bg=PANEL, padx=16, pady=8)
            inner.pack(fill="x", side="left", expand=True)

            top = tk.Frame(inner, bg=PANEL)
            top.pack(fill="x", pady=(0, 4))

            left = tk.Frame(top, bg=PANEL)
            left.pack(side="left")
            tk.Label(left, text="◈", font=("Segoe UI", 10), fg=color, bg=PANEL).pack(side="left", padx=(0, 6))
            tk.Label(left, text=stat.upper(), font=stat_font, fg=TEXT_MAIN, bg=PANEL).pack(side="left")

            level_lbl = tk.Label(top, text="LVL. 01", font=stat_font, fg=color, bg=PANEL)
            level_lbl.pack(side="right")

            bar_canvas = tk.Canvas(inner, height=10, bg=PANEL, bd=0, highlightthickness=0)
            bar_canvas.pack(fill="x", pady=(2, 4))

            pct_lbl = tk.Label(inner, text="0% TO NEXT RANK", font=tiny_font, fg=TEXT_DIM, bg=PANEL)
            pct_lbl.pack(anchor="w")

            self.stat_widgets[stat] = {
                "level_lbl": level_lbl,
                "canvas": bar_canvas,
                "pct_lbl": pct_lbl,
                "color": color
            }

        # System Logs Section
        tk.Label(self.hud_page, text="[ SYSTEM LOG STREAM ]", font=("Segoe UI", 10, "bold"), fg=TEXT_DIM, bg=BG).pack(
            anchor="w", pady=(18, 6)
        )
        log_frame = tk.Frame(self.hud_page, bg=PANEL, highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=BORDER)
        log_frame.pack(fill="both", expand=True, pady=(0, 5))

        self.log_box = tk.Listbox(
            log_frame, bg=PANEL, fg=TEXT_MAIN, font=small_font,
            borderwidth=0, highlightthickness=0, selectbackground=PANEL_ALT,
            selectforeground=ACCENT, activestyle="none"
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=10)

        self._build_abilities_page()

    def _build_abilities_page(self):
        """Builds the Abilities page: for each stat, lists every milestone level
        with the real-life ability it unlocks. Unlocked milestones (current
        level >= milestone level) are highlighted; locked ones are dimmed.
        """
        page = self.abilities_page

        top = tk.Frame(page, bg=BG)
        top.pack(fill="x", pady=(0, 14))
        tk.Label(top, text="[ ABILITY LEDGER ]", font=("Segoe UI", 18, "bold"), fg=GOLD, bg=BG).pack(side="left")
        tk.Label(top, text="MILESTONE REWARDS EARNED THROUGH LEVELING", font=("Segoe UI", 10, "bold"),
                 fg=TEXT_DIM, bg=BG).pack(side="left", padx=(14, 0))

        back_btn = tk.Button(
            top, text="◀ BACK TO STATUS", command=self._toggle_page,
            bg=PANEL, fg=ACCENT, activebackground=ACCENT, activeforeground=BG,
            font=("Segoe UI", 9, "bold"), relief="flat", padx=16, pady=6, cursor="hand2",
            bd=0, highlightthickness=1, highlightbackground=ACCENT, highlightcolor=ACCENT,
        )
        back_btn.pack(side="right")

        # Scrollable area, since 5 stats x 7 milestones each is a lot of vertical content
        outer = tk.Frame(page, bg=BG, highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER)
        outer.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer, bg=BG, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        scroll_body = tk.Frame(scroll_canvas, bg=BG)
        body_window = scroll_canvas.create_window((0, 0), window=scroll_body, anchor="nw")

        def _on_body_configure(event):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_canvas_configure(event):
            scroll_canvas.itemconfig(body_window, width=event.width)

        scroll_body.bind("<Configure>", _on_body_configure)
        scroll_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            scroll_canvas.unbind_all("<MouseWheel>")

        # Only capture the scroll wheel while the cursor is actually over the
        # Abilities list, so it doesn't hijack scrolling on the main HUD page.
        scroll_canvas.bind("<Enter>", _bind_mousewheel)
        scroll_canvas.bind("<Leave>", _unbind_mousewheel)

        self.milestone_widgets = {}

        for stat in stats_engine.STATS:
            color = STAT_COLORS.get(stat, ACCENT)

            stat_card = tk.Frame(scroll_body, bg=PANEL, highlightthickness=1,
                                  highlightbackground=BORDER, highlightcolor=BORDER)
            stat_card.pack(fill="x", pady=6, padx=2)

            accent_strip = tk.Frame(stat_card, bg=color, width=4)
            accent_strip.pack(side="left", fill="y")

            inner = tk.Frame(stat_card, bg=PANEL, padx=16, pady=10)
            inner.pack(side="left", fill="both", expand=True)

            head = tk.Frame(inner, bg=PANEL)
            head.pack(fill="x", pady=(0, 8))
            tk.Label(head, text="◈", font=("Segoe UI", 12), fg=color, bg=PANEL).pack(side="left", padx=(0, 6))
            tk.Label(head, text=stat.upper(), font=("Segoe UI", 13, "bold"), fg=TEXT_MAIN, bg=PANEL).pack(side="left")
            stat_level_lbl = tk.Label(head, text="CURRENT LVL. 01", font=("Segoe UI", 10, "bold"), fg=color, bg=PANEL)
            stat_level_lbl.pack(side="right")

            rows = []
            for lvl, title, text in milestones.milestones_for(stat):
                row = tk.Frame(inner, bg=PANEL)
                row.pack(fill="x", pady=3)

                badge = tk.Label(row, text=f"LV {lvl}", font=("Segoe UI", 9, "bold"), fg=BG, bg=color,
                                  padx=8, pady=2)
                badge.pack(side="left", padx=(0, 10))

                text_wrap = tk.Frame(row, bg=PANEL)
                text_wrap.pack(side="left", fill="x", expand=True)

                title_lbl = tk.Label(text_wrap, text=title.upper(), font=("Segoe UI", 9, "bold"),
                                      fg=color, bg=PANEL, anchor="w")
                title_lbl.pack(fill="x", anchor="w")

                ability_lbl = tk.Label(
                    text_wrap, text=f"I will be able to {text}", font=("Segoe UI", 10),
                    fg=TEXT_MAIN, bg=PANEL, anchor="w", justify="left", wraplength=900
                )
                ability_lbl.pack(fill="x", anchor="w")

                lock_lbl = tk.Label(row, text="🔒", font=("Segoe UI", 11), fg=TEXT_DIM, bg=PANEL)
                lock_lbl.pack(side="right", padx=(10, 0))

                rows.append({
                    "level": lvl,
                    "badge": badge,
                    "title_lbl": title_lbl,
                    "ability_lbl": ability_lbl,
                    "lock_lbl": lock_lbl,
                })

            self.milestone_widgets[stat] = {
                "level_lbl": stat_level_lbl,
                "rows": rows,
                "color": color,
            }

        self._refresh_abilities_page()

    def _refresh_abilities_page(self):
        """Updates unlocked/locked styling on the Abilities page to match current levels."""
        if not hasattr(self, "milestone_widgets"):
            return
        for stat in stats_engine.STATS:
            current_level = self.data["stats"][stat]["level"]
            widgets = self.milestone_widgets[stat]
            widgets["level_lbl"].config(text=f"CURRENT LVL. {current_level:02d}")
            color = widgets["color"]

            for row in widgets["rows"]:
                unlocked = current_level >= row["level"]
                if unlocked:
                    row["title_lbl"].config(fg=color)
                    row["ability_lbl"].config(fg=TEXT_MAIN)
                    row["badge"].config(bg=color, fg=BG)
                    row["lock_lbl"].config(text="✓", fg=color)
                else:
                    row["title_lbl"].config(fg=TEXT_DIM)
                    row["ability_lbl"].config(fg=TEXT_DIM)
                    row["badge"].config(bg=PANEL_ALT, fg=TEXT_DIM)
                    row["lock_lbl"].config(text="🔒", fg=TEXT_DIM)

    def _toggle_page(self):
        """Swaps between the main HUD page and the Abilities page."""
        if self._current_page == "hud":
            self.hud_page.pack_forget()
            self._refresh_abilities_page()
            self.abilities_page.pack(fill="both", expand=True)
            self.nav_btn.config(text="🏠 STATUS")
            self._current_page = "abilities"
        else:
            self.abilities_page.pack_forget()
            self.hud_page.pack(fill="both", expand=True)
            self.nav_btn.config(text="📜 ABILITIES")
            self._current_page = "hud"

    def _animate_glow(self):
        """Creates a continuous blue aura pulsing effect on the main level text."""
        current_color = self._glow_colors[self._glow_step]
        self.overall_label.config(fg=current_color)
        
        self._glow_step = (self._glow_step + 1) % len(self._glow_colors)
        self.after(120, self._animate_glow)

    def _show_levelup_popup(self, title_text, level_text, color=ACCENT):
        """Displays a simplified System Notification modal window for Level Up events."""
        popup = tk.Toplevel(self)
        popup.title("SYSTEM NOTIFICATION")
        popup.configure(bg=BG)
        popup.geometry("380x180")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (380 // 2)
        y = (popup.winfo_screenheight() // 2) - (180 // 2)
        popup.geometry(f"380x180+{x}+{y}")

        card = tk.Frame(popup, bg=PANEL, highlightthickness=2, highlightbackground=color, highlightcolor=color)
        card.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(card, text=title_text.upper(), font=("Segoe UI", 16, "bold"), fg=GOLD, bg=PANEL).pack(pady=(20, 6))
        tk.Label(card, text=level_text.upper(), font=("Segoe UI", 12, "bold"), fg=TEXT_MAIN, bg=PANEL).pack(pady=(0, 18))

        btn = tk.Button(
            card, text="ACCEPT REWARD", command=popup.destroy,
            bg=color, fg=BG, activebackground=GOLD, activeforeground=BG,
            font=("Segoe UI", 10, "bold"), relief="flat", padx=24, pady=5, cursor="hand2", bd=0
        )
        btn.pack()

    def _refresh_ui(self):
        stats = self.data["stats"]
        
        # Check and process any level ups where progress reached or exceeded 1.0 (100%)
        for stat, entry in stats.items():
            entry["progress"] = round(entry["progress"], 6)
            while entry["progress"] >= 1.0:
                entry["level"] += 1
                entry["progress"] = round(entry["progress"] - 1.0, 6)

        base_overall = stats_engine.overall_level(stats)
        effective_overall = max(1, base_overall + self.data.get("overall_level_offset", 0))
        self.overall_label.config(text=f"LVL. {effective_overall:02d}")

        # Refresh custom rendered Canvas HP Bar
        hp_pct = (self.hp / self.max_hp * 100) if self.max_hp > 0 else 0
        self.hp_val_lbl.config(text=f"{self.hp:.1f} / {self.max_hp:.0f}")
        self.update_idletasks()
        self._draw_bar(self.hp_canvas, hp_pct, DANGER, BORDER)

        # Refresh custom rendered Stat Canvas Bars
        for stat in stats_engine.STATS:
            entry = stats[stat]
            widgets = self.stat_widgets[stat]
            widgets["level_lbl"].config(text=f"LVL. {entry['level']:02d}")
            pct = entry["progress"] * 100
            widgets["pct_lbl"].config(text=f"{pct:.0f}% TO NEXT RANK")
            self._draw_bar(widgets["canvas"], pct, widgets["color"], BORDER)

        if self.data.get("last_synced"):
            self.status_lbl.config(text=f"SYSTEM LINK OK · {self.data['last_synced']}")

        self.log_box.delete(0, tk.END)
        for entry in self.data["log"][:50]:
            self.log_box.insert(tk.END, " ▶ " + entry)

        self._refresh_abilities_page()

    def _apply_zero_health_penalty(self):
        """Applies penalties when health hits 0."""
        if "Discipline" in self.data["stats"]:
            disc = self.data["stats"]["Discipline"]
            if disc["level"] > 1:
                disc["level"] -= 1
            disc["progress"] = 0.0

        if "Deep Focus" in self.data["stats"]:
            df = self.data["stats"]["Deep Focus"]
            if df["level"] > 1:
                df["level"] -= 1
            df["progress"] = 0.0

        self.data["overall_level_offset"] = self.data.get("overall_level_offset", 0) - 1

        data_store.add_log(
            self.data,
            "⚠️ PENALTY ZONE ENFORCED! HP Depleted: Stats Regressed (-1 Level to Discipline & Deep Focus)."
        )

    def _sync_clicked(self):
        """Manual sync, triggered by the button. Shows errors via dialog."""
        self._trigger_sync(is_auto=False)

    def _trigger_sync(self, is_auto=False):
        """Starts a sync in the background, whether from a click or the auto-sync heartbeat.

        Guards against overlapping syncs: if one is already running (manual or
        auto), this call is a no-op rather than firing a second request.
        """
        if self._sync_in_progress:
            return

        if not self.cfg.get("habitica_user_id") or not self.cfg.get("habitica_api_token"):
            if not is_auto:
                messagebox.showerror(
                    "SYSTEM ERROR",
                    "Player credentials missing. Restart application to re-initialize."
                )
            return

        self._sync_in_progress = True
        self.status_lbl.config(
            text="AUTO-SYNC IN PROGRESS..." if is_auto else "ESTABLISHING SYSTEM CONNECTION..."
        )
        threading.Thread(target=self._sync_worker, args=(is_auto,), daemon=True).start()

    def _sync_worker(self, is_auto=False):
        try:
            level_ups = self._do_sync()
            self.after(0, self._sync_done, None, level_ups, is_auto)
        except HabiticaError as e:
            self.after(0, self._sync_done, str(e), [], is_auto)
        except Exception as e:
            self.after(0, self._sync_done, f"Unexpected system error: {e}", [], is_auto)

    def _sync_done(self, error, level_ups, is_auto=False):
        self._sync_in_progress = False
        if error:
            self.status_lbl.config(text="SYSTEM LINK FAILED")
            if is_auto:
                # Don't interrupt the player with a dialog for a background sync;
                # log it quietly instead and let them notice next manual sync.
                data_store.add_log(self.data, f"⚠️ Auto-sync failed: {error}")
                data_store.save_data(self.data)
                self._refresh_ui()
            else:
                messagebox.showerror("SYSTEM ERROR", error)
            return
        self._refresh_ui()

        for item in level_ups:
            if item["type"] == "stat":
                color = STAT_COLORS.get(item["stat"], ACCENT)
                self._show_levelup_popup(
                    f"{item['stat']} LEVELED UP!",
                    f"LEVEL {item['new_level']}",
                    color=color
                )
            elif item["type"] == "overall":
                self._show_levelup_popup(
                    "YOU LEVELED UP!",
                    f"LEVEL {item['new_level']}",
                    color=ACCENT
                )

    def _auto_sync_interval_s(self):
        """Auto-sync interval in seconds, from config (minimum 30s as a safety floor)."""
        return max(30, int(self.cfg.get("auto_sync_minutes", 5)) * 60)

    def _start_auto_sync_heartbeat(self):
        """Kicks off a single recursive self.after loop that ticks once per second.

        This runs for the lifetime of the window. It only ever touches Tkinter
        widgets from the main thread (via self.after), and only ever starts a
        background thread through _trigger_sync, which is itself overlap-safe.
        """
        self._auto_sync_tick()

    def _auto_sync_tick(self):
        if self._shutting_down:
            return

        if self.cfg.get("auto_sync_enabled", True):
            self._auto_sync_remaining_s -= 1
            if self._auto_sync_remaining_s <= 0:
                self._trigger_sync(is_auto=True)
                self._auto_sync_remaining_s = self._auto_sync_interval_s()
            mm, ss = divmod(max(0, self._auto_sync_remaining_s), 60)
            self.auto_sync_status_lbl.config(text=f"NEXT AUTO-SYNC: {mm:02d}:{ss:02d}")
        else:
            self.auto_sync_status_lbl.config(text="AUTO-SYNC PAUSED")

        self.after(1000, self._auto_sync_tick)

    def _toggle_auto_sync(self):
        enabled = not self.cfg.get("auto_sync_enabled", True)
        self.cfg["auto_sync_enabled"] = enabled
        config.save_config(self.cfg)
        if enabled:
            # Give the player the full interval before the next auto-sync fires,
            # rather than immediately syncing on re-enable.
            self._auto_sync_remaining_s = self._auto_sync_interval_s()
        self._update_auto_sync_btn()

    def _update_auto_sync_btn(self):
        enabled = self.cfg.get("auto_sync_enabled", True)
        self.auto_sync_btn.config(
            text=f"🔁 AUTO-SYNC: {'ON' if enabled else 'OFF'}",
            fg=ACCENT if enabled else TEXT_DIM,
            highlightbackground=ACCENT if enabled else BORDER,
        )

    def _do_sync(self):
        client = HabiticaClient(self.cfg["habitica_user_id"], self.cfg["habitica_api_token"])

        prev_overall = max(1, stats_engine.overall_level(self.data["stats"]) + self.data.get("overall_level_offset", 0))

        level_ups = []

        user_data = client.get_user()
        stats_data = user_data.get("stats", {})
        self.hp = float(stats_data.get("hp", 50))
        self.max_hp = float(stats_data.get("maxHP", 50))

        self.data["hp"] = self.hp
        self.data["max_hp"] = self.max_hp

        if self.hp <= 0:
            self._apply_zero_health_penalty()

        tags = client.get_tags()
        tag_id_to_name = {t["id"]: t["name"] for t in tags}

        habits = client.get_tasks("habits")
        dailies = client.get_tasks("dailys")
        
        active_todos = client.get_tasks("todos")
        completed_todos = client.get_tasks("completedTodos")
        todos = active_todos + completed_todos

        today_str = date.today().isoformat()

        # 1. PROCESS HABITS
        for task in habits:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            
            counter_up = task.get("counterUp", 0) or 0
            counter_down = task.get("counterDown", 0) or 0
            
            prev = self.data["tasks"].get(task_id, {"counterUp": 0, "counterDown": 0})
            prev_counter_up = prev.get("counterUp", 0)
            prev_counter_down = prev.get("counterDown", 0)

            new_up = counter_up - prev_counter_up if counter_up >= prev_counter_up else counter_up
            if new_up > 0:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty] * new_up
                levels = stats_engine.apply_progress(self.data["stats"], stat, increment, direction="up")
                if levels > 0:
                    level_ups.append({
                        "type": "stat",
                        "stat": stat,
                        "new_level": self.data["stats"][stat]["level"]
                    })
                data_store.add_log(
                    self.data,
                    f"Quest Action '{task.get('text','?')}' x{new_up} -> +{stat} EXP"
                    + (f" [LEVEL UP! {stat} is now Lv.{self.data['stats'][stat]['level']}]" if levels else ""),
                )

            new_down = counter_down - prev_counter_down if counter_down >= prev_counter_down else counter_down
            if new_down > 0:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty] * new_down
                levels = stats_engine.apply_progress(self.data["stats"], stat, increment, direction="down")
                data_store.add_log(
                    self.data,
                    f"Penalty Action '{task.get('text','?')}' x{new_down} -> -{stat} EXP"
                    + (f" [LEVEL DOWN! {stat} is now Lv.{self.data['stats'][stat]['level']}]" if levels < 0 else ""),
                )

            self.data["tasks"][task_id] = {"counterUp": counter_up, "counterDown": counter_down}

        # 2. PROCESS DAILIES
        for task in dailies:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            completed = bool(task.get("completed"))
            prev = self.data["tasks"].get(task_id, {})
            last_credited = prev.get("lastCreditedDate")
            if completed and last_credited != today_str:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty]
                levels = stats_engine.apply_progress(self.data["stats"], stat, increment, direction="up")
                if levels > 0:
                    level_ups.append({
                        "type": "stat",
                        "stat": stat,
                        "new_level": self.data["stats"][stat]["level"]
                    })
                data_store.add_log(
                    self.data,
                    f"Daily Quest '{task.get('text','?')}' cleared -> +{stat} EXP"
                    + (f" [LEVEL UP! {stat} is now Lv.{self.data['stats'][stat]['level']}]" if levels else ""),
                )
                prev["lastCreditedDate"] = today_str
            self.data["tasks"][task_id] = prev

        # 3. PROCESS TO-DOS
        for task in todos:
            stat = stats_engine.match_stat_from_tags(task.get("tags"), tag_id_to_name)
            if not stat:
                continue
            task_id = task["id"]
            completed = bool(task.get("completed"))
            prev = self.data["tasks"].get(task_id, {})
            already_credited = prev.get("credited", False)

            if completed and not already_credited:
                difficulty = stats_engine.priority_to_difficulty(task.get("priority", 1))
                increment = stats_engine.DIFFICULTY_INCREMENT[difficulty]
                levels = stats_engine.apply_progress(self.data["stats"], stat, increment, direction="up")
                if levels > 0:
                    level_ups.append({
                        "type": "stat",
                        "stat": stat,
                        "new_level": self.data["stats"][stat]["level"]
                    })
                data_store.add_log(
                    self.data,
                    f"Quest Objective '{task.get('text','?')}' cleared -> +{stat} EXP"
                    + (f" [LEVEL UP! {stat} is now Lv.{self.data['stats'][stat]['level']}]" if levels else ""),
                )
                prev["credited"] = True
            self.data["tasks"][task_id] = prev

        new_overall = max(1, stats_engine.overall_level(self.data["stats"]) + self.data.get("overall_level_offset", 0))
        if new_overall > prev_overall:
            level_ups.append({
                "type": "overall",
                "new_level": new_overall
            })

        self.data["last_synced"] = today_str
        data_store.save_data(self.data)

        summary = f"TELEMETRY OK · HP: {self.hp:.1f}/{self.max_hp:.0f} · {len(habits)} habits, {len(dailies)} dailies, {len(todos)} quests synced"
        self.after(0, lambda: self.status_lbl.config(text=summary))

        return level_ups


if __name__ == "__main__":
    app = HunterApp()
    app.mainloop()