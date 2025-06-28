# =============================================================================
# EssayReview.py – Var/Fal/Cam Teleport Spam Bot
# v40  • StatsTab.png  • Random tab-flips on idle rest  • GC-safe DraftTracker
# =============================================================================
#  Hotkeys:  F1 = pause/resume  •  F2 = toggle console  •  F3 = quit
# =============================================================================
import pyautogui as pag
from pyautogui import ImageNotFoundException
import keyboard, time, random, threading, math, os, sys, traceback
import ctypes

# absolute paths ------------------------------------------------------------
PKG_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(PKG_DIR, os.pardir))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
from datetime import datetime
from .DraftTracker import DraftTracker
import pygetwindow as gw

# ───────────────────────── Overlay logger ──────────────────────────
overlay = DraftTracker()
try:
    overlay.set_cape_scale(3.0)         # enlarge cape ×2
except AttributeError:
    pass

# ─────────────────── Console visibility helpers ───────────────────
console_visible = True

def _console_hwnd():
    if os.name == 'nt':
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

def log(msg: str):
    stamp = datetime.now().strftime("%H:%M:%S")
    print(stamp, msg, flush=True)
    overlay.update_log(f"{stamp} {msg}")

# ───────────────────── PyAutoGUI tweaks ────────────────────────────
pag.FAILSAFE = False
pag.PAUSE    = 0

# ─────────────────── Teleport selection prompt ─────────────────────
OPTIONS = {
    "Varrock": os.path.join(ASSETS_DIR, "Var.png"),
    "Falador": os.path.join(ASSETS_DIR, "Fal.png"),
    "Camelot": os.path.join(ASSETS_DIR, "Cam.png"),
}
choice = pag.confirm("Which teleport should the bot spam-click?",
                     title="Choose Teleport",
                     buttons=list(OPTIONS.keys()))
if choice is None:
    sys.exit("No teleport selected – exiting.")
TELEPORT_IMAGE = OPTIONS[choice]

# ─────────────────── Safe locate wrapper ───────────────────────────
def safe_locate(img, **kw):
    try:    return pag.locateOnScreen(img, **kw)
    except ImageNotFoundException: return None

# ───────────────────── Image assets ────────────────────────────────
STATS_IMAGE      = os.path.join(ASSETS_DIR, "StatsTab.png")
MAGICLVL_IMAGE   = os.path.join(ASSETS_DIR, "MagicLvl.png")
MAGIC_TAB_IMAGE  = os.path.join(ASSETS_DIR, "MagicTab.png")
MAGIC_OPEN_IMAGE = os.path.join(ASSETS_DIR, "MagicTabOpen.png")

TAB_IMAGES = [   # side-panel sprites for random flips
    os.path.join(ASSETS_DIR, "CombatTab.png"),
    os.path.join(ASSETS_DIR, "EmojiTab.png"),
    os.path.join(ASSETS_DIR, "FriendsListTab.png"),
    os.path.join(ASSETS_DIR, "PrayerTab.png"),
    os.path.join(ASSETS_DIR, "QuestTab.png"),
    os.path.join(ASSETS_DIR, "MusicTab.png"),
    os.path.join(ASSETS_DIR, "SettingsTab.png"),
    os.path.join(ASSETS_DIR, "LogOutTab.png")
]

# ───────────────── Confidence levels ───────────────────────────────
CONFIDENCE       = 0.90
STATS_CONFIDENCE = 0.80
OPEN_CONFIDENCE  = 0.85

# ───────────────── Behaviour constants ────────────────────────────
SPAM_MIN, SPAM_MAX               = 1, 70
REST_MIN, REST_MAX               = 1, 40
CLICK_MIN_GAP, CLICK_MAX_GAP     = 0.06, 1.00
CLICK_HOLD_MIN, CLICK_HOLD_MAX   = 0.010, 0.060
AFK_MIN_SECS, AFK_MAX_SECS       = 1800, 5400
SEGMENT_MIN, SEGMENT_MAX         = 3, 6
OVERSHOOT_MIN, OVERSHOOT_MAX     = 4, 8
LOOP_MEAN, LOOP_SD               = 10, 2

STATS_REST_PROB      = 0.10
STATS_REST_TEST_MODE = False

TWEEN_FUNCS = [
    pag.easeInQuad, pag.easeOutQuad, pag.easeInOutQuad,
    pag.easeInCubic, pag.easeOutCubic, pag.easeInOutCubic]

# ───────────────── Runtime state ───────────────────────────────────
bot_active           = True
loop_counter         = 0
next_weight_refresh  = 0
next_afk_time        = 0
anti_ban_weights     = {}
overshoot_chance     = 0.30

# ───────────────── Maths helpers ───────────────────────────────────
def clamp(v, lo, hi): return max(lo, min(hi, v))
def gaussian_between(lo, hi, m=None, s=None):
    if m is None: m = (lo + hi) / 2
    if s is None: s = (hi - lo) / 6
    return clamp(random.gauss(m, s), lo, hi)
def gamma_between(lo, hi, k=2.0):
    theta = ((lo + hi) / 2) / k
    return clamp(random.gammavariate(k, theta), lo, hi)
def lognorm_between(lo, hi, mu=None, sigma=0.4):
    mu = math.log((lo + hi) / 2) if mu is None else mu
    return clamp(random.lognormvariate(mu, sigma), lo, hi)

class PinkNoise:
    def __init__(self, a=0.8): self.a, self.p = a, 0
    def next(self, s=3):
        self.p = self.a*self.p + (1-self.a)*random.uniform(-1,1)
        return int(self.p*s)
pink = PinkNoise()

# ───────────────── Anti-ban weights ────────────────────────────────
def refresh_weights():
    global anti_ban_weights, overshoot_chance, next_afk_time
    anti_ban_weights = {
        "drift_click_timing": clamp(random.gauss(.5,.2), .1,.9),
        "idle_wiggle"       : clamp(random.gauss(.4,.15), .05,.8),
        "double_click"      : clamp(random.gauss(.2,.1), 0,.5),
        "finger_hesitation" : clamp(random.gauss(.25,.1),0,.6)}
    overshoot_chance = clamp(random.gauss(.3,.08), .1,.5)
    next_afk_time    = time.time() + gamma_between(AFK_MIN_SECS, AFK_MAX_SECS, 2.4)
    log("Anti-ban settings updated.")

def feature(k): return random.random() < anti_ban_weights.get(k, 0)

# ───────────────── Outlier events (rarer ×10) ─────────────────────
def maybe_outlier_event(ctx: str):
    odds = {"burst": 0.0006, "rest": 0.0008, "afk": 0.0010}
    if random.random() > odds.get(ctx, 0.0006): return
    event = random.choice(["corner_drift", "off_click",
                           "scroll_spam", "camera_circle"])
    log(f"⚠️ Outlier event: {event} during {ctx}")
    if event == "corner_drift":
        start = pag.position(); bezier_move(5,5)
        time.sleep(random.uniform(.3,.8)); bezier_move(*start)
    elif event == "off_click":
        loc = safe_locate(TELEPORT_IMAGE, confidence=CONFIDENCE, grayscale=True)
        if loc:
            x,y = pag.center(loc)
            dx = random.randint(25,80)*random.choice([-1,1])
            dy = random.randint(25,80)*random.choice([-1,1])
            bezier_move(x+dx, y+dy); pag.click(); time.sleep(0.3)
    elif event == "scroll_spam":
        for _ in range(random.randint(3,7)):
            pag.scroll(random.randint(-300,300)); time.sleep(.1)
    elif event == "camera_circle":
        cx,cy = pag.position(); r=random.randint(20,40)
        for a in range(0,360,45):
            pag.moveTo(cx+int(r*math.cos(math.radians(a))),
                       cy+int(r*math.sin(math.radians(a))), duration=.05)

# ───────────────── Mouse helpers (Fitts+Bézier) ───────────────────
def _curve(st,en):
    sx,sy = st; ex,ey = en
    pts,segs = [], random.randint(SEGMENT_MIN,SEGMENT_MAX)
    for i in range(1,segs):
        t=i/segs; off=random.randint(-15,15)
        cx=sx+(ex-sx)*t+off; cy=sy+(ey-sy)*t+off
        pts.append((int((1-t)*sx+t*cx), int((1-t)*sy+t*cy)))
    pts.append((ex,ey)); return pts

def fitts_time(d,w,a=.05,b=.05): return a + b*math.log2(1+d/w)

def bezier_move(tx,ty):
    cx,cy = pag.position()
    if random.random() < overshoot_chance:
        dx=random.choice([-1,1])*random.randint(4,8)
        dy=random.choice([-1,1])*random.randint(4,8)
        path=_curve((cx,cy),(tx+dx,ty+dy))+_curve((tx+dx,ty+dy),(tx,ty))
    else:
        path=_curve((cx,cy),(tx,ty))
    W=random.uniform(32,48)
    total=sum(math.hypot(px-sx,py-sy) for (sx,sy),(px,py) in zip(path[:-1],path[1:])) or 1
    T=fitts_time(total,W,a=random.uniform(.04,.06),b=random.uniform(.04,.07))
    for (sx,sy),(px,py) in zip(path[:-1],path[1:]):
        seg=math.hypot(px-sx,py-sy)
        pag.moveTo(px,py,duration=clamp(seg/total*T,.01,.40),
                   tween=random.choice(TWEEN_FUNCS))

def idle_wiggle():
    x,y=pag.position()
    pag.moveTo(x+pink.next(),y+pink.next(),duration=random.uniform(.02,.05))

# ───────────────── Magic tab helper ───────────────────────────────
def click_magic_tab():
    if safe_locate(MAGIC_OPEN_IMAGE, confidence=OPEN_CONFIDENCE, grayscale=True):
        return True
    tab=safe_locate(MAGIC_TAB_IMAGE, confidence=CONFIDENCE, grayscale=True)
    if tab:
        bezier_move(*pag.center(tab)); pag.click(); time.sleep(.15)
        return True
    log("⚠️ Could not open Magic tab.")
    return False

# ───────────────── Edge / YouTube helpers ─────────────────────────
def edge_windows():
    return [w for w in gw.getAllWindows()
            if not w.isMinimized and ('Edge' in w.title or 'Microsoft Edge' in w.title)]

def click_edge_youtube():
    wins=edge_windows()
    if not wins: return False
    win=random.choice(wins)
    tx=random.randint(win.left+60, win.right-60)
    ty=random.randint(win.top+100, win.bottom-100)
    bezier_move(tx,ty); pag.click(); return True

def scroll_loop(dur):
    end=time.time()+dur
    while time.time()<end and bot_active:
        pag.scroll(random.randint(-600,600))
        time.sleep(random.uniform(.5,1.4))

# ───────────────── Random tab-flipping idle loop ──────────────────
def random_tab_loop(duration):
    mu = clamp(random.gauss(4.0,0.7), 2.0, 7.0)   # mean sec between flips
    lam = 1.0 / mu
    t_next = time.time() + random.expovariate(lam)
    end = time.time() + duration
    while t_next < end and bot_active:
        time.sleep(max(0, t_next - time.time()))
        tab_img = random.choice(TAB_IMAGES)
        loc = safe_locate(tab_img, confidence=CONFIDENCE, grayscale=True)
        if loc: bezier_move(*pag.center(loc)); pag.click()
        t_next += random.expovariate(lam)

# ───────────────── Stats-hover helper ─────────────────────────────
def stats_hover(dur)->bool:
    stats=safe_locate(STATS_IMAGE, confidence=STATS_CONFIDENCE, grayscale=True)
    if not stats: return False
    bezier_move(*pag.center(stats)); pag.click(); time.sleep(.2)
    magic=safe_locate(MAGICLVL_IMAGE, confidence=STATS_CONFIDENCE, grayscale=True)
    if not magic: return False
    bezier_move(*pag.center(magic))
    end=time.time()+dur
    while time.time()<end and bot_active:
        if feature("idle_wiggle"): idle_wiggle()
        maybe_outlier_event("rest"); time.sleep(.25)
    return True

# ───────────────── Short-rest handler ─────────────────────────────
def default_rest(dur):
    ch=random.random()
    if ch<.60 and click_edge_youtube():
        scroll_loop(dur)
    else:
        random_tab_loop(dur)
    click_magic_tab()

def handle_short_rest(rest):
    if rest<.25: return
    maybe_outlier_event("rest")
    if STATS_REST_TEST_MODE or random.random()<STATS_REST_PROB:
        if not stats_hover(rest):
            default_rest(rest)
    else:
        default_rest(rest)

# ───────────────── AFK handler (unchanged) ────────────────────────
def handle_afk():
    global next_afk_time
    if time.time()<next_afk_time: return
    long_prob=random.betavariate(2.2,5.0)
    is_long=random.random()<long_prob
    dur=gamma_between(53,300,2.1) if is_long else gamma_between(1,47,2.1)
    log(f"{'Long' if is_long else 'Short'} AFK: {int(dur)} s")
    ch=random.random()
    if (ch<.60 if is_long else ch<.50) and click_edge_youtube():
        scroll_loop(dur)
    else:
        end=time.time()+dur
        while time.time()<end and bot_active:
            maybe_outlier_event("afk"); time.sleep(.5)
    next_afk_time=time.time()+gamma_between(AFK_MIN_SECS,AFK_MAX_SECS,2.4)
    click_magic_tab()

# ───────────────── Click-spam session ─────────────────────────────
def spam_session():
    burst=gaussian_between(SPAM_MIN,SPAM_MAX)
    rest =gaussian_between(REST_MIN,REST_MAX)

    # Always click the Magic tab before attempting to locate the teleport.
    # Sometimes random tab flips leave another tab active which prevents the
    # teleport icon from being found. Clicking the Magic tab each session is
    # cheap and ensures the spellbook is visible.
    click_magic_tab()

    loc=safe_locate(TELEPORT_IMAGE, confidence=CONFIDENCE, grayscale=True)
    if not loc:
        log("Teleport rune not found; clicking Magic tab...")
        if not click_magic_tab():
            log("Teleport rune not found and could not open Magic tab; skipping burst.")
            return
        loc=safe_locate(TELEPORT_IMAGE, confidence=CONFIDENCE, grayscale=True)
        if not loc:
            log("Teleport rune still not found; skipping burst."); return
    x,y = pag.center(loc)
    log(f"Click burst {burst:.1f}s at {(x,y)}")
    end=time.time()+burst
    while time.time()<end and bot_active:
        handle_afk(); maybe_outlier_event("burst")
        bezier_move(x+random.randint(-2,2), y+random.randint(-2,2))
        if feature("finger_hesitation"): time.sleep(random.uniform(.05,.15))
        pag.mouseDown(); time.sleep(lognorm_between(.010,.060)); pag.mouseUp()
        if feature("double_click"): time.sleep(random.uniform(.03,.08)); pag.click()
        gap=gamma_between(.12,.60,2.5) if feature("drift_click_timing") \
            else random.uniform(.06,1.00)
        time.sleep(gap)
        if feature("idle_wiggle"): idle_wiggle()
    log(f"Burst done. Rest {rest:.1f}s...")
    handle_short_rest(rest)

# ───────────────── Hotkey thread ──────────────────────────────────
def hotkey_thread():
    global bot_active
    while True:
        if keyboard.is_pressed('f1'):
            bot_active = not bot_active
            log("Bot paused." if not bot_active else "Bot resumed.")
            time.sleep(.4)
        if keyboard.is_pressed('f2'):
            toggle_console()
            time.sleep(.4)
        if keyboard.is_pressed('f3'):
            log("Bot stopped (F3)."); os._exit(0)
        time.sleep(.05)

# ───────────────── Main loop ───────────────────────────────────────
def main_loop():
    global loop_counter,next_weight_refresh
    while True:
        if not bot_active:
            time.sleep(.25); continue
        loop_counter+=1
        if loop_counter>=next_weight_refresh:
            refresh_weights()
            next_weight_refresh=loop_counter+int(abs(random.gauss(LOOP_MEAN,LOOP_SD))+1)
        handle_afk(); spam_session()

# ───────────────── Entry ───────────────────────────────────────────
if __name__=="__main__":
    hide_console()
    threading.Thread(target=hotkey_thread, daemon=True).start()
    refresh_weights()
    next_weight_refresh=int(abs(random.gauss(LOOP_MEAN,LOOP_SD))+1)
    log(f"Bot started spamming {choice}. F1=pause • F3=quit")
    try:
        main_loop()
    except Exception as e:
        log(f"Fatal error: {e}")
        traceback.print_exc()
