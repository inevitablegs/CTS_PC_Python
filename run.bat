@echo off
echo =============================================
echo      🎯 Circle to Search - Starting...
echo =============================================
echo.

:: Check if virtual environment exists
if not exist .venv\ (
    echo ❌ Virtual environment not found!
    echo Please run 'install.bat' first to set up the application.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Check if main file exists
if not exist main_direct.py (
    echo ❌ main_direct.py not found!
    echo Make sure you're in the correct directory.
    echo.
    pause
    exit /b 1
)

echo ✅ Starting Circle to Search...
echo 🎯 Press Ctrl+Shift+Space or Ctrl+Alt+S to capture anywhere!
echo 💡 Press Ctrl+C in this window to quit
echo.

:: Run the application
python main_direct.py

:: If we get here, the app has closed
echo.
echo Circle to Search has stopped.
pause