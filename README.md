# Python OSRS Teleport Bot

This project contains **EssayReview.pyw**, a teleport spam bot for Old School RuneScape. It repeatedly clicks a teleport spell using human-like mouse movement and randomised delays. Logs and status messages appear in a draggable overlay provided by `DraftTracker.py`.

## Features

- Supports Varrock, Falador and Camelot teleports (prompted at start).
- Overlay HUD showing recent log lines and a magic cape image.
- Anti-ban behaviour with varying click timings and occasional idle actions.
- Hotkeys: **Space** to pause/resume, **Esc** to quit immediately.

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
python EssayReview.pyw
```

The script uses the `.pyw` extension so that no extra console window
opens on Windows. If you prefer to see the console output you can
rename it to `EssayReview.py` and launch it the same way.

A prompt asks which teleport to spam-click. After selecting a teleport, the bot begins clicking. The overlay window appears near the RuneLite window and can be dragged or resized; geometry is saved in `overlay_pos.json`.

Press **Space** at any time to pause or resume automation. Press **Esc** to stop the bot completely.

