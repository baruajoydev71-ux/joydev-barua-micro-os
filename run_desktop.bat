@echo off
title Launch Joydev Micro-OS Graphical Desktop
echo =======================================================================
echo          LAUNCHING JOYDEV MICRO-OS GRAPHICAL DESKTOP
echo =======================================================================
echo.

set "BRIDGE_SCRIPT=C:\Users\barua\.gemini\antigravity\scratch\micro-os\desktop\wifi_bridge.py"
set "HTML_PATH=C:\Users\barua\.gemini\antigravity\scratch\micro-os\desktop\index.html"
set "PYTHON_BIN="

if exist "%LOCALAPPDATA%\Python\bin\pythonw.exe" set "PYTHON_BIN=%LOCALAPPDATA%\Python\bin\pythonw.exe"
if not defined PYTHON_BIN (
    for /f "delims=" %%P in ('where pythonw 2^>nul') do if not defined PYTHON_BIN set "PYTHON_BIN=%%P"
)
if not defined PYTHON_BIN if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PYTHON_BIN=%LOCALAPPDATA%\Python\bin\python.exe"
if not defined PYTHON_BIN (
    for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_BIN set "PYTHON_BIN=%%P"
)

set "APP_URL=file:///%HTML_PATH:\=/%"

if defined PYTHON_BIN if exist "%BRIDGE_SCRIPT%" (
    echo Starting Live Host Wi-Fi Bridge on http://127.0.0.1:8765 ...
    start "" "%PYTHON_BIN%" "%BRIDGE_SCRIPT%"
    ping 127.0.0.1 -n 2 >nul
    set "APP_URL=http://127.0.0.1:8765/"
)

echo Opening Joydev Micro-OS Desktop (%APP_URL%)...

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="%APP_URL%" --start-maximized
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="%APP_URL%" --start-maximized
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app="%APP_URL%" --start-maximized
) else (
    start "" "%APP_URL%"
)

exit /b 0
