@echo off
echo =============================================
echo   Circle to Search - Portable Installer
echo =============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found!
echo.

:: Create virtual environment
echo 📦 Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

:: Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo 📋 Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo Installing packages individually...
    pip install PySide6
    pip install easyocr
    pip install Pillow
    pip install mss
    pip install pynput
    pip install pyperclip
    pip install pywin32
)

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ✅ Installation completed successfully!
echo.
echo 🚀 To run Circle to Search:
echo    - Double-click 'run.bat'
echo    - Or run 'python main_direct.py'
echo.
echo 🎯 Hotkeys: Ctrl+Shift+Space or Ctrl+Alt+S
echo.
pause