#!/bin/bash
# Navigate to the build_exe folder
cd "$(dirname "$0")"

# Initialize the database
echo "Initializing database..."
python3 init_db.py

# Run PyInstaller
echo "Building executable..."
pyinstaller time_tracker.spec

echo "Build completed. Check the 'dist/' folder."
