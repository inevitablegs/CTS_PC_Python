@echo off
echo =============================================
echo   Circle to Search - Portable Python Setup
echo =============================================
echo.

:: Create portable directory
if not exist "portable_python" mkdir portable_python

:: Check if portable Python already exists
if exist "portable_python\python.exe" (
    echo ✅ Portable Python already installed!
    goto :install_deps
)

echo 📥 Downloading Portable Python...
echo This may take a few minutes...

:: Download portable Python (you can update this URL for latest version)
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip' -OutFile 'python_portable.zip'}"

if not exist "python_portable.zip" (
    echo ❌ Download failed! Please check internet connection.
    echo Alternative: Download Python manually from python.org
    pause
    exit /b 1
)

echo 📦 Extracting Python...
powershell -Command "Expand-Archive -Path 'python_portable.zip' -DestinationPath 'portable_python' -Force"

:: Cleanup
del python_portable.zip

echo ✅ Portable Python installed!

:install_deps
echo 📋 Installing dependencies...

:: Install pip for portable Python
portable_python\python.exe -m ensurepip --default-pip

:: Install requirements
portable_python\python.exe -m pip install --upgrade pip
portable_python\python.exe -m pip install PySide6 easyocr Pillow mss pynput pyperclip pywin32

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

:: Create portable run script
echo @echo off > run_portable.bat
echo echo ✅ Starting Circle to Search (Portable)... >> run_portable.bat
echo echo 🎯 Press Ctrl+Shift+Space or Ctrl+Alt+S to capture! >> run_portable.bat
echo echo. >> run_portable.bat
echo portable_python\python.exe main_direct.py >> run_portable.bat
echo pause >> run_portable.bat

echo.
echo ✅ Portable setup completed!
echo.
echo 🚀 To run: Double-click 'run_portable.bat'
echo 📦 This folder is now completely portable!
echo 💾 Size: ~200MB (includes Python + dependencies)
echo.
echo 🎯 Hotkeys: Ctrl+Shift+Space or Ctrl+Alt+S
echo.
pause