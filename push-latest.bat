@echo off
title EssayReview Bot – Push to GitHub
echo ================================
echo     EssayReview Git Pusher
echo ================================
echo.

REM Navigate to project folder
cd /d "C:\Users\HaloWarsDE\Desktop\Essays"

REM Stage all changes
git add .

REM Prompt for a commit message
set /p msg=Enter commit message: 
git commit -m "%msg%"

REM Push to main branch
git push origin main

echo.
echo ✅ Push complete. Press any key to close...
pause >nul
