@echo off
REM Wrapper script to build the EssayReview executable

REM Ensure we're in the project directory
cd /d "%~dp0"

REM Call the actual build script
call build-exe.bat

