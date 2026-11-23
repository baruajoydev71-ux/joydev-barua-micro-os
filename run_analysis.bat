@echo off
title "Micro-OS - Python Trace Analysis and Visualizer"
echo =======================================================================
echo          MICRO-OS TRACE ANALYSIS AND GANTT VISUALIZER
echo =======================================================================
echo.

:: Detect Python executable
set PYTHON_EXE=
if exist "C:\Program Files\Spyder\Python\python.exe" (
    set "PYTHON_EXE=C:\Program Files\Spyder\Python\python.exe"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python was not found!
    echo Please install Python 3.8+ or check your path.
    pause
    exit /b 1
)

echo [OK] Using Python at: "%PYTHON_EXE%"
echo.
echo -----------------------------------------------------------------------
echo 1. PARSING SERIAL TRACE LOGS AND COMPUTING OS METRICS...
echo -----------------------------------------------------------------------
"%PYTHON_EXE%" "%~dp0scripts\analyze_traces.py"
echo.
echo -----------------------------------------------------------------------
echo 2. GENERATING ASCII GANTT TIMELINE CHARTS...
echo -----------------------------------------------------------------------
"%PYTHON_EXE%" "%~dp0scripts\visualize.py"
echo.
echo -----------------------------------------------------------------------
echo 3. GENERATING HIGH-RESOLUTION PLOTS IN results\...
echo -----------------------------------------------------------------------
"%PYTHON_EXE%" "%~dp0scripts\generate_plots.py"
echo.
echo =======================================================================
echo Analysis complete! 
echo Check the generated plots in: %~dp0results\
echo =======================================================================
echo.
pause
