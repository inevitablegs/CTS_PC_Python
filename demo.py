#!/usr/bin/env python3
"""
Quick demo and functionality test for Circle to Search
"""

import sys
import os
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont

def create_test_screen():
    """Create a test image with text to demonstrate OCR"""
    print("🎯 Creating test screen with text...")
    
    # Create a test image with various text elements
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        text_font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
            text_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
    
    # Add various text elements
    draw.text((50, 50), "Circle to Search Demo", fill='black', font=title_font)
    draw.text((50, 120), "Select this text to test OCR", fill='blue', font=text_font)
    draw.text((50, 160), "Email: test@example.com", fill='green', font=text_font)
    draw.text((50, 200), "Phone: (555) 123-4567", fill='red', font=text_font)
    draw.text((50, 240), "Address: 123 Main St, City", fill='purple', font=text_font)
    draw.text((50, 280), "Website: https://example.com", fill='orange', font=text_font)
    
    # Add some shapes for image search testing
    draw.rectangle([450, 150, 650, 250], outline='blue', width=3)
    draw.ellipse([450, 300, 650, 400], outline='red', width=3)
    draw.text((470, 200), "Test Shape", fill='blue', font=text_font)
    draw.text((470, 330), "Search Me!", fill='red', font=text_font)
    
    # Save the test image to desktop for easy access
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    test_image_path = os.path.join(desktop, "circle_to_search_demo.png")
    
    try:
        img.save(test_image_path)
        print(f"✅ Test image saved to: {test_image_path}")
        print("📸 Open this image to test the Circle to Search functionality!")
        return test_image_path
    except Exception as e:
        # Fallback to temp directory
        temp_path = os.path.join(tempfile.gettempdir(), "circle_to_search_demo.png")
        img.save(temp_path)
        print(f"✅ Test image saved to: {temp_path}")
        return temp_path

def check_app_status():
    """Check if the Circle to Search app is running"""
    print("\n🔍 Checking application status...")
    
    # Check for lock file
    from PySide6.QtCore import QDir
    import tempfile
    
    lock_file_path = os.path.join(QDir.tempPath(), "circle-to-search.lock")
    
    if os.path.exists(lock_file_path):
        print("✅ Circle to Search is currently running!")
        print("👀 Look for the icon in your system tray (bottom-right corner)")
        return True
    else:
        print("❌ Circle to Search is not running")
        print("🚀 Run: python main_simple.py to start the application")
        return False

def show_usage_instructions():
    """Show detailed usage instructions"""
    print("\n📖 How to Use Circle to Search:")
    print("=" * 50)
    print("1. 🎯 Start Capture:")
    print("   • Press Ctrl+Alt+S anywhere on your screen")
    print("   • OR right-click the tray icon → 'Capture Region'")
    print()
    print("2. 🖱️  Select Area:")
    print("   • Click and drag to select text or image region")
    print("   • The selection will be highlighted")
    print()
    print("3. 🔍 Search Options:")
    print("   • Text Search: OCR extracts text → search on Google/Bing")
    print("   • Image Search: Reverse image search using the captured image")
    print()
    print("4. ⚙️  Settings:")
    print("   • Right-click tray icon → 'Search Engine' to switch")
    print("   • Choose between Google and Bing")
    print()
    print("5. 🛑 Exit:")
    print("   • Right-click tray icon → 'Exit'")
    print("   • OR press Ctrl+C in the terminal")

def test_ocr_capability():
    """Test OCR on the demo image"""
    print("\n🧪 Testing OCR capability...")
    
    try:
        import easyocr
        
        # Create a simple test image
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), "Test OCR: Hello World 123", fill='black', font=font)
        
        # Save to temp file
        temp_path = os.path.join(tempfile.gettempdir(), "ocr_test.png")
        img.save(temp_path)
        
        print("🔄 Running OCR test...")
        reader = easyocr.Reader(['en'], gpu=False)
        result = reader.readtext(temp_path)
        
        recognized_text = " ".join([text for bbox, text, conf in result])
        print(f"✅ OCR Result: '{recognized_text}'")
        
        # Cleanup
        os.remove(temp_path)
        
        if "Hello" in recognized_text and "World" in recognized_text:
            print("🎉 OCR is working perfectly!")
        else:
            print("⚠️  OCR working but may need better image quality")
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")

def main():
    """Main demo function"""
    print("🚀 Circle to Search - Demo & Status Check")
    print("=" * 50)
    
    # Check if app is running
    app_running = check_app_status()
    
    # Create demo image
    demo_image = create_test_screen()
    
    # Test OCR
    test_ocr_capability()
    
    # Show instructions
    show_usage_instructions()
    
    print("\n" + "=" * 50)
    if app_running:
        print("🎉 Ready to test! Try the following:")
        print("1. 📸 Open the demo image on your screen")
        print("2. 🎯 Press Ctrl+Alt+S to start capture")
        print("3. 🖱️  Select any text in the demo image")
        print("4. 🔍 Choose 'Search Text' or 'Search Image'")
        print("5. 🌐 Watch the browser open with search results!")
    else:
        print("❌ Start the application first:")
        print("   python main_simple.py")
    
    print("\n💡 Pro Tips:")
    print("• The app works with ANY content on your screen")
    print("• Try selecting text from websites, PDFs, images")
    print("• Image search works great for finding similar images")
    print("• The app runs quietly in the background")

if __name__ == "__main__":
    main()