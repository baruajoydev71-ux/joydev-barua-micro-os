@echo off
title Micro-OS - Rust Kernel Execution
echo =======================================================================
echo                 MICRO-OS RUST KERNEL EXECUTION
echo =======================================================================
echo.

:: Check for Cargo in PATH or standard user location
set CARGO_EXE=
where cargo >nul 2>&1
if %errorlevel% equ 0 (
    set "CARGO_EXE=cargo"
) else if exist "%USERPROFILE%\.cargo\bin\cargo.exe" (
    set "CARGO_EXE=%USERPROFILE%\.cargo\bin\cargo.exe"
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

if "%CARGO_EXE%"=="" (
    echo [ERROR] Rust / Cargo is NOT installed on this machine yet!
    echo.
    echo Why is this happening?
    echo   Windows does not include the Rust compiler by default.
    echo.
    echo How to fix this:
    echo   Option A (Recommended):
    echo     Open PowerShell and run:
    echo       winget install Rustlang.Rustup
    echo.
    echo   Option B:
    echo     Download and run 'rustup-init.exe' from:
    echo       https://win.rustup.rs
    echo.
    echo After installing Rust, close this window and double-click 'run_kernel.bat' again.
    echo.
    pause
    exit /b 1
)

echo [OK] Found Cargo at: "%CARGO_EXE%"
echo.
cd /d "%~dp0"

echo -----------------------------------------------------------------------
echo 1. RUNNING COMPARATIVE EVALUATION (Round Robin vs MLFQ)
echo -----------------------------------------------------------------------
"%CARGO_EXE%" run -- --compare
echo.

echo -----------------------------------------------------------------------
echo 2. RUNNING FORMAL VERIFICATION TEST SUITE (TC1 to TC6)
echo -----------------------------------------------------------------------
"%CARGO_EXE%" run -- --test-all
echo.

echo =======================================================================
echo Execution complete!
echo =======================================================================
pause
