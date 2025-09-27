# Circle to Search - Portable Version

## 🚀 Quick Setup for Friends

### Option 1: Simple Setup (Recommended)
1. **Copy the entire folder** to any location
2. **Double-click `install.bat`** - this will:
   - Check if Python is installed
   - Create virtual environment
   - Install all dependencies
3. **Double-click `run.bat`** to start the app
4. **Use hotkeys**: `Ctrl+Shift+Space` or `Ctrl+Alt+S` anywhere!

### Option 2: Auto-Start with Windows
1. Follow Option 1 first
2. **Right-click `setup_autostart.bat`** → **Run as Administrator**
3. App will start automatically when Windows boots

### Option 3: Portable Python Bundle (No Python Installation Required)
1. Download portable Python from: https://www.python.org/downloads/
2. Extract to `portable_python/` folder
3. Run `install_portable.bat` instead of `install.bat`

## 📋 System Requirements
- **Windows 10/11** (64-bit recommended)
- **Python 3.8+** (auto-installed with portable version)
- **4GB RAM** minimum
- **Internet connection** (for Google searches)

## 🎯 How to Use
1. **Activate**: Press `Ctrl+Shift+Space` or `Ctrl+Alt+S` anywhere
2. **Select**: Drag to select text or images on screen
3. **Search**: Automatically opens Google with your selection
4. **Copy**: Text is automatically copied to clipboard

## 🔧 Troubleshooting

### "Python not found"
- Install Python from https://python.org
- **Important**: Check "Add Python to PATH" during installation

### "Permission denied" or "Access denied"
- Right-click batch files → **Run as Administrator**
- Disable antivirus temporarily during installation

### Hotkeys not working
- Close other screen capture apps (Snipping Tool, etc.)
- Restart the application
- Try alternative hotkey: `Ctrl+Alt+S`

### App won't start
- Run `install.bat` again
- Check if antivirus is blocking Python

## 📁 Folder Structure
```
CircleToSearch_Portable/
├── main_direct.py          # Main application
├── overlay.py              # Screen overlay
├── side_panel.py           # Results panel
├── requirements.txt        # Dependencies
├── install.bat             # Easy installer
├── run.bat                 # Run application
├── setup_autostart.bat     # Auto-start setup
├── install_portable.bat    # Portable Python installer
├── README.md               # This file
└── .venv/                  # Virtual environment (created after install)
```

## 🌐 Features
- ✅ **Global hotkeys** work from any application
- ✅ **OCR text recognition** with EasyOCR
- ✅ **Instant Google search** for text
- ✅ **Reverse image search** for images
- ✅ **Auto clipboard copy** for text
- ✅ **No file saving** - clean and fast
- ✅ **Portable** - works from any folder

## 🤝 Sharing with Friends
1. **Zip the entire folder**
2. **Send to friend**
3. **Friend runs `install.bat`**
4. **Ready to use!**

No complex setup needed! 🎉

---
**Created by**: Your friendly developer
**Hotkeys**: `Ctrl+Shift+Space` or `Ctrl+Alt+S`
**Version**: Portable 1.0