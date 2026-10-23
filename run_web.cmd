@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project virtual environment is missing. See README.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" web_app.py %*
if errorlevel 1 pause
