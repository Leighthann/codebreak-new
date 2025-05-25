@echo off
echo Starting CodeBreak Game...

REM Check and install dependencies first
echo Checking dependencies...
python install_dependencies.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Start the game launcher
python unified_game_launcher.py
pause 