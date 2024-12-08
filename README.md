# Time Tracker Application

This is a standalone cross-platform application for time tracking. You can either download the pre-built executable for your operating system or modify the code and build it yourself.

## **Download the Executable**

The latest release of the app is available here:

[**Download the Executable**](https://github.com/sheydHD/Time-tracker/releases/tag/v1.0)

### **For Windows Users**
1. Download the `time_tracker.exe` file from the latest release.
2. Double-click the file to launch the app.  
   No installation or Python required!

### **For Linux Users**
1. Download the `time_tracker` file from the latest release.
2. Make the file executable:

   ```bash
   chmod +x time_tracker
   ```

3. Run the application:

   ```bash
   ./time_tracker
   ```

---

## **Modifying and Building the Code**

If you want to modify the code and build the executable yourself, follow these steps:

### **On Windows**

1. Install **Python** and **PyInstaller** if not already installed:

   ```cmd
   pip install pyinstaller
   ```

2. Modify the code as needed.
3. Run the `build_exe.bat` script to generate the executable:

   ```cmd
   build_exe.bat
   ```

4. The executable will be generated in the `dist/` folder.

---

### **On Linux**

1. Install **Python** and **PyInstaller** if not already installed:

   ```bash
   pip install pyinstaller
   ```

2. Modify the code as needed.
3. Make the `run_app.sh` script executable:

   ```bash
   chmod +x run_app.sh
   ```

4. Run the script to build and run the app:

   ```bash
   ./run_app.sh
   ```

5. The executable will be generated in the `dist/` folder.

---

## **Scripts**

- `build_exe.bat`: A script for Windows to build the executable.
- `run_app.sh`: A script for Linux to build and run the app.

