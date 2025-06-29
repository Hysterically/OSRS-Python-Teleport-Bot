# =============================================================================
# DraftTracker.py – Overlay HUD with Magic Cape  (v3, GC-safe)
# =============================================================================
# • Drag anywhere to move   • Drag ◢ grip to resize (geometry saved)
# • Text log (left) + scalable magiccape.png (right)
# • Public API: update_log(msg), set_cape_scale(factor)
# • Fix B applied: keeps a list of *all* PhotoImages so Tcl never
#   loses the image handle (eliminates “pyimageX doesn’t exist” crashes)
# =============================================================================
import win32gui
import pyautogui as pag
import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import threading
import queue
import json
import os

# absolute paths ------------------------------------------------------------
PKG_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(PKG_DIR, os.pardir))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")


class DraftTracker:
    # ---------- CONFIG ----------
    GAME_TITLE = "RuneLite – I am Hys"
    IMG_FILE = os.path.join(ASSETS_DIR, "magiccape.png")
    SAVE_FILE = os.path.join(ROOT_DIR, "overlay_pos.json")
    OPACITY = 0.85
    DEFAULT_W = 800
    DEFAULT_H = 140
    MAX_LINES = 6
    CAPE_BASE_H = 96

    # ---------- public API ----------
    def update_log(self, msg: str) -> None:
        self.queue.put(msg)

    def set_cape_scale(self, factor: float) -> None:
        self._cape_scale = max(0.2, min(factor, 3.0))
        if hasattr(self, "_root"):  # schedule on GUI thread
            self._root.after(0, self._load_cape)

    # ---------- ctor ----------
    def __init__(self):
        self.queue: queue.Queue[str] = queue.Queue()
        self.lines: list[str] = []
        self._cape_scale = 1.0
        self._images: list[ImageTk.PhotoImage] = []  # <<< Fix B container
        x, y, w, h = self._load_geom() or self._fallback_geom()
        threading.Thread(target=self._run_gui, args=(x, y, w, h), daemon=True).start()

    # ---------- geometry ----------
    def _load_geom(self):
        if os.path.isfile(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, "r") as f:
                    g = json.load(f)
                    return g["x"], g["y"], g["w"], g["h"]
            except Exception:
                pass
        return None

    def _save_geom(self, root):
        try:
            with open(self.SAVE_FILE, "w") as f:
                json.dump(
                    dict(
                        x=root.winfo_x(),
                        y=root.winfo_y(),
                        w=root.winfo_width(),
                        h=root.winfo_height(),
                    ),
                    f,
                )
        except Exception:
            pass

    def _fallback_geom(self):
        hwnd = win32gui.FindWindow(None, self.GAME_TITLE)
        if hwnd:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            w, h = self.DEFAULT_W, self.DEFAULT_H
            x = l + (r - l - w) // 2
            y = b
        else:
            sw, sh = pag.size()
            w, h = self.DEFAULT_W, self.DEFAULT_H
            x = (sw - w) // 2
            y = sh - h - 50
        return x, y, w, h

    # ---------- GUI THREAD ----------
    def _run_gui(self, x0, y0, w0, h0):
        self._root = root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", self.OPACITY)
        root.geometry(f"{w0}x{h0}+{x0}+{y0}")
        root.configure(bg="black")

        outer = tk.Frame(root, bg="black")
        outer.pack(fill="both", expand=True, padx=4, pady=4)

        log_lbl = tk.Label(
            outer,
            fg="lime",
            bg="black",
            font=("Consolas", 10),
            justify="left",
            anchor="nw",
        )
        log_lbl.pack(side="left", fill="both", expand=True)

        self._cape_label = tk.Label(outer, bg="black")
        self._cape_label.pack(side="right", anchor="ne", padx=(8, 0))
        self._load_cape()

        ttk.Sizegrip(root).place(relx=1.0, rely=1.0, anchor="se")

        drag = {"x": 0, "y": 0}
        root.bind("<ButtonPress-1>", lambda e: drag.update(x=e.x_root, y=e.y_root))
        root.bind(
            "<B1-Motion>",
            lambda e: (
                root.geometry(
                    f"+{root.winfo_x() + e.x_root - drag['x']}+"
                    f"{root.winfo_y() + e.y_root - drag['y']}"
                ),
                drag.update(x=e.x_root, y=e.y_root),
            ),
        )
        root.bind("<ButtonRelease-1>", lambda _: self._save_geom(root))

        def on_conf(_):
            tid = getattr(root, "_save_after", None)
            if isinstance(tid, int):
                root.after_cancel(tid)
            root._save_after = root.after(350, lambda: self._save_geom(root))

        root.bind("<Configure>", on_conf)

        def poll():
            updated = False
            try:
                while True:
                    line = self.queue.get_nowait()
                    self.lines.append(line)
                    if len(self.lines) > self.MAX_LINES:
                        self.lines.pop(0)
                    updated = True
            except queue.Empty:
                pass
            if updated:
                log_lbl.config(text="\n".join(self.lines))
            root.after(100, poll)

        poll()

        root.mainloop()

    # ---------- image loader ----------
    def _load_cape(self):
        path = self.IMG_FILE
        if not os.path.isfile(path):
            self.update_log(f"❌ {os.path.basename(self.IMG_FILE)} not found")
            return
        try:
            with Image.open(path) as im:
                img = im.convert("RGBA")
            target_h = int(self.CAPE_BASE_H * self._cape_scale)
            scale = target_h / img.height
            img = img.resize((int(img.width * scale), target_h), Image.LANCZOS)
            cap_img = ImageTk.PhotoImage(img, master=self._root)
            self._images.append(cap_img)  # <<< keep reference
            self._cape_label.image = cap_img  # keep via widget
            self._cape_label.config(image=cap_img)
            self.update_log("🧙‍♂️  Cape image loaded ✔")
        except Exception as e:
            self.update_log(f"❌ Cape load error: {e}")
            print("[DraftTracker] load error:", e)
