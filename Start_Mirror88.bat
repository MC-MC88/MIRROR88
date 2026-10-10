@echo off
title Mirror88 - Phone Screen Mirror
cd /d "%~dp0"

REM --- Python check ---
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo  Python was not found on this PC.
    echo  Install it from https://python.org
    echo  and check "Add Python to PATH" during setup.
    echo.
    pause
    exit /b 1
)

REM --- ADB auto-download if missing ---
if not exist "platform-tools\adb.exe" (
    echo.
    echo  Downloading Android Platform Tools, please wait...
    echo  This happens only the first time.
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "try { Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'platform-tools.zip' -UseBasicParsing } catch { exit 1 }"
    if errorlevel 1 (
        echo.
        echo  Download failed. Check your internet connection.
        pause
        exit /b 1
    )
    echo  Extracting...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Expand-Archive -Path 'platform-tools.zip' -DestinationPath '.' -Force"
    del /q platform-tools.zip 2>nul
    echo  ADB ready.
)

REM --- Python virtual environment ---
if not exist ".venv" (
    echo.
    echo  Setting up Mirror88 for the first time, please wait...
    echo.
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

cls
python mirror88.py

pause
