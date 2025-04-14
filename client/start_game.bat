@echo off
echo ====================================
echo       CODEBREAK GAME LAUNCHER
echo ====================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in your PATH.
    echo Please install Python 3.8 or newer from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking requirements...
pip show pygame > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages.
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo.
echo Starting CodeBreak...
echo.
python codebreak_launcher.py --skip-server

REM If the game crashes, show an error message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo The game encountered an error.
    echo If this persists, please contact support.
)

pause