@echo off
title Micro-OS - Oracle VM VirtualBox Launcher
echo =======================================================================
echo              MICRO-OS ORACLE VM VIRTUALBOX LAUNCHER
echo =======================================================================
echo.

set VBOX_EXE=
if exist "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" (
    set "VBOX_EXE=C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
) else (
    where VBoxManage >nul 2>&1
    if %errorlevel% equ 0 (
        set "VBOX_EXE=VBoxManage"
    )
)

if "%VBOX_EXE%"=="" (
    echo [NOTICE] Oracle VM VirtualBox is not detected in standard program files.
    echo.
    echo How to run Micro-OS in VirtualBox:
    echo   1. If VirtualBox is not installed:
    echo      Install it via PowerShell:
    echo        winget install Oracle.VirtualBox
    echo      Or download from: https://www.virtualbox.org
    echo.
    echo   2. Once VirtualBox is installed:
    echo      - Open VirtualBox
    echo      - Click "Machine" -> "Add..." (or press Ctrl+A)
    echo      - Select the file: "%~dp0Micro-OS.vbox"
    echo      - Click "Start" (Green arrow)!
    echo.
    echo   3. Alternatively, boot directly in QEMU if installed:
    echo        qemu-system-x86_64 -cdrom "%~dp0micro-os.iso" -serial stdio
    echo.
    pause
    exit /b 0
)

echo [OK] Found VirtualBox at: "%VBOX_EXE%"
echo.
echo Registering Micro-OS VM in VirtualBox...
"%VBOX_EXE%" registervm "%~dp0Micro-OS.vbox" >nul 2>&1

echo Starting Micro-OS Virtual Machine...
"%VBOX_EXE%" startvm "Micro-OS"
echo.
echo VirtualBox VM launched! Check the VirtualBox window on your screen.
echo.
pause
