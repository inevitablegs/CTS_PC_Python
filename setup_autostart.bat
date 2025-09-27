@echo off
echo =============================================
echo   Circle to Search - Windows Service Setup
echo =============================================
echo.

:: Check for admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo This script requires administrator privileges.
    echo Please right-click and "Run as administrator"
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%main_direct.py"
set "VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"

:: Check if files exist
if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: main_direct.py not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

echo Creating startup shortcut...

:: Create VBS script for silent startup
echo Set WshShell = CreateObject("WScript.Shell") > "%SCRIPT_DIR%circle_search_silent.vbs"
echo WshShell.Run """%VENV_PYTHON%"" ""%PYTHON_SCRIPT%""", 0 >> "%SCRIPT_DIR%circle_search_silent.vbs"

:: Create startup shortcut
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\Circle to Search.lnk"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%SCRIPT_DIR%circle_search_silent.vbs'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = '%SCRIPT_DIR%assets\icon.png'; $Shortcut.Description = 'Circle to Search - Auto Start'; $Shortcut.Save()"

if exist "%SHORTCUT%" (
    echo ✅ Startup shortcut created successfully!
    echo Circle to Search will now start automatically when Windows boots.
    echo.
    echo 🎯 Hotkeys: Ctrl+Shift+Space or Ctrl+Alt+S
    echo.
    echo To remove auto-startup, delete:
    echo %SHORTCUT%
) else (
    echo ❌ Failed to create startup shortcut
)

echo.
pause