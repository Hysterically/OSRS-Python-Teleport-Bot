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
  random tab flips and the short rest between bursts if desired.
- Entry to adjust how often short AFK tasks occur during those rests.
- Slider to control how frequently the bot takes AFK breaks.
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


Use the config window to choose a teleport and turn features on or off.
Check boxes for overshoot, stats hover, tab flips and other options.
Set break rate and icon confidence, then click **Start** to begin.

On non-Windows systems the window is only shown when the `DISPLAY` environment variable is set. It is also skipped automatically during test runs.

Press **1** at any time to pause or resume automation. Press **2** to show or hide the console window. Press **3** to stop the bot completely. If the teleport tab still cannot be found after the bot attempts to open it, it will press **F6** automatically as a fallback.

## Building an executable

Use the `build-exe.bat` script to create an executable version of the bot. This
script now includes the `assets` folder so the bundled executable can locate the
image files it needs. `EssayReview.pyw` checks the `sys._MEIPASS` attribute when
running from PyInstaller so the assets load correctly:

```cmd
build-exe.bat
```

The generated `EssayReview.exe` will appear inside the `dist` folder.

