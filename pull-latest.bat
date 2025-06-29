@echo off
title EssayReview Updater
echo ===============================
echo   EssayReview Bot – Auto Pull
echo ===============================
echo.

REM Navigate to your bot folder
cd /d "C:\Users\HaloWarsDE\Desktop\Essays"

REM Pull latest changes
git pull origin main

echo.
echo ✅ Bot updated from GitHub.
echo Press any key to close...
pause >nul
