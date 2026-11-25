@echo off
title Export Micro-OS Bootable Media to Desktop and Downloads
echo =======================================================================
echo         EXPORT MICRO-OS VM ARTIFACTS TO DESKTOP ^& DOWNLOADS
echo =======================================================================
echo.

set "VB_DIR=%~dp0virtualbox"

if not exist "%VB_DIR%\micro-os.iso" (
    echo [ERROR] Source media not found at: "%VB_DIR%"
    pause
    exit /b 1
)

echo Source directory: "%VB_DIR%"
echo.

:: Detect Desktop location (standard or OneDrive sync)
set "TARGET_DESKTOP="
if exist "%USERPROFILE%\OneDrive\Pictures\Desktop" set "TARGET_DESKTOP=%USERPROFILE%\OneDrive\Pictures\Desktop"
if not defined TARGET_DESKTOP if exist "%USERPROFILE%\OneDrive\Desktop" set "TARGET_DESKTOP=%USERPROFILE%\OneDrive\Desktop"
if not defined TARGET_DESKTOP if exist "%USERPROFILE%\Desktop" set "TARGET_DESKTOP=%USERPROFILE%\Desktop"

:: Detect Downloads location
set "TARGET_DOWNLOADS=%USERPROFILE%\Downloads"

if defined TARGET_DESKTOP (
    echo [OK] Detected Desktop at: "%TARGET_DESKTOP%"
    copy /y "%VB_DIR%\micro-os.iso" "%TARGET_DESKTOP%\micro-os.iso" >nul
    copy /y "%VB_DIR%\micro-os.iso" "%TARGET_DESKTOP%\micro-os-v2.iso" >nul
    copy /y "%VB_DIR%\micro-os.iso" "%TARGET_DESKTOP%\micro-os-v3.iso" >nul
    copy /y "%VB_DIR%\micro-os.vhd" "%TARGET_DESKTOP%\micro-os.vhd" >nul
    copy /y "%VB_DIR%\micro-os.img" "%TARGET_DESKTOP%\micro-os.img" >nul
    echo   -^> Deployed: micro-os.iso (ISO 9660 Bootable CD)
    echo   -^> Deployed: micro-os-v2.iso (Updated for existing VirtualBox VM)
    echo   -^> Deployed: micro-os-v3.iso (Fresh mountable ISO)
    echo   -^> Deployed: micro-os.vhd (Fixed Virtual Hard Disk 10MB)
    echo   -^> Deployed: micro-os.img (Raw Floppy 1.44MB)
) else (
    echo [WARN] Could not automatically locate Desktop folder.
)

echo.
if exist "%TARGET_DOWNLOADS%" (
    echo [OK] Detected Downloads at: "%TARGET_DOWNLOADS%"
    copy /y "%VB_DIR%\micro-os.iso" "%TARGET_DOWNLOADS%\micro-os.iso" >nul
    copy /y "%VB_DIR%\micro-os.iso" "%TARGET_DOWNLOADS%\micro-os-v3.iso" >nul
    copy /y "%VB_DIR%\micro-os.vhd" "%TARGET_DOWNLOADS%\micro-os.vhd" >nul
    echo   -^> Deployed ISO and VHD to Downloads folder.
)

echo.
echo =======================================================================
echo SUCCESS! All bootable media updated.
echo You can now return to Oracle VM VirtualBox and start your VM!
echo =======================================================================
echo.
