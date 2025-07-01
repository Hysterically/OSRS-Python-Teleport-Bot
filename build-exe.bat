@echo off
REM Build EssayReview.exe using PyInstaller

REM Ensure we're in the project directory
cd /d "%~dp0"

REM Install PyInstaller if missing
python -m pip install --upgrade pyinstaller

REM Build the executable
pyinstaller --onefile --windowed --name EssayReview ^
    --add-data "assets;assets" src\EssayReview.pyw

echo.
echo ✅ Build complete. Executable is in the dist folder.
pause
