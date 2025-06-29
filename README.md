# Python OSRS Teleport Bot

This project contains **EssayReview.pyw**, a teleport spam bot for Old School RuneScape. It repeatedly clicks a teleport spell using human-like mouse movement and randomised delays. Logs and status messages appear in a draggable overlay provided by `DraftTracker.py`.

## Features

- Supports Varrock, Falador and Camelot teleports (prompted at start).
- Overlay HUD showing recent log lines and a magic cape image.
- Anti-ban behaviour with varying click timings and occasional idle actions.
- Randomised cursor speed for more human-like movement.
- Optional "robust click" mode that holds the mouse
  button down briefly so clicks aren't missed on some setups.
- Option to disable all AFK events in the configuration window.
- New toggles let you disable stats hovering, Edge/YouTube AFK tasks
  random tab flips and the short rest between bursts if desired.
- Simple login helper that clicks the RuneScape launcher buttons.
- Hotkeys: **1** to pause/resume, **2** to toggle the console, **3** to quit.

## Prerequisites

Python 3.9+ on Windows.

Install the required packages with:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file lists:

- `pyautogui`
- `pygetwindow`
- `Pillow`
- `keyboard`
- `pywin32` (for the overlay window)

## Running

Run the bot from this directory:

```
python -m src.EssayReview
```

The script uses the `.pyw` extension so that no extra console window
opens on Windows. If you prefer to see the console output you can
rename it to `EssayReview.py` and launch it the same way. Logs now always
print to the terminal so you can monitor activity and debug issues.


 A configuration window first lets you choose the teleport and toggle options like the overlay, mouse overshoot, velocity limit and robust click mode. Additional checkboxes control stats hovering, Edge/YouTube AFK tasks, tab flipping and the short rest after each burst. You can also enter the confidence threshold used to locate `Cam.png` (or other teleport icons). The default value is **0.8**. After clicking **Start** the bot begins spamming the chosen teleport. When enabled, the overlay window appears near the RuneLite window and can be dragged or resized; its geometry is saved in `overlay_pos.json`.

On non-Windows systems the window is only shown when the `DISPLAY` environment variable is set. It is also skipped automatically during test runs.

Press **1** at any time to pause or resume automation. Press **2** to show or hide the console window. Press **3** to stop the bot completely. If the teleport tab still cannot be found after the bot attempts to open it, it will press **F6** automatically as a fallback.

