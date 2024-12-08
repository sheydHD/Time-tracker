@echo off
REM Navigate to the script's directory
cd /d "%~dp0"

REM Initialize the database
echo Initializing database...
python init_db.py

REM Run PyInstaller to build the executable
echo Building executable...
pyinstaller time_tracker.spec

REM Notify the user that the build is completed
echo Build completed. Check the 'dist/' folder.
pause
