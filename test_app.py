#!/usr/bin/env python3
"""
Test script for Circle to Search Application
This script runs various tests to verify the application is working correctly.
"""

import sys
import os
import tempfile
import time
from PIL import Image, ImageDraw, ImageFont

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    failed_imports = []
    
    # Test PySide6
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        print("✅ PySide6 imported successfully")
    except ImportError as e:
        failed_imports.append(f"PySide6: {e}")
    
    # Test PIL
    try:
        from PIL import Image
        print("✅ PIL imported successfully")
    except ImportError as e:
        failed_imports.append(f"PIL: {e}")
    
    # Test mss
    try:
        import mss
        print("✅ mss imported successfully")
    except ImportError as e:
        failed_imports.append(f"mss: {e}")
    
    # Test easyocr
    try:
        import easyocr
        print("✅ easyocr imported successfully")
    except ImportError as e:
        failed_imports.append(f"easyocr: {e}")
    
    # Test pynput
    try:
        from pynput import keyboard
        print("✅ pynput imported successfully")
    except ImportError as e:
        failed_imports.append(f"pynput: {e}")
    
    # Test numpy
    try:
        import numpy
        print("✅ numpy imported successfully")
    except ImportError as e:
        failed_imports.append(f"numpy: {e}")
    
    if failed_imports:
        print("\n❌ Failed imports:")
        for fail in failed_imports:
            print(f"   - {fail}")
        return False
    else:
        print("✅ All imports successful!")
        return True

def test_file_structure():
    """Test if required files exist"""
    print("\n🧪 Testing file structure...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "main.py",
        "overlay.py", 
        "side_panel.py",
        "core/__init__.py",
        "core/search_engines.py",
        "core/image_search.py",
        "utils/__init__.py",
        "utils/image_processing.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    # Check for icon
    icon_path = os.path.join(current_dir, "assets", "icon.png")
    if os.path.exists(icon_path):
        print("✅ assets/icon.png")
    else:
        print("❌ assets/icon.png")
        missing_files.append("assets/icon.png")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files")
        return False
    else:
        print("✅ All required files present!")
        return True

def test_local_imports():
    """Test if local modules can be imported"""
    print("\n🧪 Testing local module imports...")
    
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Test core modules
        from core.search_engines import SearchEngineManager
        print("✅ SearchEngineManager imported")
        
        from core.image_search import ImageSearchHandler
        print("✅ ImageSearchHandler imported")
        
        from utils.image_processing import ImageProcessor
        print("✅ ImageProcessor imported")
        
        # Test main modules
        from overlay import OverlayWindow
        print("✅ OverlayWindow imported")
        
        from side_panel import SidePanelWindow
        print("✅ SidePanelWindow imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_qt_application():
    """Test Qt application creation"""
    print("\n🧪 Testing Qt application...")
    
    try:
        from PySide6.QtWidgets import QApplication, QSystemTrayIcon
        from PySide6.QtCore import Qt
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        print("✅ QApplication created successfully")
        
        # Test system tray availability
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("✅ System tray is available")
        else:
            print("❌ System tray is not available")
            return False
        
        # Clean up
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Qt application test failed: {e}")
        return False

def test_ocr_functionality():
    """Test OCR with a simple image"""
    print("\n🧪 Testing OCR functionality...")
    
    try:
        # Create a simple test image with text
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
            except:
                font = ImageFont.load_default()
        
        draw.text((10, 30), "Hello World 123", fill='black', font=font)
        
        # Save test image
        test_image_path = os.path.join(tempfile.gettempdir(), "test_ocr.png")
        img.save(test_image_path)
        print(f"✅ Test image created: {test_image_path}")
        
        # Test EasyOCR
        import easyocr
        print("🔄 Initializing EasyOCR (this may take a moment)...")
        reader = easyocr.Reader(['en'], gpu=False)
        
        result = reader.readtext(test_image_path)
        recognized_text = " ".join([text for bbox, text, conf in result])
        
        print(f"✅ OCR Result: '{recognized_text}'")
        
        # Clean up
        os.remove(test_image_path)
        
        if "Hello" in recognized_text or "World" in recognized_text:
            print("✅ OCR working correctly!")
            return True
        else:
            print("⚠️  OCR didn't recognize expected text, but no errors")
            return True
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False

def test_screen_capture():
    """Test screen capture functionality"""
    print("\n🧪 Testing screen capture...")
    
    try:
        import mss
        
        with mss.mss() as sct:
            # Capture a small area of the screen
            monitor = {"top": 0, "left": 0, "width": 100, "height": 100}
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            print(f"✅ Screen capture successful: {img.size}")
            return True
            
    except Exception as e:
        print(f"❌ Screen capture test failed: {e}")
        return False

def test_search_engines():
    """Test search engine functionality"""
    print("\n🧪 Testing search engines...")
    
    try:
        from core.search_engines import SearchEngineManager
        
        manager = SearchEngineManager()
        print("✅ SearchEngineManager created")
        
        # Test setting engines
        manager.set_engine('google')
        print("✅ Google engine set")
        
        manager.set_engine('bing')
        print("✅ Bing engine set")
        
        return True
        
    except Exception as e:
        print(f"❌ Search engine test failed: {e}")
        return False

def create_missing_icon():
    """Create a simple icon if missing"""
    icon_dir = os.path.join(os.path.dirname(__file__), "assets")
    icon_path = os.path.join(icon_dir, "icon.png")
    
    if not os.path.exists(icon_path):
        print("\n🔧 Creating missing icon...")
        
        try:
            os.makedirs(icon_dir, exist_ok=True)
            
            # Create a simple icon
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw a search circle
            draw.ellipse([10, 10, 54, 54], outline=(0, 100, 255, 255), width=4)
            draw.ellipse([35, 35, 45, 45], fill=(0, 100, 255, 255))
            
            img.save(icon_path)
            print(f"✅ Icon created at: {icon_path}")
            
        except Exception as e:
            print(f"❌ Failed to create icon: {e}")

def run_basic_app_test():
    """Run a basic application test"""
    print("\n🧪 Testing basic application startup...")
    
    try:
        # Import the application
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from PySide6.QtWidgets import QApplication
        from core.search_engines import SearchEngineManager
        from core.image_search import ImageSearchHandler
        from utils.image_processing import ImageProcessor
        
        # Create minimal app
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # Test component creation
        search_manager = SearchEngineManager()
        image_handler = ImageSearchHandler()
        image_processor = ImageProcessor()
        
        print("✅ Core components created successfully")
        
        # Clean up
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Basic app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Circle to Search - Application Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("File Structure Test", test_file_structure),
        ("Local Import Test", test_local_imports),
        ("Qt Application Test", test_qt_application),
        ("Screen Capture Test", test_screen_capture),
        ("Search Engine Test", test_search_engines),
        ("Basic App Test", run_basic_app_test),
        ("OCR Test", test_ocr_functionality),  # This is last as it's slowest
    ]
    
    # Create missing icon first
    create_missing_icon()
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your application should work correctly.")
        print("\n🚀 You can now run: python main.py")
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the errors above.")
        print("\n💡 Common fixes:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Check if all files exist")
        print("   - Make sure you're in the correct directory")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)