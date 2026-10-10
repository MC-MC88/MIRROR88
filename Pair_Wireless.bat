@echo off
title Mirror88 - Pair Wireless
cd /d "%~dp0"

if not exist "platform-tools\adb.exe" (
    echo.
    echo  Please run Start_Mirror88.bat first to download ADB.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   WIRELESS PAIRING
echo  ============================================
echo.
echo   On your phone (Android 11+):
echo     1. Settings - Developer options
echo     2. Enable "Wireless debugging"
echo     3. Tap "Pair device with pairing code"
echo     4. You will see: IP:PORT and a 6-digit code
echo.
echo   Enter that IP:PORT below when asked.
echo.
echo  ============================================
echo.

"platform-tools\adb.exe" pair

echo.
echo  If pairing succeeded, now run Connect_Wireless.bat
echo.
pause
