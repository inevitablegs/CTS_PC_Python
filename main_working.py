# main_working.py - A working version with simplified, reliable hotkey handling

import sys
import os
import threading
import mss
import easyocr
import numpy
import webbrowser
import pyperclip
from urllib.parse import quote_plus

# PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox, 
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtCore import QObject, Signal, QThread, QTimer, QLockFile, QDir, QRect, Qt

# Simple imports that we know work
from overlay import OverlayWindow
from side_panel import SidePanelWindow
from PIL import Image
from core.search_engines import SearchEngineManager
from utils.image_processing import ImageProcessor

# Global OCR Reader
EASYOCR_READER = None

def get_ocr_reader():
    """Creates or returns the singleton OCR reader instance."""
    global EASYOCR_READER
    if EASYOCR_READER is None:
        print("[INFO] Initializing EasyOCR Reader...")
        EASYOCR_READER = easyocr.Reader(['en'], gpu=False)
        print("[INFO] EasyOCR Reader initialized.")
    return EASYOCR_READER

class SimpleHotkeyListener(QObject):
    """Simplified hotkey listener using Qt shortcuts"""
    hotkey_pressed = Signal()

    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Setup Qt-based shortcuts"""
        try:
            from PySide6.QtGui import QShortcut, QKeySequence
            
            # Primary hotkey: Ctrl+Shift+Space
            self.shortcut1 = QShortcut(QKeySequence("Ctrl+Shift+Space"), self.parent_widget)
            self.shortcut1.activated.connect(self.on_hotkey_activated)
            
            # Alternative hotkey: Ctrl+Alt+S (for backup)
            self.shortcut2 = QShortcut(QKeySequence("Ctrl+Alt+S"), self.parent_widget)
            self.shortcut2.activated.connect(self.on_hotkey_activated)
            
            print("[INFO] Qt shortcuts registered: Ctrl+Shift+Space and Ctrl+Alt+S")
            
        except Exception as e:
            print(f"[ERROR] Failed to setup shortcuts: {e}")

    def on_hotkey_activated(self):
        """Handle hotkey activation"""
        print("[DEBUG] Hotkey activated!")
        self.hotkey_pressed.emit()

class SimpleOcrWorker(QThread):
    """Simplified OCR worker"""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, pil_image):
        super().__init__()
        self.pil_image = pil_image

    def run(self):
        """Run OCR processing"""
        try:
            reader = get_ocr_reader()
            image_np = numpy.array(self.pil_image)
            result = reader.readtext(image_np)
            
            recognized_texts = [text for bbox, text, conf in result if conf > 0.3]
            full_text = "\n".join(recognized_texts)
            
            self.finished.emit(full_text)
        except Exception as e:
            self.error.emit(f"OCR Error: {repr(e)}")

class WorkingTrayApplication(QObject):
    """Working tray application with simplified but reliable functionality"""
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        print("[DEBUG] Initializing Working Circle to Search...")
        
        # Core components
        self.search_manager = SearchEngineManager()
        self.image_processor = ImageProcessor()
        
        # UI Components
        self.overlay = OverlayWindow()
        self.side_panel = SidePanelWindow()
        
        # State
        self.ocr_worker = None
        self.last_selection_rect = None
        self.last_captured_image = None
        
        # Setup
        self.setup_tray_icon()
        self.setup_shortcuts()
        
        # Connect signals
        self.overlay.region_selected.connect(self.on_region_selected)
        
        print("[DEBUG] Working Circle to Search initialized!")

    def setup_tray_icon(self):
        """Setup system tray icon"""
        icon_path = os.path.join(os.path.dirname(__file__), "assets/icon.png")
        if not os.path.exists(icon_path):
            self.create_simple_icon(icon_path)

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), parent=self.app)
        self.tray_icon.setToolTip("Circle to Search - Working Version")

        menu = QMenu()
        
        # Capture action
        capture_action = QAction("🎯 Capture Region")
        capture_action.triggered.connect(self.handle_show_overlay)
        menu.addAction(capture_action)
        
        menu.addSeparator()
        
        # Test action
        test_action = QAction("🧪 Test Capture")
        test_action.triggered.connect(self.test_capture)
        menu.addAction(test_action)
        
        menu.addSeparator()
        
        # Search engine
        google_action = QAction("🔍 Use Google")
        google_action.triggered.connect(lambda: self.search_manager.set_engine('google'))
        menu.addAction(google_action)
        
        bing_action = QAction("🔍 Use Bing")
        bing_action.triggered.connect(lambda: self.search_manager.set_engine('bing'))
        menu.addAction(bing_action)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("❌ Exit")
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
        # Double-click to capture
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        print("[DEBUG] Tray icon created successfully")

    def create_simple_icon(self, icon_path):
        """Create a simple icon if none exists"""
        try:
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            from PIL import Image, ImageDraw
            
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], outline=(0, 120, 255, 255), width=4)
            draw.ellipse([38, 38, 48, 48], fill=(0, 120, 255, 255))
            img.save(icon_path)
            print(f"[INFO] Created icon at: {icon_path}")
        except Exception as e:
            print(f"[WARNING] Could not create icon: {e}")

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Create a hidden widget for shortcuts
        self.shortcut_widget = QWidget()
        self.shortcut_widget.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.shortcut_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.shortcut_widget.resize(1, 1)
        self.shortcut_widget.show()  # Must be shown for shortcuts to work
        self.shortcut_widget.hide()  # But hide it immediately
        
        # Setup hotkey listener
        self.hotkey_listener = SimpleHotkeyListener(self.shortcut_widget)
        self.hotkey_listener.hotkey_pressed.connect(self.handle_show_overlay)

    def on_tray_activated(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.DoubleClick:
            print("[DEBUG] Tray icon double-clicked")
            self.handle_show_overlay()

    def handle_show_overlay(self):
        """Show the capture overlay"""
        print("[DEBUG] Showing overlay...")
        try:
            self.overlay.show_overlay()
            print("[DEBUG] Overlay should be visible now")
        except Exception as e:
            print(f"[ERROR] Failed to show overlay: {e}")
            # Fallback: show message
            QMessageBox.information(None, "Capture", 
                "Click OK, then manually capture a screenshot and paste it here.")

    def test_capture(self):
        """Test capture functionality"""
        print("[DEBUG] Testing capture...")
        
        try:
            # Capture a small area of the screen
            test_rect = QRect(100, 100, 200, 100)
            self.simulate_capture(test_rect)
        except Exception as e:
            print(f"[ERROR] Test capture failed: {e}")
            QMessageBox.warning(None, "Test Failed", f"Test capture failed: {e}")

    def simulate_capture(self, rect):
        """Simulate a screen capture for testing"""
        try:
            capture_rect = {
                "top": rect.top(),
                "left": rect.left(),
                "width": rect.width(),
                "height": rect.height(),
            }
            
            with mss.mss() as sct:
                sct_img = sct.grab(capture_rect)
                pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                self.last_captured_image = pil_img.copy()
                self.last_selection_rect = rect
                
                print("✅ Test capture successful, starting OCR...")
                
                # Start OCR
                if self.ocr_worker and self.ocr_worker.isRunning():
                    self.ocr_worker.quit()
                    self.ocr_worker.wait()

                enhanced_img = self.image_processor.enhance_for_ocr(pil_img.copy())
                self.ocr_worker = SimpleOcrWorker(enhanced_img)
                self.ocr_worker.finished.connect(self.handle_ocr_result)
                self.ocr_worker.error.connect(self.handle_ocr_error)
                self.ocr_worker.start()
                
        except Exception as e:
            print(f"[ERROR] Simulate capture failed: {e}")

    def on_region_selected(self, rect: QRect):
        """Handle region selection"""
        print(f"[DEBUG] Region selected: {rect}")
        
        self.last_selection_rect = rect
        screen = QGuiApplication.primaryScreen()
        pixel_ratio = screen.devicePixelRatio()
        
        capture_rect = {
            "top": int(rect.top() * pixel_ratio),
            "left": int(rect.left() * pixel_ratio),
            "width": int(rect.width() * pixel_ratio),
            "height": int(rect.height() * pixel_ratio),
        }
        
        try:
            with mss.mss() as sct:
                sct_img = sct.grab(capture_rect)
                pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                self.last_captured_image = pil_img.copy()
                
                print("✅ Region captured, starting OCR...")
                
                if self.ocr_worker and self.ocr_worker.isRunning():
                    self.ocr_worker.quit()
                    self.ocr_worker.wait()

                enhanced_img = self.image_processor.enhance_for_ocr(pil_img.copy())
                self.ocr_worker = SimpleOcrWorker(enhanced_img)
                self.ocr_worker.finished.connect(self.handle_ocr_result)
                self.ocr_worker.error.connect(self.handle_ocr_error)
                self.ocr_worker.start()
                
        except Exception as e:
            print(f"[ERROR] Screen capture failed: {e}")
            QMessageBox.warning(None, "Capture Error", f"Failed to capture screen: {e}")

    def handle_ocr_result(self, ocr_text):
        """Handle OCR results"""
        clean_text = ocr_text.strip()
        print(f"✅ OCR Result: {clean_text}")
        
        # Auto-copy to clipboard
        if clean_text:
            try:
                pyperclip.copy(clean_text)
                print("[INFO] Text copied to clipboard")
            except Exception as e:
                print(f"[WARNING] Could not copy to clipboard: {e}")
        
        # Show results
        self.side_panel.set_content(clean_text, self.last_captured_image, self.search_manager)
        self.side_panel.show_panel(self.last_selection_rect)
        
        # Show notification
        if clean_text:
            self.tray_icon.showMessage(
                "Text Found!", 
                f"Found: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}", 
                QSystemTrayIcon.Information, 
                3000
            )
        else:
            self.tray_icon.showMessage(
                "No Text Found", 
                "Try selecting a clearer text region", 
                QSystemTrayIcon.Warning, 
                3000
            )

    def handle_ocr_error(self, error_message):
        """Handle OCR errors"""
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", f"Text recognition failed:\n{error_message}")

if __name__ == "__main__":
    print("🚀 Starting Working Circle to Search")
    
    # Single instance lock
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search-working.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running.")
        QMessageBox.information(None, "Already Running", 
                              "Circle to Search is already running!\n\nLook for the icon in your system tray.")
        sys.exit(0)
    
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Circle to Search Working")

    # Create main controller
    main_controller = WorkingTrayApplication(app)

    print("✨ Circle to Search is ready!")
    print("📖 How to use:")
    print("   🎯 Press Ctrl+Shift+Space OR Ctrl+Alt+S to capture")
    print("   🖱️  Double-click tray icon for quick capture")
    print("   🧪 Right-click tray icon → 'Test Capture' to test")
    print("   ❌ Right-click tray icon → 'Exit' to quit")

    # Start the application
    sys.exit(app.exec())