# Python OSRS Teleport Bot

This project contains **EssayReview.pyw**, a teleport spam bot for Old School RuneScape. It repeatedly clicks a teleport spell using human-like mouse movement and randomised delays. Logs are printed to the terminal.

## Features

- Supports Varrock, Falador and Camelot teleports (prompted at start).
- Anti-ban behaviour with varying click timings and occasional idle actions.
- Randomised cursor speed for more human-like movement.
- Optional "robust click" mode that holds the mouse
  button down briefly so clicks aren't missed on some setups.
- Option to disable all AFK events in the configuration window.
- Toggle to enable verbose debug logging when troubleshooting.
- New toggles let you disable stats hovering, Edge/YouTube AFK tasks
  random tab flips and the short Mini-AFK between bursts if desired.
- Three sliders set the chance of Mini-AFK, short and long AFK breaks
  (0\% never, 100\% always) and default to 50\%.
- The Mini-AFK rest after each burst now always lasts between 5 and 11 seconds.
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

## Running

Run the bot from this directory:

```
python -m src.EssayReview
```

The script uses the `.pyw` extension so that no extra console window
opens on Windows. If you prefer to see the console output you can
rename it to `EssayReview.py` and launch it the same way. Logs now always
print to the terminal so you can monitor activity and debug issues.


A configuration window first lets you choose the teleport and toggle options like mouse overshoot, velocity limit and robust click mode. Additional checkboxes control stats hovering, Edge/YouTube AFK tasks, tab flipping and the short Mini-AFK after each burst. Three sliders set the chance of Mini-AFK, short and long AFK breaks (0% never, 100% always). You can also enter the confidence threshold used to locate `Cam.png` (or other teleport icons). The default value is **0.8**. After clicking **Start** the bot begins spamming the chosen teleport.

On non-Windows systems the window is only shown when the `DISPLAY` environment variable is set. It is also skipped automatically during test runs.

Press **1** at any time to pause or resume automation. Press **2** to show or hide the console window. Press **3** to stop the bot completely. If the teleport tab still cannot be found after the bot attempts to open it, it will press **F6** automatically as a fallback.

## Building an executable

Use the `build.bat` script to create an executable version of the bot. This
wrapper simply invokes `build-exe.bat`, which includes the `assets` folder so
the bundled executable can locate the image files it needs. `EssayReview.pyw`
checks the `sys._MEIPASS` attribute when running from PyInstaller so the assets
load correctly:

```cmd
build.bat
```

The generated `EssayReview.exe` will appear inside the `dist` folder.

