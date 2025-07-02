# =============================================================================
# EssayReview.py – Var/Fal/Cam Teleport Spam Bot
# v40  • StatsTab.png  • Random tab-flips on idle rest
# =============================================================================
#  Hotkeys:  1 = pause/resume  •  2 = toggle console  •  3 = quit
# =============================================================================
import pygetwindow as gw
import pyautogui as pag
from pyautogui import ImageNotFoundException

try:
    import keyboard
except Exception:
    from types import SimpleNamespace

    keyboard = SimpleNamespace(is_pressed=lambda *_a, **_k: False)
import time
import random
import threading
import math
import os
import sys
import traceback
import ctypes
from datetime import datetime


PKG_DIR = os.path.dirname(__file__)
ROOT_DIR = getattr(
    sys, "_MEIPASS", os.path.abspath(os.path.join(PKG_DIR, os.pardir))
)
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")


ENABLE_OVERSHOOT = True
ENABLE_JITTER = True
ENABLE_VELOCITY_LIMIT = True
CHECK_FINAL_POS = True
LOG_CLICKS = True
DEBUG_LOGGING = False
ROBUST_CLICK = False
ENABLE_AFK = True
ENABLE_ANTIBAN = True
ENABLE_STATS_HOVER = True
ENABLE_BROWSER_AFK = True
ENABLE_TAB_FLIP = True
ENABLE_REST = True
SHORT_REST_TASK_PROB = 1.0


ENABLE_POST_MOVE_DRIFT = True
POST_MOVE_DRIFT_PROB = 0.50
ENABLE_PRE_CLICK_HOVER = True
PRE_CLICK_HOVER_PROB = 0.50
ENABLE_IDLE_WANDER = True
IDLE_WANDER_PROB = 0.50
ENABLE_WANDER_OFFSCREEN = True
WANDER_OFFSCREEN_PROB = 0.90


CONFIDENCE = 0.80
TELEPORT_CONFIDENCE = CONFIDENCE


# ─────────────────── Console visibility helpers ───────────────────
console_visible = True


def _console_hwnd():
    if os.name == "nt":
        return ctypes.windll.kernel32.GetConsoleWindow()
    return None


def hide_console():
    global console_visible
    hwnd = _console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        console_visible = False


def show_console():
    global console_visible
    hwnd = _console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 5)
        console_visible = True


def toggle_console():
    if console_visible:
        hide_console()
    else:
        show_console()


def debug(msg: str):
    if DEBUG_LOGGING:
        log(f"[DEBUG] {msg}")


def log(msg: str):
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"{stamp} {msg}", flush=True)


# ───────────────────── Config prompt ───────────────────────────────


def config_prompt():
    """Interactive window for teleport and feature settings."""
    if "PYTEST_CURRENT_TEST" in os.environ or (
        os.name != "nt" and not os.environ.get("DISPLAY")
    ):

        global choice
        choice = "Camelot"
        return choice

    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Bot Configuration")
    root.geometry(
        f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0"
    )
    # ---- dark mode colours ----
    bg = "#2b2b2b"
    fg = "#ffffff"
    root.configure(bg=bg)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TRadiobutton", background=bg, foreground=fg)
    style.configure("TCheckbutton", background=bg, foreground=fg)
    style.configure("TButton", background="#444444", foreground=fg)

    def _slider_colour(val: float) -> str:
        f = clamp(float(val) / 100, 0.0, 1.0)
        r = int(255 * (1 - f))
        g = int(255 * f)
        return f"#{r:02x}{g:02x}00"

    def _update_scale_colour(scale: tk.Scale, val: str) -> None:
        colour = _slider_colour(float(val))
        scale.config(troughcolor=colour, activebackground=colour)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    container = ttk.Frame(root)
    container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    container.columnconfigure(0, weight=1)
    container.columnconfigure(1, weight=1)

    left_frame = ttk.Frame(container)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    right_frame = ttk.Frame(container)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    tele_var = tk.StringVar(value="Camelot")
    tk.Label(left_frame, text="Select teleport:", bg=bg, fg=fg).pack(
        pady=(10, 0)
    )
    for opt in OPTIONS.keys():
        ttk.Radiobutton(
            left_frame, text=opt, value=opt, variable=tele_var
        ).pack()

    over_var = tk.BooleanVar(value=ENABLE_OVERSHOOT)
    jitter_var = tk.BooleanVar(value=ENABLE_JITTER)
    vel_var = tk.BooleanVar(value=ENABLE_VELOCITY_LIMIT)
    final_var = tk.BooleanVar(value=CHECK_FINAL_POS)
    log_var = tk.BooleanVar(value=LOG_CLICKS)
    debug_var = tk.BooleanVar(value=DEBUG_LOGGING)
    robust_var = tk.BooleanVar(value=ROBUST_CLICK)
    afk_var = tk.BooleanVar(value=ENABLE_AFK)
    antiban_var = tk.BooleanVar(value=ENABLE_ANTIBAN)
    stats_var = tk.BooleanVar(value=ENABLE_STATS_HOVER)
    browser_var = tk.BooleanVar(value=ENABLE_BROWSER_AFK)
    tabflip_var = tk.BooleanVar(value=ENABLE_TAB_FLIP)
    rest_var = tk.BooleanVar(value=ENABLE_REST)

    post_drift_var = tk.BooleanVar(value=ENABLE_POST_MOVE_DRIFT)
    post_drift_prob_var = tk.DoubleVar(value=POST_MOVE_DRIFT_PROB * 100)
    pre_hover_var = tk.BooleanVar(value=ENABLE_PRE_CLICK_HOVER)
    pre_hover_prob_var = tk.DoubleVar(value=PRE_CLICK_HOVER_PROB * 100)
    idle_wander_var = tk.BooleanVar(value=ENABLE_IDLE_WANDER)
    idle_wander_prob_var = tk.DoubleVar(value=IDLE_WANDER_PROB * 100)
    offscreen_var = tk.BooleanVar(value=ENABLE_WANDER_OFFSCREEN)
    offscreen_prob_var = tk.DoubleVar(value=WANDER_OFFSCREEN_PROB * 100)

    tk.Label(left_frame, text="Options:", bg=bg, fg=fg).pack(pady=(10, 0))

    options_frame = ttk.Frame(left_frame)
    options_frame.pack()
    _switch_pos = [0, 0]
    _switch_cols = 3
    for i in range(_switch_cols):
        options_frame.columnconfigure(i, weight=1)

    def add_switch(label_text: str, var: tk.BooleanVar) -> None:
        frame = ttk.Frame(options_frame)
        ttk.Label(frame, text=label_text).pack(side="left")
        btn_text = tk.StringVar(value="On" if var.get() else "Off")

        def _toggle() -> None:
            btn_text.set("On" if var.get() else "Off")

        tk.Checkbutton(
            frame,
            variable=var,
            textvariable=btn_text,
            indicatoron=False,
            width=4,
            command=_toggle,
            bg=bg,
            fg=fg,
            activebackground="#444444",
            activeforeground=fg,
            selectcolor=bg,
        ).pack(side="right", padx=(10, 0))
        frame.grid(
            row=_switch_pos[0],
            column=_switch_pos[1],
            sticky="w",
            padx=5,
            pady=2,
        )
        _switch_pos[1] += 1
        if _switch_pos[1] >= _switch_cols:
            _switch_pos[1] = 0
            _switch_pos[0] += 1

    move_frame = ttk.Frame(right_frame)
    move_frame.pack(pady=(10, 0))
    _move_pos = [0, 0]
    _move_cols = 2
    for i in range(_move_cols):
        move_frame.columnconfigure(i, weight=1)

    def add_move_setting(
        label_text: str, var: tk.BooleanVar, prob: tk.DoubleVar, info: str
    ) -> None:
        frame = ttk.Frame(move_frame)
        ttk.Label(frame, text=label_text).pack(side="left")
        btn_text = tk.StringVar(value="On" if var.get() else "Off")

        def _toggle() -> None:
            btn_text.set("On" if var.get() else "Off")

        tk.Checkbutton(
            frame,
            variable=var,
            textvariable=btn_text,
            indicatoron=False,
            width=4,
            command=_toggle,
            bg=bg,
            fg=fg,
            activebackground="#444444",
            activeforeground=fg,
            selectcolor=bg,
        ).pack(side="left", padx=(10, 0))
        ttk.Entry(frame, textvariable=prob, width=5).pack(
            side="left", padx=(10, 0)
        )
        ttk.Label(frame, text=info).pack(side="left", padx=(10, 0))
        frame.grid(
            row=_move_pos[0], column=_move_pos[1], sticky="w", padx=5, pady=2
        )
        _move_pos[1] += 1
        if _move_pos[1] >= _move_cols:
            _move_pos[1] = 0
            _move_pos[0] += 1

    add_switch("Mouse overshoot (aim past target)", over_var)
    add_switch("Mouse jitter (tiny wiggles)", jitter_var)
    add_switch("Velocity limit (slower speed changes)", vel_var)
    add_switch("Check final position (correct drift)", final_var)
    add_switch("Log clicks (print each one)", log_var)
    add_switch("Debug logging (verbose output)", debug_var)
    add_switch("Robust click (hold button slightly)", robust_var)
    add_switch("AFK breaks (random pauses)", afk_var)
    add_switch("Anti-ban extras (human-like mistakes)", antiban_var)
    add_switch("Hover stats during rests", stats_var)
    add_switch("Use Edge/YouTube during AFK", browser_var)
    add_switch("Random tab flips when idle", tabflip_var)
    add_switch("Rest between bursts", rest_var)

    tk.Label(
        right_frame, text="Human-Like Movement Settings:", bg=bg, fg=fg
    ).pack(pady=(10, 0))
    add_move_setting(
        "Post-move drift",
        post_drift_var,
        post_drift_prob_var,
        "Makes the mouse wiggle after moving",
    )
    add_move_setting(
        "Pre-click hover",
        pre_hover_var,
        pre_hover_prob_var,
        "Hovers near the target before clicking",
    )
    add_move_setting(
        "Idle wander",
        idle_wander_var,
        idle_wander_prob_var,
        "Subtle cursor movement while idle",
    )
    add_move_setting(
        "Off-screen wander",
        offscreen_var,
        offscreen_prob_var,
        "Moves off-screen briefly then returns",
    )

    tk.Label(left_frame, text="Teleport confidence:", bg=bg, fg=fg).pack(
        pady=(10, 0)
    )
    tele_conf_var = tk.DoubleVar(value=TELEPORT_CONFIDENCE)
    ttk.Entry(left_frame, textvariable=tele_conf_var, width=5).pack()

    tk.Label(
        right_frame,
        text="Micro AFK Chance: 0=never, 100=always",
        bg=bg,
        fg=fg,
    ).pack(pady=(10, 0))
    micro_afk_freq_var = tk.DoubleVar(value=MICRO_AFK_FREQ_LEVEL * 100)
    micro_afk_freq_desc = tk.Label(right_frame, bg=bg, fg=fg)
    micro_afk_freq_desc.pack()

    def _update_micro_desc(val: str) -> None:
        f = clamp(float(val) / 100, 0.0, 1.0)
        micro_afk_freq_desc.config(text=f"~{int(f * 100)}% chance per click")

    micro_afk_scale = tk.Scale(
        right_frame,
        variable=micro_afk_freq_var,
        from_=0,
        to=100,
        orient="horizontal",
        length=200,
        bg=bg,
        fg=fg,
        troughcolor=_slider_colour(micro_afk_freq_var.get()),
        highlightthickness=0,
        command=lambda v: (
            _update_micro_desc(v),
            _update_scale_colour(micro_afk_scale, v),
        ),
    )
    micro_afk_scale.pack()
    _update_scale_colour(micro_afk_scale, micro_afk_freq_var.get())
    _update_micro_desc(micro_afk_freq_var.get())

    tk.Label(
        right_frame,
        text="Mini-AFK Chance: 0=never, 100=always",
        bg=bg,
        fg=fg,
    ).pack(pady=(10, 0))
    mini_afk_freq_var = tk.DoubleVar(value=MINI_AFK_FREQ_LEVEL * 100)
    mini_afk_freq_desc = tk.Label(right_frame, bg=bg, fg=fg)
    mini_afk_freq_desc.pack()

    def _update_mini_afk_desc(val: str) -> None:
        f = clamp(float(val) / 100, 0.0, 1.0)
        spam_max = int((1 - f) * BASE_SPAM_MAX + f * HIGH_SPAM_MAX)
        rest_min = clamp((1 - f) * BASE_REST_MIN + f * HIGH_REST_MIN, 5.0, 11.0)
        rest_max = clamp((1 - f) * BASE_REST_MAX + f * HIGH_REST_MAX, 5.0, 11.0)
        avg_burst = int((BASE_SPAM_MIN + spam_max) / 2)
        avg_rest = (rest_min + rest_max) / 2
        mini_afk_freq_desc.config(
            text=f"~{avg_burst} teleports then {avg_rest:.1f}s rest"
        )

    mini_afk_scale = tk.Scale(
        right_frame,
        variable=mini_afk_freq_var,
        from_=0,
        to=100,
        orient="horizontal",
        length=200,
        bg=bg,
        fg=fg,
        troughcolor=_slider_colour(mini_afk_freq_var.get()),
        highlightthickness=0,
        command=lambda v: (
            _update_mini_afk_desc(v),
            _update_scale_colour(mini_afk_scale, v),
        ),
    )
    mini_afk_scale.pack()
    _update_scale_colour(mini_afk_scale, mini_afk_freq_var.get())
    _update_mini_afk_desc(mini_afk_freq_var.get())

    tk.Label(
        right_frame,
        text="Short AFK Chance: 0=never, 100=always",
        bg=bg,
        fg=fg,
    ).pack(pady=(10, 0))
    short_afk_freq_var = tk.DoubleVar(value=AFK_FREQ_LEVEL * 100)
    short_afk_freq_desc = tk.Label(right_frame, bg=bg, fg=fg)
    short_afk_freq_desc.pack()

    def _update_short_desc(val: str) -> None:
        f = clamp(float(val) / 100, 0.0, 1.0)
        smin = int((1 - f) * BASE_AFK_MIN_SECS + f * HIGH_AFK_MIN_SECS)
        smax = int((1 - f) * BASE_AFK_MAX_SECS + f * HIGH_AFK_MAX_SECS)
        avg = int((smin + smax) / 2 / 60)
        short_afk_freq_desc.config(text=f"about every {avg} mins")

    short_afk_scale = tk.Scale(
        right_frame,
        variable=short_afk_freq_var,
        from_=0,
        to=100,
        orient="horizontal",
        length=200,
        bg=bg,
        fg=fg,
        troughcolor=_slider_colour(short_afk_freq_var.get()),
        highlightthickness=0,
        command=lambda v: (
            _update_short_desc(v),
            _update_scale_colour(short_afk_scale, v),
        ),
    )
    short_afk_scale.pack()
    _update_scale_colour(short_afk_scale, short_afk_freq_var.get())
    _update_short_desc(short_afk_freq_var.get())

    tk.Label(
        right_frame,
        text="Long AFK Chance: 0=never, 100=always",
        bg=bg,
        fg=fg,
    ).pack(pady=(10, 0))
    long_afk_freq_var = tk.DoubleVar(value=LONG_AFK_FREQ_LEVEL * 100)
    long_afk_freq_desc = tk.Label(right_frame, bg=bg, fg=fg)
    long_afk_freq_desc.pack()

    def _update_long_desc(val: str) -> None:
        f = clamp(float(val) / 100, 0.0, 1.0)
        lmin = int(
            (1 - f) * BASE_LONG_AFK_MIN_SECS + f * HIGH_LONG_AFK_MIN_SECS
        )
        lmax = int(
            (1 - f) * BASE_LONG_AFK_MAX_SECS + f * HIGH_LONG_AFK_MAX_SECS
        )
        avg = (lmin + lmax) / 2
        if avg >= 3600:
            txt = f"about every {avg / 3600:.1f} hrs"
        else:
            txt = f"about every {int(avg / 60)} mins"
        long_afk_freq_desc.config(text=txt)

    long_afk_scale = tk.Scale(
        right_frame,
        variable=long_afk_freq_var,
        from_=0,
        to=100,
        orient="horizontal",
        length=200,
        bg=bg,
        fg=fg,
        troughcolor=_slider_colour(long_afk_freq_var.get()),
        highlightthickness=0,
        command=lambda v: (
            _update_long_desc(v),
            _update_scale_colour(long_afk_scale, v),
        ),
    )
    long_afk_scale.pack()
    _update_scale_colour(long_afk_scale, long_afk_freq_var.get())
    _update_long_desc(long_afk_freq_var.get())

    def _start():
        global ENABLE_OVERSHOOT, ENABLE_JITTER
        global ENABLE_VELOCITY_LIMIT, CHECK_FINAL_POS, LOG_CLICKS, ROBUST_CLICK
        global ENABLE_AFK, ENABLE_ANTIBAN
        global ENABLE_STATS_HOVER, ENABLE_BROWSER_AFK, ENABLE_TAB_FLIP, choice
        global ENABLE_REST, TELEPORT_CONFIDENCE, DEBUG_LOGGING
        global AFK_FREQ_LEVEL, MINI_AFK_FREQ_LEVEL, LONG_AFK_FREQ_LEVEL
        global MICRO_AFK_FREQ_LEVEL
        global ENABLE_POST_MOVE_DRIFT, POST_MOVE_DRIFT_PROB
        global ENABLE_PRE_CLICK_HOVER, PRE_CLICK_HOVER_PROB
        global ENABLE_IDLE_WANDER, IDLE_WANDER_PROB
        global ENABLE_WANDER_OFFSCREEN, WANDER_OFFSCREEN_PROB
        ENABLE_OVERSHOOT = over_var.get()
        ENABLE_JITTER = jitter_var.get()
        ENABLE_VELOCITY_LIMIT = vel_var.get()
        CHECK_FINAL_POS = final_var.get()
        LOG_CLICKS = log_var.get()
        DEBUG_LOGGING = debug_var.get()
        ROBUST_CLICK = robust_var.get()
        ENABLE_AFK = afk_var.get()
        ENABLE_ANTIBAN = antiban_var.get()
        ENABLE_STATS_HOVER = stats_var.get()
        ENABLE_BROWSER_AFK = browser_var.get()
        ENABLE_TAB_FLIP = tabflip_var.get()
        ENABLE_REST = rest_var.get()
        try:
            TELEPORT_CONFIDENCE = max(
                0.0, min(1.0, float(tele_conf_var.get()))
            )
        except Exception:
            TELEPORT_CONFIDENCE = CONFIDENCE
        try:
            MICRO_AFK_FREQ_LEVEL = clamp(
                float(micro_afk_freq_var.get()) / 100, 0.0, 1.0
            )
        except Exception:
            MICRO_AFK_FREQ_LEVEL = 0.0
        try:
            MINI_AFK_FREQ_LEVEL = clamp(
                float(mini_afk_freq_var.get()) / 100, 0.0, 1.0
            )
        except Exception:
            MINI_AFK_FREQ_LEVEL = 0.0
        try:
            AFK_FREQ_LEVEL = clamp(
                float(short_afk_freq_var.get()) / 100, 0.0, 1.0
            )
        except Exception:
            AFK_FREQ_LEVEL = 0.0
        try:
            LONG_AFK_FREQ_LEVEL = clamp(
                float(long_afk_freq_var.get()) / 100, 0.0, 1.0
            )
        except Exception:
            LONG_AFK_FREQ_LEVEL = 0.0
        ENABLE_POST_MOVE_DRIFT = post_drift_var.get()
        ENABLE_PRE_CLICK_HOVER = pre_hover_var.get()
        ENABLE_IDLE_WANDER = idle_wander_var.get()
        ENABLE_WANDER_OFFSCREEN = offscreen_var.get()
        try:
            POST_MOVE_DRIFT_PROB = max(
                0.0, min(1.0, float(post_drift_prob_var.get()) / 100)
            )
        except Exception:
            POST_MOVE_DRIFT_PROB = 0.50
        try:
            PRE_CLICK_HOVER_PROB = max(
                0.0, min(1.0, float(pre_hover_prob_var.get()) / 100)
            )
        except Exception:
            PRE_CLICK_HOVER_PROB = 0.50
        try:
            IDLE_WANDER_PROB = max(
                0.0, min(1.0, float(idle_wander_prob_var.get()) / 100)
            )
        except Exception:
            IDLE_WANDER_PROB = 0.50
        try:
            WANDER_OFFSCREEN_PROB = max(
                0.0, min(1.0, float(offscreen_prob_var.get()) / 100)
            )
        except Exception:
            WANDER_OFFSCREEN_PROB = 0.90
        choice = tele_var.get()
        update_afk_settings()
        root.destroy()

    ttk.Button(root, text="Start", command=_start).grid(
        row=1, column=0, pady=10
    )
    root.protocol(
        "WM_DELETE_WINDOW", lambda: sys.exit("No teleport selected – exiting.")
    )
    root.mainloop()
    return choice


# ───────────────── AFK frequency helper ───────────────────────────


def update_afk_settings() -> None:
    """Update AFK-related timing based on frequency sliders."""
    global SPAM_MIN, SPAM_MAX, REST_MIN, REST_MAX
    global AFK_MIN_SECS, AFK_MAX_SECS
    global LONG_AFK_MIN_SECS, LONG_AFK_MAX_SECS

    f_rest = clamp(MINI_AFK_FREQ_LEVEL, 0.0, 1.0)
    f_short = clamp(AFK_FREQ_LEVEL, 0.0, 1.0)
    f_long = clamp(LONG_AFK_FREQ_LEVEL, 0.0, 1.0)

    SPAM_MIN = BASE_SPAM_MIN
    SPAM_MAX = int((1 - f_rest) * BASE_SPAM_MAX + f_rest * HIGH_SPAM_MAX)

    REST_MIN = clamp(
        (1 - f_rest) * BASE_REST_MIN + f_rest * HIGH_REST_MIN,
        5.0,
        11.0,
    )
    REST_MAX = clamp(
        (1 - f_rest) * BASE_REST_MAX + f_rest * HIGH_REST_MAX,
        5.0,
        11.0,
    )

    AFK_MIN_SECS = int(
        (1 - f_short) * BASE_AFK_MIN_SECS + f_short * HIGH_AFK_MIN_SECS
    )
    AFK_MAX_SECS = int(
        (1 - f_short) * BASE_AFK_MAX_SECS + f_short * HIGH_AFK_MAX_SECS
    )

    LONG_AFK_MIN_SECS = int(
        (1 - f_long) * BASE_LONG_AFK_MIN_SECS + f_long * HIGH_LONG_AFK_MIN_SECS
    )
    LONG_AFK_MAX_SECS = int(
        (1 - f_long) * BASE_LONG_AFK_MAX_SECS + f_long * HIGH_LONG_AFK_MAX_SECS
    )


# ───────────────────── PyAutoGUI tweaks ────────────────────────────
pag.FAILSAFE = False
pag.PAUSE = 0


# ─────────────────── Safe locate wrapper ───────────────────────────


def safe_locate(img, **kw):
    try:
        loc = pag.locateOnScreen(img, **kw)
        if loc:
            debug(f"Located {os.path.basename(img)} at {loc}")
        else:
            debug(f"Image {os.path.basename(img)} not found")
        return loc
    except (ImageNotFoundException, ValueError, OSError) as e:
        debug(f"Locate failed for {os.path.basename(img)}: {e}")
        return None


# ───────────────────── Image assets ────────────────────────────────
STATS_IMAGE = os.path.join(ASSETS_DIR, "StatsTab.png")
MAGICLVL_IMAGE = os.path.join(ASSETS_DIR, "MagicLvl.png")
MAGIC_TAB_IMAGE = os.path.join(ASSETS_DIR, "MagicTab.png")
MAGIC_OPEN_IMAGE = os.path.join(ASSETS_DIR, "MagicTabOpen.png")
PLAY_NOW_IMAGE = os.path.join(ASSETS_DIR, "PlayNow.png")
CLICK_TO_PLAY_IMAGE = os.path.join(ASSETS_DIR, "ClickHereToPlay.png")

TAB_IMAGES = [
    os.path.join(ASSETS_DIR, "CombatTab.png"),
    os.path.join(ASSETS_DIR, "EmojiTab.png"),
    os.path.join(ASSETS_DIR, "FriendsListTab.png"),
    os.path.join(ASSETS_DIR, "PrayerTab.png"),
    os.path.join(ASSETS_DIR, "QuestTab.png"),
    os.path.join(ASSETS_DIR, "MusicTab.png"),
    os.path.join(ASSETS_DIR, "SettingsTab.png"),
    os.path.join(ASSETS_DIR, "LogOutTab.png"),
]

# ───────────────── Confidence levels ───────────────────────────────
STATS_CONFIDENCE = 0.80
OPEN_CONFIDENCE = 0.85

MAGIC_TAB_CONFIDENCE = 0.80

# ───────────────── Behaviour constants ────────────────────────────

BASE_SPAM_MIN, BASE_SPAM_MAX = 1, 140
BASE_REST_MIN, BASE_REST_MAX = 1, 40
BASE_AFK_MIN_SECS, BASE_AFK_MAX_SECS = 30 * 60, 45 * 60
BASE_LONG_AFK_MIN_SECS, BASE_LONG_AFK_MAX_SECS = 2 * 60 * 60, 3 * 60 * 60

HIGH_SPAM_MAX = 20
HIGH_REST_MIN, HIGH_REST_MAX = 5, 120
HIGH_AFK_MIN_SECS, HIGH_AFK_MAX_SECS = 5 * 60, 15 * 60
HIGH_LONG_AFK_MIN_SECS, HIGH_LONG_AFK_MAX_SECS = 40 * 60, 80 * 60

MINI_AFK_FREQ_LEVEL = 0.5
MICRO_AFK_FREQ_LEVEL = 0.5
AFK_FREQ_LEVEL = 0.5
LONG_AFK_FREQ_LEVEL = 0.5

SPAM_MIN, SPAM_MAX = BASE_SPAM_MIN, BASE_SPAM_MAX
REST_MIN, REST_MAX = BASE_REST_MIN, BASE_REST_MAX
CLICK_MIN_GAP, CLICK_MAX_GAP = 0.06, 1.00


CLICK_HOLD_MIN, CLICK_HOLD_MAX = 0.010, 0.060
AFK_MIN_SECS, AFK_MAX_SECS = BASE_AFK_MIN_SECS, BASE_AFK_MAX_SECS
LONG_AFK_MIN_SECS, LONG_AFK_MAX_SECS = (
    BASE_LONG_AFK_MIN_SECS,
    BASE_LONG_AFK_MAX_SECS,
)
SEGMENT_MIN, SEGMENT_MAX = 3, 6


OVERSHOOT_MIN, OVERSHOOT_MAX = 4, 8
LOOP_MEAN, LOOP_SD = 10, 2

MAX_ACCEL = 8000
SMOOTH_STOP_DIST = 40

STATS_REST_PROB = 0.10
STATS_REST_TEST_MODE = False
TWEEN_FUNCS = [
    pag.easeInQuad,
    pag.easeOutQuad,
    pag.easeInOutQuad,
    pag.easeInCubic,
    pag.easeOutCubic,
    pag.easeInOutCubic,
]


JITTER_PROB = 0.1
JITTER_PIXELS = 1
JITTER_DIST_THRESHOLD = 100
JITTER_PAUSE_MIN, JITTER_PAUSE_MAX = 0.003, 0.010


LOGIN_RETRY_SECS = 180

# ───────────────── Runtime state ───────────────────────────────────
bot_active = True
loop_counter = 0
next_weight_refresh = 0
next_short_afk_time = 0
next_long_afk_time = 0
anti_ban_weights = {}
overshoot_chance = 0.30
last_move_velocities: list[float] = []
teleport_last_seen = time.time()
last_login_attempt = 0.0


in_spam_session = False

# ───────────────── Maths helpers ───────────────────────────────────


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def gaussian_between(lo, hi, m=None, s=None):
    if m is None:
        m = (lo + hi) / 2
    if s is None:
        s = (hi - lo) / 6
    return clamp(random.gauss(m, s), lo, hi)


def gamma_between(lo, hi, k=2.0):
    theta = ((lo + hi) / 2) / k
    return clamp(random.gammavariate(k, theta), lo, hi)


def lognorm_between(lo, hi, mu=None, sigma=0.4):
    mu = math.log((lo + hi) / 2) if mu is None else mu
    return clamp(random.lognormvariate(mu, sigma), lo, hi)


class PinkNoise:
    def __init__(self, a=0.8):
        self.a, self.p = a, 0

    def next(self, s=3):
        self.p = self.a * self.p + (1 - self.a) * random.uniform(-1, 1)
        return int(self.p * s)


pink = PinkNoise()

# ─────────────────── Teleport selection prompt ─────────────────────
OPTIONS = {
    "Varrock": os.path.join(ASSETS_DIR, "Var.png"),
    "Falador": os.path.join(ASSETS_DIR, "Fal.png"),
    "Camelot": os.path.join(ASSETS_DIR, "Cam.png"),
}

choice = None
config_prompt()
if choice is None:
    sys.exit("No teleport selected – exiting.")
TELEPORT_IMAGE = OPTIONS[choice]

# ───────────────── Anti-ban weights ────────────────────────────────
# ───────────────── Anti-ban weights ────────────────────────────────


def refresh_weights():
    global anti_ban_weights, overshoot_chance
    global next_short_afk_time, next_long_afk_time
    anti_ban_weights = {
        "drift_click_timing": clamp(random.gauss(0.5, 0.2), 0.1, 0.9),
        "idle_wiggle": clamp(random.gauss(0.4, 0.15), 0.05, 0.8),
        "double_click": clamp(random.gauss(0.2, 0.1), 0, 0.5),
        "finger_hesitation": clamp(random.gauss(0.25, 0.1), 0, 0.6),
    }
    overshoot_chance = clamp(random.gauss(0.3, 0.08), 0.1, 0.5)
    if ENABLE_AFK:
        next_short_afk_time = time.time() + gamma_between(
            AFK_MIN_SECS, AFK_MAX_SECS, 2.4
        )
        next_long_afk_time = time.time() + gamma_between(
            LONG_AFK_MIN_SECS, LONG_AFK_MAX_SECS, 2.4
        )
    else:
        next_short_afk_time = float("inf")
        next_long_afk_time = float("inf")
    log("Anti-ban settings updated.")


def feature(k):
    if not ENABLE_ANTIBAN:
        return False
    return random.random() < anti_ban_weights.get(k, 0)


# ───────────────── Outlier events (rarer ×10) ─────────────────────


def maybe_outlier_event(ctx: str):
    if not ENABLE_ANTIBAN:
        return
    odds = {"burst": 0.0006, "rest": 0.0008, "afk": 0.0010}
    if random.random() > odds.get(ctx, 0.0006):
        return
    event = random.choice(
        ["corner_drift", "off_click", "scroll_spam", "camera_circle"]
    )
    log(f"⚠️ Outlier event: {event} during {ctx}")
    if event == "corner_drift":
        start = pag.position()
        bezier_move(5, 5)
        time.sleep(random.uniform(0.3, 0.8))
        bezier_move(*start)
    elif event == "off_click":
        loc = safe_locate(
            TELEPORT_IMAGE, confidence=TELEPORT_CONFIDENCE, grayscale=True
        )
        if loc:
            x, y = pag.center(loc)
            dx = random.randint(25, 80) * random.choice([-1, 1])
            dy = random.randint(25, 80) * random.choice([-1, 1])
            bezier_move(x + dx, y + dy)
            pag.click()
            time.sleep(0.3)
    elif event == "scroll_spam":
        cx, cy = pag.position()
        for _ in range(random.randint(3, 7)):
            off_x = random.randint(-20, 20)
            off_y = random.randint(-20, 20)
            bezier_move(cx + off_x, cy + off_y)
            pag.scroll(random.randint(-300, 300))
            time.sleep(random.uniform(0.08, 0.18))
    elif event == "camera_circle":
        cx, cy = pag.position()
        r = random.randint(20, 40)
        for a in range(0, 360, 45):
            tx = cx + int(r * math.cos(math.radians(a)))
            ty = cy + int(r * math.sin(math.radians(a)))
            bezier_move(tx, ty)


# ───────────────── Mouse helpers (Fitts+Bézier) ───────────────────


def _smooth_path(points: list[tuple[int, int]], radius: int = 2):
    """Apply a simple moving average to smooth angle changes."""
    if radius <= 0 or len(points) < 3:
        return points
    smoothed: list[tuple[int, int]] = []
    n = len(points)
    for i in range(n):
        s0 = max(0, i - radius)
        s1 = min(n, i + radius + 1)
        xs = [p[0] for p in points[s0:s1]]
        ys = [p[1] for p in points[s0:s1]]
        smoothed.append((int(sum(xs) / len(xs)), int(sum(ys) / len(ys))))
    smoothed[0] = points[0]
    smoothed[-1] = points[-1]
    return smoothed


def _curve(st, en):
    sx, sy = st
    ex, ey = en
    pts, segs = [], random.randint(SEGMENT_MIN, SEGMENT_MAX)
    for i in range(1, segs):
        t = i / segs
        off = random.randint(-15, 15)
        cx = sx + (ex - sx) * t + off
        cy = sy + (ey - sy) * t + off
        pts.append((int((1 - t) * sx + t * cx), int((1 - t) * sy + t * cy)))
    pts.append((ex, ey))
    pts = _smooth_path(pts)
    return pts


def fitts_time(d, w, a=0.05, b=0.05):
    return a + b * math.log2(1 + d / w)


def bezier_move(tx, ty, *, jitter_prob=None, jitter_px=None):
    cx, cy = pag.position()
    dist = math.hypot(tx - cx, ty - cy)
    debug(f"bezier_move start {(cx, cy)} -> {(tx, ty)} dist {dist:.1f}")
    if jitter_prob is None:
        jitter_prob = JITTER_PROB
    if jitter_px is None:
        jitter_px = JITTER_PIXELS

    use_over = (
        ENABLE_OVERSHOOT
        and random.random() < overshoot_chance
        and dist > 30
        and dist > 20
    )
    if use_over:
        debug(f"Overshoot move to ({tx}, {ty}) distance {dist:.1f}")
        max_over = clamp(dist * 0.15, OVERSHOOT_MIN, OVERSHOOT_MAX)
        dx = random.choice([-1, 1]) * random.uniform(OVERSHOOT_MIN, max_over)
        dy = random.choice([-1, 1]) * random.uniform(OVERSHOOT_MIN, max_over)
        path = _curve((cx, cy), (tx + dx, ty + dy)) + _curve(
            (tx + dx, ty + dy), (tx, ty)
        )
    else:
        path = _curve((cx, cy), (tx, ty))
    path = _smooth_path(path)
    W = random.uniform(32, 48)
    seg_lens = [
        math.hypot(px - sx, py - sy)
        for (sx, sy), (px, py) in zip(path[:-1], path[1:])
    ]
    total = sum(seg_lens) or 1
    T = fitts_time(
        total, W, a=random.uniform(0.04, 0.06), b=random.uniform(0.04, 0.07)
    )

    T *= random.uniform(1.6, 2.4)

    def _sig(t: float, k: float = 8.0) -> float:
        start = 1 / (1 + math.exp(k / 2))
        end = 1 / (1 + math.exp(-k / 2))
        y = 1 / (1 + math.exp(-k * (t - 0.5)))
        return (y - start) / (end - start)

    cum = 0.0
    times = [0.0]
    for seg in seg_lens:
        cum += seg
        times.append(_sig(cum / total) * T)
    debug(f"total move time {T:.3f}s over {len(seg_lens)} segments")

    global last_move_velocities
    last_move_velocities = []
    prev_v = 0.0
    dist_done = 0.0
    for (px, py), seg_len, t0, t1 in zip(
        path[1:], seg_lens, times[:-1], times[1:]
    ):
        remaining = total - dist_done
        seg_T = (t1 - t0) * random.uniform(0.9, 1.1)
        seg_T = clamp(seg_T, 0.01, 0.90)
        v = seg_len / seg_T
        if ENABLE_VELOCITY_LIMIT and abs(v - prev_v) / seg_T > MAX_ACCEL:
            if v > prev_v:
                seg_T = max(
                    seg_T,
                    (-prev_v + math.sqrt(prev_v**2 + 4 * MAX_ACCEL * seg_len))
                    / (2 * MAX_ACCEL),
                )
            else:
                disc = prev_v**2 - 4 * MAX_ACCEL * seg_len
                if disc > 0 and prev_v > 0:
                    seg_T = max(
                        seg_T, (prev_v + math.sqrt(disc)) / (2 * MAX_ACCEL)
                    )
                elif prev_v > 0:
                    seg_T = max(seg_T, seg_len / prev_v)
                else:
                    seg_T = max(seg_T, math.sqrt(seg_len / MAX_ACCEL))
            seg_T = clamp(seg_T, 0.01, 0.90)
            v = seg_len / seg_T
        if remaining < SMOOTH_STOP_DIST and prev_v > 0:
            allowed_v = prev_v * max(remaining / SMOOTH_STOP_DIST, 0.1)
            if v > allowed_v:
                v = allowed_v
                seg_T = seg_len / v
                seg_T = clamp(seg_T, 0.01, 0.90)
                v = seg_len / seg_T
        last_move_velocities.append(v)
        debug(f"seg to {(px, py)} len={seg_len:.1f} T={seg_T:.3f} v={v:.1f}")
        pag.moveTo(px, py, duration=seg_T, tween=random.choice(TWEEN_FUNCS))
        if (
            ENABLE_JITTER
            and dist > JITTER_DIST_THRESHOLD
            and random.random() < jitter_prob
        ):
            jx = random.choice([-1, 1]) * jitter_px
            jy = random.choice([-1, 1]) * jitter_px
            pag.moveRel(jx, jy)
            time.sleep(random.uniform(JITTER_PAUSE_MIN, JITTER_PAUSE_MAX))
            pag.moveRel(-jx, -jy)
        prev_v = v
        dist_done += seg_len

    pag.moveTo(tx, ty)
    debug(f"move complete at {pag.position()}")


def idle_wiggle():
    x, y = pag.position()
    pag.moveTo(
        x + pink.next(), y + pink.next(), duration=random.uniform(0.02, 0.05)
    )


# ───────────────── Human-like extras ──────────────────────────────


def post_move_drift():
    """Slight cursor drift after a move."""
    if not ENABLE_POST_MOVE_DRIFT:
        return
    if in_spam_session or random.random() >= POST_MOVE_DRIFT_PROB:
        return
    dx = int(random.gauss(0, 2))
    dy = int(random.gauss(0, 2))
    pag.moveRel(dx, dy, duration=gaussian_between(0.02, 0.15))


def pre_click_hover(tx=None, ty=None):
    """Briefly hover near the target before clicking."""
    if not ENABLE_PRE_CLICK_HOVER:
        return
    if in_spam_session or random.random() >= PRE_CLICK_HOVER_PROB:
        return
    if tx is None or ty is None:
        tx, ty = pag.position()
    hx = int(tx + random.gauss(0, 5))
    hy = int(ty + random.gauss(0, 5))
    pag.moveTo(hx, hy, duration=gaussian_between(0.05, 0.20))
    time.sleep(gaussian_between(0.05, 0.20))
    pag.moveTo(tx, ty, duration=gaussian_between(0.05, 0.15))


def idle_wander():
    """Subtle cursor wandering during idle periods."""
    if not ENABLE_IDLE_WANDER:
        return
    if in_spam_session or random.random() >= IDLE_WANDER_PROB:
        return
    sx, sy = pag.position()
    end = time.time() + gaussian_between(0.5, 2.0)
    while time.time() < end and bot_active:
        nx = int(sx + random.gauss(0, 10))
        ny = int(sy + random.gauss(0, 10))
        pag.moveTo(nx, ny, duration=gaussian_between(0.05, 0.25))
        time.sleep(gaussian_between(0.05, 0.25))
    pag.moveTo(sx, sy, duration=gaussian_between(0.05, 0.25))


def wander_offscreen_then_return():
    """Move the cursor offscreen for a moment then return."""
    if not ENABLE_WANDER_OFFSCREEN:
        return
    if in_spam_session or random.random() >= WANDER_OFFSCREEN_PROB:
        return
    sx, sy = pag.position()
    w, h = pag.size()
    side = random.choice(["left", "right", "top", "bottom"])
    if side == "left":
        ox, oy = -10, random.randint(0, h)
    elif side == "right":
        ox, oy = w + 10, random.randint(0, h)
    elif side == "top":
        ox, oy = random.randint(0, w), -10
    else:
        ox, oy = random.randint(0, w), h + 10
    pag.moveTo(ox, oy, duration=gaussian_between(0.2, 0.5))
    time.sleep(gaussian_between(0.2, 0.6))
    pag.moveTo(sx, sy, duration=gaussian_between(0.2, 0.5))


def micro_jitter(duration: float) -> None:
    """Tiny cursor jitters for the given duration."""
    end = time.time() + duration
    while time.time() < end and bot_active:
        sig = random.uniform(2, 5)
        dx = int(random.gauss(0, sig))
        dy = int(random.gauss(0, sig))
        pag.moveRel(dx, dy, duration=gaussian_between(0.02, 0.06))
        time.sleep(random.uniform(0.2, 0.5))


def _hover_jitter_variant_a():
    """Fine micro-jitters with small Gaussian offsets."""
    dx = int(clamp(random.gauss(0, 1.5), -3, 3))
    dy = int(clamp(random.gauss(0, 1.5), -3, 3))
    if dx or dy:
        pag.moveRel(dx, dy, duration=gaussian_between(0.01, 0.03))


def _hover_jitter_variant_b():
    """Broader tracking jitters occasionally triggered by a Gaussian curve."""
    if random.gauss(0, 1) > 0.6:
        dx = int(clamp(random.gauss(0, 3), -5, 5))
        dy = int(clamp(random.gauss(0, 3), -5, 5))
        pag.moveRel(dx, dy, duration=gaussian_between(0.03, 0.08))
        if random.random() < 0.3:
            pag.moveRel(
                -dx + int(random.gauss(0, 1)),
                -dy + int(random.gauss(0, 1)),
                duration=gaussian_between(0.03, 0.08),
            )


# ───────────────── Magic tab helper ───────────────────────────────


def click_magic_tab():
    if safe_locate(
        MAGIC_OPEN_IMAGE, confidence=OPEN_CONFIDENCE, grayscale=True
    ):
        return True
    tab = safe_locate(
        MAGIC_TAB_IMAGE, confidence=MAGIC_TAB_CONFIDENCE, grayscale=True
    )
    if tab:
        tx, ty = pag.center(tab)
        bezier_move(tx, ty)
        post_move_drift()
        pre_click_hover(tx, ty)
        pag.click()
        time.sleep(0.15)
        return True
    log("⚠️ Could not open Magic tab.")
    return False


# ───────────────────── Login helper ───────────────────────────────


def login(timeout: float = 15.0) -> bool:
    """Attempt to log in by clicking Play Now then Click Here to Play."""
    play = safe_locate(PLAY_NOW_IMAGE, confidence=CONFIDENCE, grayscale=True)
    if not play:
        log("⚠️ PlayNow.png not found.")
        return False
    tx, ty = pag.center(play)
    bezier_move(tx, ty)
    post_move_drift()
    pre_click_hover(tx, ty)
    pag.click()
    end = time.time() + timeout
    while time.time() < end:
        click = safe_locate(
            CLICK_TO_PLAY_IMAGE, confidence=CONFIDENCE, grayscale=True
        )
        if click:
            tx, ty = pag.center(click)
            bezier_move(tx, ty)
            post_move_drift()
            pre_click_hover(tx, ty)
            pag.click()
            return True
        time.sleep(0.25)
    log("⚠️ ClickHereToPlay.png not found.")
    return False


def _startup_login_check() -> None:
    """Attempt login on launch if the teleport rune is missing."""
    global teleport_last_seen, last_login_attempt
    if not safe_locate(
        TELEPORT_IMAGE, confidence=TELEPORT_CONFIDENCE, grayscale=True
    ):
        log("Teleport rune not found at start; attempting login...")
        last_login_attempt = time.time()
        if login():
            teleport_last_seen = time.time()


_startup_login_check()


def maybe_login() -> None:
    """Log in if the teleport rune has not been seen for LOGIN_RETRY_SECS."""
    global last_login_attempt, teleport_last_seen
    now = time.time()
    if (
        now - teleport_last_seen >= LOGIN_RETRY_SECS
        and now - last_login_attempt >= LOGIN_RETRY_SECS
    ):
        log("Teleport rune missing for 3 minutes; attempting login...")
        last_login_attempt = now
        if login():
            teleport_last_seen = time.time()


# ───────────────── Edge / YouTube helpers ─────────────────────────


def edge_windows():
    return [
        w
        for w in gw.getAllWindows()
        if not w.isMinimized
        and ("Edge" in w.title or "Microsoft Edge" in w.title)
    ]


def click_edge_youtube():
    wins = edge_windows()
    if not wins:
        return False
    win = random.choice(wins)
    tx = random.randint(win.left + 60, win.right - 60)
    ty = random.randint(win.top + 100, win.bottom - 100)
    bezier_move(tx, ty)
    post_move_drift()
    pre_click_hover(tx, ty)
    pag.click()
    return True


def scroll_loop(dur: float) -> None:
    """AFK interaction with a browser window."""
    log(f"Short AFK: scrolling for {dur:.1f}s")
    end = time.time() + dur
    win = None
    if hasattr(gw, "getActiveWindow"):
        try:
            win = gw.getActiveWindow()
        except Exception:
            win = None
    if win:
        cx = (win.left + win.right) / 2
        cy = (win.top + win.bottom) / 2
    else:
        cx, cy = pag.position()
    next_click = time.time() + clamp(random.gauss(4.0, 1.5), 1.0, 8.0)
    next_pause = time.time() + clamp(random.gauss(15.0, 5.0), 5.0, dur)
    while time.time() < end and bot_active:
        if win:
            tx = int(random.gauss(cx, win.width / 4))
            ty = int(random.gauss(cy, win.height / 4))
            tx = clamp(tx, win.left + 5, win.right - 5)
            ty = clamp(ty, win.top + 5, win.bottom - 5)
            bezier_move(tx, ty)
        pag.scroll(int(random.gauss(0, 80)))
        idle_wander()
        wander_offscreen_then_return()
        if time.time() >= next_click:
            if random.random() < 0.5:
                pag.click()
            else:
                pag.doubleClick()
            next_click = time.time() + clamp(random.gauss(4.0, 1.5), 1.0, 8.0)
        if time.time() >= next_pause:
            pause = clamp(
                random.gauss(15.0, 5.0), 5.0, max(0.0, end - time.time())
            )
            micro_jitter(pause)
            next_pause = time.time() + clamp(random.gauss(15.0, 5.0), 5.0, dur)
        time.sleep(random.uniform(0.5, 1.4))


# ───────────────── Random tab-flipping idle loop ──────────────────


def random_tab_loop(duration):
    log(f"Short AFK: tab flipping for {duration:.1f}s")
    mu = clamp(random.gauss(4.0, 0.7), 2.0, 7.0)
    lam = 1.0 / mu
    t_next = time.time() + random.expovariate(lam)
    end = time.time() + duration

    last_idx = random.randrange(len(TAB_IMAGES))
    while t_next < end and bot_active:
        time.sleep(max(0, t_next - time.time()))
        low = max(0, last_idx - 2)
        high = min(len(TAB_IMAGES) - 1, last_idx + 2)
        next_idx = random.randint(low, high)
        last_idx = next_idx
        tab_img = TAB_IMAGES[next_idx]
        loc = safe_locate(tab_img, confidence=CONFIDENCE, grayscale=True)
        if loc:
            tx, ty = pag.center(loc)
            bezier_move(tx, ty)
            post_move_drift()
            pre_click_hover(tx, ty)
            pag.click()
            idle_wander()
            wander_offscreen_then_return()
        t_next += random.expovariate(lam)


# ───────────────── Stats-hover helper ─────────────────────────────


def stats_hover(dur) -> bool:
    log(f"Short AFK: hovering stats for {dur:.1f}s")
    stats = safe_locate(
        STATS_IMAGE, confidence=STATS_CONFIDENCE, grayscale=True
    )
    if not stats:
        return False
    tx, ty = pag.center(stats)
    bezier_move(tx, ty)
    post_move_drift()
    pre_click_hover(tx, ty)
    pag.click()
    time.sleep(0.2)
    magic = safe_locate(
        MAGICLVL_IMAGE, confidence=STATS_CONFIDENCE, grayscale=True
    )
    if not magic:
        return False
    tx, ty = pag.center(magic)
    bezier_move(tx, ty)
    post_move_drift()
    pre_click_hover(tx, ty)
    end = time.time() + dur
    use_a = random.random() < 0.5
    next_jitter = time.time()
    while time.time() < end and bot_active:
        now = time.time()
        if now >= next_jitter:
            if use_a:
                _hover_jitter_variant_a()
                next_jitter = now + random.uniform(0.05, 0.25)
            else:
                _hover_jitter_variant_b()
                next_jitter = now + random.uniform(0.10, 0.30)
        if feature("idle_wiggle"):
            idle_wiggle()
        idle_wander()
        wander_offscreen_then_return()
        maybe_outlier_event("rest")
        time.sleep(0.05)
    return True


# ───────────────── Short-rest handler ─────────────────────────────


def default_rest(dur):
    idle_wander()
    wander_offscreen_then_return()
    ch = random.random()
    if ENABLE_BROWSER_AFK and ch < 0.60 and click_edge_youtube():
        scroll_loop(dur)
    elif ENABLE_TAB_FLIP:
        random_tab_loop(dur)
    else:
        time.sleep(dur)
    click_magic_tab()


def handle_afk(mode: str = "normal_afk", dur: float | None = None):
    """Handle all AFK behaviour.

    Parameters
    ----------
    mode : str, optional
        "micro_afk", "mini_afk" or "short_afk" for rest periods between bursts,
        "normal_afk" for scheduled short breaks,
        "long_afk" for scheduled long breaks.
    dur : float | None, optional
        Override duration in seconds. If ``None`` the duration is
        determined automatically based on ``mode``.
    """

    global next_short_afk_time, next_long_afk_time

    if mode not in {"micro_afk", "mini_afk", "short_afk", "normal_afk", "long_afk"}:
        debug(f"Invalid AFK mode: {mode}")
        return

    # Treat mini_afk as an alias for short_afk but remember for logging
    is_mini = False
    if mode == "mini_afk":
        is_mini = True
        mode = "short_afk"

    was_micro = False
    if mode == "micro_afk":
        was_micro = True
        if dur is None:
            dur = gamma_between(0.8, 3.5, 2.0)
        if random.random() > MICRO_AFK_FREQ_LEVEL:
            return
        mode = "short_afk"

    if mode == "normal_afk":
        if not ENABLE_AFK:
            return
        if dur is None and time.time() < next_short_afk_time:
            debug("AFK not due yet")
            return
        if random.random() >= AFK_FREQ_LEVEL:
            next_short_afk_time = time.time() + gamma_between(
                AFK_MIN_SECS, AFK_MAX_SECS, 2.4
            )
            debug("AFK skipped")
            return
    elif mode == "long_afk":
        if not ENABLE_AFK:
            return
        if dur is None and time.time() < next_long_afk_time:
            debug("Long AFK not due yet")
            return
        if random.random() >= LONG_AFK_FREQ_LEVEL:
            next_long_afk_time = time.time() + gamma_between(
                LONG_AFK_MIN_SECS, LONG_AFK_MAX_SECS, 2.4
            )
            debug("Long AFK skipped")
            return

    if mode == "short_afk":
        if dur is None or dur < 0.25:
            return
        if random.random() >= MINI_AFK_FREQ_LEVEL:
            return
        if random.random() >= SHORT_REST_TASK_PROB:
            if is_mini:
                log(f"Mini AFK for {dur:.1f}s")
            time.sleep(dur)
            click_magic_tab()
            return
        if is_mini:
            log(f"Mini AFK task for {dur:.1f}s")
        else:
            log(f"Short AFK task for {dur:.1f}s")
    else:
        is_long = mode == "long_afk"
        if dur is None:
            dur = (
                gamma_between(53, 300, 2.1)
                if is_long
                else gamma_between(1, 47, 2.1)
            )
        log(f"{'Long' if is_long else 'Short'} AFK: {int(dur)} s")

    ctx = "rest" if mode == "short_afk" else "afk"
    maybe_outlier_event(ctx)
    if was_micro:
        maybe_outlier_event("afk")

    if (
        mode == "short_afk"
        and ENABLE_STATS_HOVER
        and (STATS_REST_TEST_MODE or random.random() < STATS_REST_PROB)
    ):
        if not stats_hover(dur):
            default_rest(dur)
    else:
        ch = random.random()
        threshold = 0.60 if mode in {"short_afk", "long_afk"} else 0.50
        if ENABLE_BROWSER_AFK and ch < threshold and click_edge_youtube():
            scroll_loop(dur)
        elif ENABLE_TAB_FLIP:
            random_tab_loop(dur)
        else:
            if mode == "short_afk":
                idle_wander()
                wander_offscreen_then_return()
                time.sleep(dur)
            else:
                end = time.time() + dur
                while time.time() < end and bot_active:
                    maybe_outlier_event("afk")
                    idle_wander()
                    wander_offscreen_then_return()
                    time.sleep(0.5)

    if mode == "normal_afk":
        next_short_afk_time = time.time() + gamma_between(
            AFK_MIN_SECS, AFK_MAX_SECS, 2.4
        )
        debug(
            f"Next AFK scheduled in {int(next_short_afk_time - time.time())} s"
        )
    elif mode == "long_afk":
        next_long_afk_time = time.time() + gamma_between(
            LONG_AFK_MIN_SECS, LONG_AFK_MAX_SECS, 2.4
        )
        debug(
            f"Next long AFK scheduled in {int(next_long_afk_time - time.time())} s"
        )

    click_magic_tab()


# ───────────────── Click-spam session ─────────────────────────────
def spam_session():
    """Single teleport spam burst."""
    global in_spam_session
    in_spam_session = True
    try:
        burst = gaussian_between(SPAM_MIN, SPAM_MAX)
        rest = clamp(
            gaussian_between(REST_MIN, REST_MAX),
            5.0,
            11.0,
        )

        click_magic_tab()

        loc = safe_locate(
            TELEPORT_IMAGE, confidence=TELEPORT_CONFIDENCE, grayscale=True
        )
        if not loc:
            log("Teleport rune not found; clicking Magic tab...")
            if not click_magic_tab():
                log("⚠️ Could not open Magic tab; skipping burst.")
                return
            loc = safe_locate(
                TELEPORT_IMAGE, confidence=TELEPORT_CONFIDENCE, grayscale=True
            )
            if not loc:
                log("Teleport rune still not found; pressing F6...")
                pag.press("f6")
                time.sleep(0.5)
                loc = safe_locate(
                    TELEPORT_IMAGE,
                    confidence=TELEPORT_CONFIDENCE,
                    grayscale=True,
                )
                if not loc:
                    log("Teleport rune still not found; skipping burst.")
                    maybe_login()
                    return

        global teleport_last_seen
        teleport_last_seen = time.time()

        x, y = pag.center(loc)
        y += 3
        log(f"Click burst {burst:.1f}s at ({x}, {y})")

        end = time.time() + burst
        while time.time() < end and bot_active:
            maybe_outlier_event("burst")

            drift_x = random.gauss(0, 0.3)
            drift_y = random.gauss(0, 0.3)
            if abs(drift_x) < 0.3:
                drift_x = 0
            if abs(drift_y) < 0.3:
                drift_y = 0

            target_x = x + int(round(drift_x))
            target_y = y + int(round(drift_y))
            bezier_move(target_x, target_y)

            if CHECK_FINAL_POS:
                fx, fy = pag.position()
                if math.hypot(fx - target_x, fy - target_y) > 3:
                    debug(
                        f"cursor drifted to {(fx, fy)} expected {(target_x, target_y)}"
                    )
                    pag.moveTo(target_x, target_y)
                    pag.click()
                    continue

            if feature("finger_hesitation"):
                time.sleep(random.uniform(0.05, 0.15))

            if LOG_CLICKS:
                debug(f"click at {pag.position()}")

            if ROBUST_CLICK:
                pag.mouseDown()
                time.sleep(random.uniform(CLICK_HOLD_MIN, CLICK_HOLD_MAX))
                pag.mouseUp()
            else:
                pag.click()

            if LOG_CLICKS:
                debug("click issued")

            if CHECK_FINAL_POS:
                chk = safe_locate(
                    TELEPORT_IMAGE,
                    confidence=TELEPORT_CONFIDENCE,
                    grayscale=True,
                    region=(x - 20, y - 20, 40, 40),
                )
                if chk:
                    debug("click retry")
                    pag.click()

            if feature("double_click"):
                time.sleep(random.uniform(0.03, 0.08))
                if LOG_CLICKS:
                    debug("double click")
                pag.click()

            gap = (
                gamma_between(0.12, 0.60, 2.5)
                if feature("drift_click_timing")
                else random.uniform(0.06, 1.00)
            )
            time.sleep(gap)

            if feature("idle_wiggle"):
                idle_wiggle()

            if random.random() < 0.05:
                handle_afk("micro_afk")

        if ENABLE_REST:
            log(f"Burst done. Rest {rest:.1f}s...")
            handle_afk("mini_afk", rest)
        else:
            log("Burst done. Rest skipped.")
    finally:
        in_spam_session = False


# ───────────────── Hotkey thread ──────────────────────────────────


def hotkey_thread():
    global bot_active
    while True:
        if keyboard.is_pressed("1"):
            bot_active = not bot_active
            log("Bot paused." if not bot_active else "Bot resumed.")
            time.sleep(0.4)
        if keyboard.is_pressed("2"):
            toggle_console()
            time.sleep(0.4)
        if keyboard.is_pressed("3"):
            log("Bot stopped (3).")
            os._exit(0)
        time.sleep(0.05)


# ───────────────── Main loop ───────────────────────────────────────


def main_loop():
    global loop_counter, next_weight_refresh
    while True:
        if not bot_active:
            time.sleep(0.25)
            continue
        loop_counter += 1
        if loop_counter >= next_weight_refresh:
            refresh_weights()
            next_weight_refresh = loop_counter + int(
                abs(random.gauss(LOOP_MEAN, LOOP_SD)) + 1
            )
        handle_afk()
        handle_afk("long_afk")
        spam_session()


# ───────────────── Entry ───────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=hotkey_thread, daemon=True).start()
    refresh_weights()
    next_weight_refresh = int(abs(random.gauss(LOOP_MEAN, LOOP_SD)) + 1)
    log(f"Bot started spamming {choice}. 1=pause • 3=quit")
    try:
        main_loop()
    except Exception as e:
        log(f"Fatal error: {e}")
        traceback.print_exc()
