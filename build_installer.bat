@echo off
echo PostHog Windows Standalone Installer Builder
echo =============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    exit /b 1
)

REM Check for admin rights
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo This script requires administrator privileges.
    echo Please run as administrator to continue.
    exit /b 1
)

echo This script will download and build a standalone offline Windows installer for PostHog.
echo The build process requires an internet connection and may take some time.
echo.
echo Press Ctrl+C to cancel, or any key to continue...
pause >nul

REM Run the build script
python build_standalone.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo The installer is available in the output directory.
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    echo Please check the console output for details.
)

pause 