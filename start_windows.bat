@echo off
title Theos Lyrics

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Please run install_windows.bat first.
    pause
    exit /b 1
)

.venv\Scripts\python.exe main_windows.py

if errorlevel 1 (
    echo.
    echo Theos Lyrics exited with an error.
    pause
)
