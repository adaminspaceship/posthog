@echo off
title PostHog
echo Starting PostHog...
echo.
echo This window will display startup progress and log information.
echo Please do not close this window while using PostHog.
echo.

REM Get the directory of this batch file
set SCRIPT_DIR=%~dp0

REM Run the Python launcher script with the bundled Python interpreter
"%SCRIPT_DIR%python\python.exe" "%SCRIPT_DIR%standalone_launcher.py"

echo.
echo PostHog has been shut down.
echo You can close this window now.
pause 