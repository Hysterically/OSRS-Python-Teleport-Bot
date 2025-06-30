# =============================================================================
# EssayReview.py – Var/Fal/Cam Teleport Spam Bot
# v40  • StatsTab.png  • Random tab-flips on idle rest  • GC-safe DraftTracker
# =============================================================================
#  Hotkeys:  1 = pause/resume  •  2 = toggle console  •  3 = quit
# =============================================================================
import pygetwindow as gw
from .DraftTracker import DraftTracker
import pyautogui as pag
from pyautogui import ImageNotFoundException
try:
    import keyboard
except Exception:  # pragma: no cover - keyboard may be unavailable
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

# absolute paths ------------------------------------------------------------
PKG_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(PKG_DIR, os.pardir))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

# ───────────────────────── Overlay logger ──────────────────────────
# Toggle for enabling the draggable overlay that shows recent log
# messages and a magic cape image. The overlay is enabled by default
# but can be switched off in the configuration window.
ENABLE_OVERLAY = True

# Feature toggles ----------------------------------------------------
# Move slightly past the target before coming back
# to mimic how humans sometimes overshoot the cursor.
ENABLE_OVERSHOOT = True

# Add tiny wiggles during long mouse moves so the
# cursor doesn't glide in a perfectly straight line.
ENABLE_JITTER = True

# Prevent unrealistic acceleration by capping how
# quickly the mouse speed can change.
ENABLE_VELOCITY_LIMIT = True

# After moving to a rune, check the final mouse
# position and correct drift before clicking.
CHECK_FINAL_POS = True

# Write every click position to the overlay and console
# which helps diagnose missed clicks.
LOG_CLICKS = True

# Master switch for verbose debug output.
DEBUG_LOGGING = False

# Use a mouseDown → short pause → mouseUp sequence
# for each click. This can be more reliable on some
# systems than a regular quick click.
ROBUST_CLICK = False

# Toggle long and short AFK events. When disabled the bot will
# never perform random idle breaks.
ENABLE_AFK = True

# Enable random anti-ban extras like double clicks or cursor wiggles.
ENABLE_ANTIBAN = True

# Additional optional behaviours
# When enabled the bot may move the mouse over the stats tab during
# short rests. Disabling this prevents any stats-hover actions.
ENABLE_STATS_HOVER = True

# During some breaks the bot scrolls a random Edge/YouTube window.
# This can be turned off if no browser is running or it causes issues.
ENABLE_BROWSER_AFK = True

# If enabled the bot flips through random side tabs while idling.
ENABLE_TAB_FLIP = True

# Disable the brief rest between click bursts. When off the bot immediately
# starts the next burst without pausing.
ENABLE_REST = True

# Chance that the bot performs any short AFK task during the brief rest
# between bursts. Set between 0.0 (never) and 1.0 (always).
SHORT_REST_TASK_PROB = 1.0



class _DummyOverlay:
    def update_log(self, msg: str) -> None:
        pass

    def set_cape_scale(self, factor: float) -> None:
        pass


# Placeholder overlay; the real DraftTracker instance is created after
# the configuration window so the user can disable it before it starts.
overlay: object = _DummyOverlay()

# Default confidence for image recognition
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
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
        console_visible = False


def show_console():
    global console_visible
    hwnd = _console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
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
    overlay.update_log(f"{stamp} {msg}")
    print(f"{stamp} {msg}", flush=True)


# ───────────────────── Config prompt ───────────────────────────────

def config_prompt():
    """Interactive window for teleport and feature settings."""
    if "PYTEST_CURRENT_TEST" in os.environ or (
        os.name != "nt" and not os.environ.get("DISPLAY")
    ):
        # during automated tests or headless environments use defaults
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

    container = ttk.Frame(root)
    container.place(relx=0.5, rely=0.5, anchor="center")

    tele_var = tk.StringVar(value="Camelot")
    tk.Label(container, text="Select teleport:", bg=bg, fg=fg).pack(
        pady=(10, 0)
    )
    for opt in OPTIONS.keys():
        ttk.Radiobutton(container, text=opt, value=opt, variable=tele_var).pack(
        )

    overlay_var = tk.BooleanVar(value=ENABLE_OVERLAY)
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

    tk.Label(container, text="Options:", bg=bg, fg=fg).pack(pady=(10, 0))

    def add_switch(label_text: str, var: tk.BooleanVar) -> None:
        frame = ttk.Frame(container)
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
        frame.pack(pady=2)

    add_switch("Show overlay (info window)", overlay_var)
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

    tk.Label(container, text="Teleport confidence:", bg=bg, fg=fg).pack(
        pady=(10, 0)
    )
    tele_conf_var = tk.DoubleVar(value=TELEPORT_CONFIDENCE)
    ttk.Entry(container, textvariable=tele_conf_var, width=5).pack()

    tk.Label(container, text="Short rest task chance:", bg=bg, fg=fg).pack(
        pady=(10, 0)
    )
    short_rest_prob_var = tk.DoubleVar(value=SHORT_REST_TASK_PROB)
    ttk.Entry(container, textvariable=short_rest_prob_var, width=5).pack()

    def _start():
        global ENABLE_OVERLAY, ENABLE_OVERSHOOT, ENABLE_JITTER
        global ENABLE_VELOCITY_LIMIT, CHECK_FINAL_POS, LOG_CLICKS, ROBUST_CLICK
        global ENABLE_AFK, ENABLE_ANTIBAN
        global ENABLE_STATS_HOVER, ENABLE_BROWSER_AFK, ENABLE_TAB_FLIP, choice
        global ENABLE_REST, TELEPORT_CONFIDENCE, DEBUG_LOGGING
        global SHORT_REST_TASK_PROB
        ENABLE_OVERLAY = overlay_var.get()
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
            TELEPORT_CONFIDENCE = max(0.0, min(1.0, float(tele_conf_var.get())))
        except Exception:
            TELEPORT_CONFIDENCE = CONFIDENCE
        try:
            SHORT_REST_TASK_PROB = max(
                0.0, min(1.0, float(short_rest_prob_var.get()))
            )
        except Exception:
            SHORT_REST_TASK_PROB = 1.0
        choice = tele_var.get()
        root.destroy()

    ttk.Button(container, text="Start", command=_start).pack(pady=10)
    root.protocol("WM_DELETE_WINDOW", lambda: sys.exit("No teleport selected – exiting."))
    root.mainloop()
    return choice


# ───────────────────── PyAutoGUI tweaks ────────────────────────────
pag.FAILSAFE = False
pag.PAUSE = 0

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

if ENABLE_OVERLAY:
    overlay = DraftTracker()
    try:
        overlay.set_cape_scale(3.0)
    except AttributeError:
        pass

# ─────────────────── Safe locate wrapper ───────────────────────────


def safe_locate(img, **kw):
    try:
        loc = pag.locateOnScreen(img, **kw)
        if loc:
            debug(f"Located {os.path.basename(img)} at {loc}")
        else:
            debug(f"Image {os.path.basename(img)} not found")
        return loc
    except (ImageNotFoundException, ValueError) as e:
        debug(f"Locate failed for {os.path.basename(img)}: {e}")
        return None


# ───────────────────── Image assets ────────────────────────────────
STATS_IMAGE = os.path.join(ASSETS_DIR, "StatsTab.png")
MAGICLVL_IMAGE = os.path.join(ASSETS_DIR, "MagicLvl.png")
MAGIC_TAB_IMAGE = os.path.join(ASSETS_DIR, "MagicTab.png")
MAGIC_OPEN_IMAGE = os.path.join(ASSETS_DIR, "MagicTabOpen.png")
PLAY_NOW_IMAGE = os.path.join(ASSETS_DIR, "PlayNow.png")
CLICK_TO_PLAY_IMAGE = os.path.join(ASSETS_DIR, "ClickHereToPlay.png")

TAB_IMAGES = [  # side-panel sprites for random flips
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
# Lowered threshold for locating MagicTab.png
MAGIC_TAB_CONFIDENCE = 0.80

# ───────────────── Behaviour constants ────────────────────────────
SPAM_MIN, SPAM_MAX = 1, 70
REST_MIN, REST_MAX = 1, 40
CLICK_MIN_GAP, CLICK_MAX_GAP = 0.06, 1.00
# Range of seconds to hold the mouse button down when
# ROBUST_CLICK is enabled.
CLICK_HOLD_MIN, CLICK_HOLD_MAX = 0.010, 0.060
# Increase AFK interval so events occur ~5x less often
AFK_MIN_SECS, AFK_MAX_SECS = 22500, 67500
SEGMENT_MIN, SEGMENT_MAX = 3, 6
# Overshoot range for mouse movement (pixels). When the cursor distance is
# small the overshoot amount is scaled down so movements between adjacent tabs
# don't appear robotic.
OVERSHOOT_MIN, OVERSHOOT_MAX = 4, 8
LOOP_MEAN, LOOP_SD = 10, 2

MAX_ACCEL = 8000  # max allowed acceleration (px/s^2)
SMOOTH_STOP_DIST = 40  # distance (px) to begin slowing for final stop

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

# Jitter settings for long mouse moves
JITTER_PROB = 0.1  # chance per segment to add jitter
JITTER_PIXELS = 1  # ±pixels moved during jitter
JITTER_DIST_THRESHOLD = 100  # only apply jitter when distance > this
JITTER_PAUSE_MIN, JITTER_PAUSE_MAX = 0.003, 0.010

# ───────────────── Runtime state ───────────────────────────────────
bot_active = True
loop_counter = 0
next_weight_refresh = 0
next_afk_time = 0
anti_ban_weights = {}
overshoot_chance = 0.30
last_move_velocities: list[float] = []

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

# ───────────────── Anti-ban weights ────────────────────────────────


def refresh_weights():
    global anti_ban_weights, overshoot_chance, next_afk_time
    anti_ban_weights = {
        "drift_click_timing": clamp(random.gauss(0.5, 0.2), 0.1, 0.9),
        "idle_wiggle": clamp(random.gauss(0.4, 0.15), 0.05, 0.8),
        "double_click": clamp(random.gauss(0.2, 0.1), 0, 0.5),
        "finger_hesitation": clamp(random.gauss(0.25, 0.1), 0, 0.6),
    }
    overshoot_chance = clamp(random.gauss(0.3, 0.08), 0.1, 0.5)
    if ENABLE_AFK:
        next_afk_time = time.time() + gamma_between(AFK_MIN_SECS, AFK_MAX_SECS, 2.4)
    else:
        next_afk_time = float("inf")
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
    event = random.choice(["corner_drift", "off_click", "scroll_spam", "camera_circle"])
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
        math.hypot(px - sx, py - sy) for (sx, sy), (px, py) in zip(path[:-1], path[1:])
    ]
    total = sum(seg_lens) or 1
    T = fitts_time(total, W, a=random.uniform(0.04, 0.06), b=random.uniform(0.04, 0.07))
    # Add built-in random variation and slower baseline
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
    for (px, py), seg_len, t0, t1 in zip(path[1:], seg_lens, times[:-1], times[1:]):
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
                    seg_T = max(seg_T, (prev_v + math.sqrt(disc)) / (2 * MAX_ACCEL))
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
        debug(
            f"seg to {(px, py)} len={seg_len:.1f} T={seg_T:.3f} v={v:.1f}"
        )
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

    # ensure the cursor ends exactly on the target
    pag.moveTo(tx, ty)
    debug(f"move complete at {pag.position()}")


def idle_wiggle():
    x, y = pag.position()
    pag.moveTo(x + pink.next(), y + pink.next(), duration=random.uniform(0.02, 0.05))


# ───────────────── Magic tab helper ───────────────────────────────


def click_magic_tab():
    if safe_locate(MAGIC_OPEN_IMAGE, confidence=OPEN_CONFIDENCE, grayscale=True):
        return True
    tab = safe_locate(MAGIC_TAB_IMAGE, confidence=MAGIC_TAB_CONFIDENCE, grayscale=True)
    if tab:
        bezier_move(*pag.center(tab))
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
    bezier_move(*pag.center(play))
    pag.click()
    end = time.time() + timeout
    while time.time() < end:
        click = safe_locate(CLICK_TO_PLAY_IMAGE, confidence=CONFIDENCE, grayscale=True)
        if click:
            bezier_move(*pag.center(click))
            pag.click()
            return True
        time.sleep(0.25)
    log("⚠️ ClickHereToPlay.png not found.")
    return False


# ───────────────── Edge / YouTube helpers ─────────────────────────


def edge_windows():
    return [
        w
        for w in gw.getAllWindows()
        if not w.isMinimized and ("Edge" in w.title or "Microsoft Edge" in w.title)
    ]


def click_edge_youtube():
    wins = edge_windows()
    if not wins:
        return False
    win = random.choice(wins)
    tx = random.randint(win.left + 60, win.right - 60)
    ty = random.randint(win.top + 100, win.bottom - 100)
    bezier_move(tx, ty)
    pag.click()
    return True


def scroll_loop(dur):
    log(f"Short AFK: scrolling for {dur:.1f}s")
    end = time.time() + dur
    while time.time() < end and bot_active:
        pag.scroll(random.randint(-600, 600))
        time.sleep(random.uniform(0.5, 1.4))


# ───────────────── Random tab-flipping idle loop ──────────────────


def random_tab_loop(duration):
    log(f"Short AFK: tab flipping for {duration:.1f}s")
    mu = clamp(random.gauss(4.0, 0.7), 2.0, 7.0)  # mean sec between flips
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
            bezier_move(*pag.center(loc))
            pag.click()
        t_next += random.expovariate(lam)


# ───────────────── Stats-hover helper ─────────────────────────────


def stats_hover(dur) -> bool:
    log(f"Short AFK: hovering stats for {dur:.1f}s")
    stats = safe_locate(STATS_IMAGE, confidence=STATS_CONFIDENCE, grayscale=True)
    if not stats:
        return False
    bezier_move(*pag.center(stats))
    pag.click()
    time.sleep(0.2)
    magic = safe_locate(MAGICLVL_IMAGE, confidence=STATS_CONFIDENCE, grayscale=True)
    if not magic:
        return False
    bezier_move(*pag.center(magic))
    end = time.time() + dur
    while time.time() < end and bot_active:
        if feature("idle_wiggle"):
            idle_wiggle()
        maybe_outlier_event("rest")
        time.sleep(0.25)
    return True


# ───────────────── Short-rest handler ─────────────────────────────


def default_rest(dur):
    ch = random.random()
    if ENABLE_BROWSER_AFK and ch < 0.60 and click_edge_youtube():
        scroll_loop(dur)
    elif ENABLE_TAB_FLIP:
        random_tab_loop(dur)
    else:
        time.sleep(dur)
    click_magic_tab()


def handle_short_rest(rest):
    if rest < 0.25:
        return
    if random.random() >= SHORT_REST_TASK_PROB:
        time.sleep(rest)
        click_magic_tab()
        return
    log(f"Short AFK task for {rest:.1f}s")
    maybe_outlier_event("rest")
    if ENABLE_STATS_HOVER and (
        STATS_REST_TEST_MODE or random.random() < STATS_REST_PROB
    ):
        if not stats_hover(rest):
            default_rest(rest)
    else:
        default_rest(rest)


# ───────────────── AFK handler (unchanged) ────────────────────────


def handle_afk():
    global next_afk_time
    if not ENABLE_AFK:
        return
    if time.time() < next_afk_time:
        debug("AFK not due yet")
        return
    long_prob = random.betavariate(2.2, 5.0)
    is_long = random.random() < long_prob
    dur = gamma_between(53, 300, 2.1) if is_long else gamma_between(1, 47, 2.1)
    log(f"{'Long' if is_long else 'Short'} AFK: {int(dur)} s")
    ch = random.random()
    if ENABLE_BROWSER_AFK and (ch < 0.60 if is_long else ch < 0.50) and click_edge_youtube():
        scroll_loop(dur)
    elif ENABLE_TAB_FLIP:
        random_tab_loop(dur)
    else:
        end = time.time() + dur
        while time.time() < end and bot_active:
            maybe_outlier_event("afk")
            time.sleep(0.5)
    next_afk_time = time.time() + gamma_between(AFK_MIN_SECS, AFK_MAX_SECS, 2.4)
    debug(f"Next AFK scheduled in {int(next_afk_time - time.time())} s")
    click_magic_tab()

# ───────────────── Click-spam session ─────────────────────────────
def spam_session():
    burst = gaussian_between(SPAM_MIN, SPAM_MAX)
    rest  = gaussian_between(REST_MIN, REST_MAX)

    # Always start by opening the Magic tab
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
                TELEPORT_IMAGE, confidence=TELEPORT_CONFIDENCE, grayscale=True
            )
            if not loc:
                log("Teleport rune still not found; skipping burst.")
                return

    # Centre plus downward nudge
    x, y = pag.center(loc)
    y    += 3
    log(f"Click burst {burst:.1f}s at ({x}, {y})")

    end = time.time() + burst
    while time.time() < end and bot_active:
        handle_afk()
        maybe_outlier_event("burst")

        # add a little randomness around the centre point
        target_x = x + random.randint(-2, 2)
        target_y = y + random.randint(-2, 2)
        bezier_move(target_x, target_y)

        # if the cursor drifted, re-align and force a click
        if CHECK_FINAL_POS:
            fx, fy = pag.position()
            if math.hypot(fx - target_x, fy - target_y) > 3:
                debug(f"cursor drifted to {(fx, fy)} expected {(target_x, target_y)}")
                pag.moveTo(target_x, target_y)
                pag.click()
                continue

        if feature("finger_hesitation"):
            time.sleep(random.uniform(0.05, 0.15))

        if LOG_CLICKS:
            debug(f"click at {pag.position()}")

        # robust click if enabled, else normal click
        if ROBUST_CLICK:
            pag.mouseDown()
            time.sleep(random.uniform(CLICK_HOLD_MIN, CLICK_HOLD_MAX))
            pag.mouseUp()
        else:
            pag.click()

        if LOG_CLICKS:
            debug("click issued")

        # if the rune is still present, retry click once
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

    if ENABLE_REST:
        log(f"Burst done. Rest {rest:.1f}s...")
        handle_short_rest(rest)
    else:
        log("Burst done. Rest skipped.")



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
