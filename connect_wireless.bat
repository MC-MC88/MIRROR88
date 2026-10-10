@echo off
title Mirror88 - Connect Wireless
cd /d "%~dp0"

if not exist "platform-tools\adb.exe" (
    echo.
    echo  Please run Start_Mirror88.bat first to download ADB.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   WIRELESS CONNECT
echo  ============================================
echo.
echo   On your phone: Developer options - Wireless debugging
echo   Look at the MAIN screen (not the pairing dialog).
echo   It shows: IP address and PORT
echo.
echo   Enter that IP:PORT below.
echo.
echo  ============================================
echo.

set /p TARGET="IP:PORT  = "
"platform-tools\adb.exe" connect %TARGET%

echo.
"platform-tools\adb.exe" devices
echo.
echo  If your phone shows as "device", you are ready.
echo  Now run Start_Mirror88.bat
echo.
pause
