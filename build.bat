@echo off
echo PostHog Windows Executable Builder
echo =================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.11 from https://www.python.org/downloads/
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Node.js is not installed or not in PATH.
    echo Please install Node.js 18.x from https://nodejs.org/
    exit /b 1
)

REM Check if PNPM is installed
pnpm --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PNPM is not installed or not in PATH.
    echo Please install PNPM by running: npm install -g pnpm
    exit /b 1
)

REM Check if PostHog source exists
if not exist posthog-master (
    echo PostHog source code not found.
    echo Please clone the PostHog repository first:
    echo git clone https://github.com/PostHog/posthog.git posthog-master
    exit /b 1
)

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Run the build script
echo.
echo Starting build process...
python build_windows_exe.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo The PostHog Windows executable is available in posthog-windows.zip
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    echo Please check the console output for details.
)

pause 