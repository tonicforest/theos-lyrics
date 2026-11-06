@echo off
title Theos Lyrics - Installer

echo.
echo =================================
echo       THEOS LYRICS INSTALLER
echo =================================
echo.

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.12 was not found.
    echo Install Python 3.12 and enable the Python Launcher.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 goto error
)

echo Updating pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error

echo Installing dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo Installation completed!
pause
exit /b 0

:error
echo.
echo Installation failed. Check the error above.
pause
exit /b 1
