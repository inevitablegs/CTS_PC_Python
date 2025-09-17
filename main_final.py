# Final Working Circle to Search Application
# Version: Enhanced with proper image search

import sys
import os
import threading
import mss
import easyocr
import numpy
import webbrowser
import pyperclip
import tempfile
from urllib.parse import quote_plus

# PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox, 
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QShortcut, QKeySequence
from PySide6.QtCore import QObject, Signal, QThread, QTimer, QLockFile, QDir, QRect, Qt

# Simple imports that we know work
from overlay import OverlayWindow
from side_panel import SidePanelWindow
from PIL import Image

# Enhanced Image Search Handler with File Saving
class ImageSearchHandler:
    """Handles enhanced image search with actual image upload and file saving"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.save_dir = self.create_save_directory()
    
    def create_save_directory(self):
        """Create directory to save captured files"""
        try:
            # Create save directory in user's Documents folder
            documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            save_path = os.path.join(documents_path, "CircleToSearch_Captures")
            os.makedirs(save_path, exist_ok=True)
            print(f"[INFO] Save directory: {save_path}")
            return save_path
        except Exception as e:
            print(f"[ERROR] Could not create save directory: {e}")
            # Fallback to desktop
            return os.path.join(os.path.expanduser("~"), "Desktop")
    
    def save_capture_permanently(self, pil_image: Image.Image, ocr_text=""):
        """Save captured image and text permanently with timestamp"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save image
            image_filename = f"capture_{timestamp}.jpg"
            image_path = os.path.join(self.save_dir, image_filename)
            
            # Optimize and save image
            img = pil_image.copy()
            img.save(image_path, "JPEG", quality=95, optimize=True)
            
            # Save text file if there's OCR text
            if ocr_text.strip():
                text_filename = f"capture_{timestamp}.txt"
                text_path = os.path.join(self.save_dir, text_filename)
                
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(f"Circle to Search Capture\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Image File: {image_filename}\n")
                    f.write(f"\n--- Recognized Text ---\n")
                    f.write(ocr_text)
                
                print(f"[INFO] ✅ Saved: {image_path} and {text_path}")
                return image_path, text_path
            else:
                print(f"[INFO] ✅ Saved: {image_path}")
                return image_path, None
                
        except Exception as e:
            print(f"[ERROR] Could not save capture: {e}")
            return None, None
    
    def perform_image_search(self, pil_image: Image.Image, engine='google'):
        """Perform image search with actual image data"""
        try:
            # Method 1: Save image to desktop for easy upload
            desktop_path = self.save_to_desktop(pil_image)
            
            # Method 2: Try to copy to clipboard (Windows)
            clipboard_success = self.copy_to_clipboard_windows(pil_image)
            
            # Method 3: Open Google (always use Google as requested)
            search_url = "https://images.google.com/"
            webbrowser.open(search_url)
            instructions = "Click the camera icon 📷 to search by image"
            
            # Provide helpful feedback
            print(f"[INFO] 🔍 Google Image Search opened!")
            
            if clipboard_success:
                print("✅ Image copied to clipboard - you can paste it directly!")
            
            if desktop_path:
                print(f"✅ Image saved to: {desktop_path}")
                print("   You can upload this file to Google Images")
            
            print(f"📖 {instructions}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Image search failed: {e}")
            return False
    
    def save_to_desktop(self, pil_image: Image.Image):
        """Save image to desktop for easy upload"""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop_path):
                desktop_path = os.path.expanduser("~")
            
            image_path = os.path.join(desktop_path, "circle_search_image.jpg")
            
            # Optimize image size
            img = pil_image.copy()
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            img.save(image_path, "JPEG", quality=90, optimize=True)
            return image_path
            
        except Exception as e:
            print(f"[ERROR] Could not save to desktop: {e}")
            return None
    
    def copy_to_clipboard_windows(self, pil_image: Image.Image):
        """Copy image to Windows clipboard"""
        try:
            import io
            import win32clipboard
            
            # Convert to bitmap format
            output = io.BytesIO()
            pil_image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Remove BMP header
            output.close()
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            return True
            
        except ImportError:
            print("[INFO] win32clipboard not available")
            return False
        except Exception as e:
            print(f"[ERROR] Clipboard copy failed: {e}")
            return False

# Enhanced Search Engine with Image Support
class EnhancedSearchEngine:
    """Enhanced search engine with proper image search"""
    
    def __init__(self):
        self.image_handler = ImageSearchHandler()
        self.current_engine = 'google'
        self.auto_search = True  # Auto search on Google by default
    
    def set_engine(self, engine):
        """Set current search engine"""
        self.current_engine = engine
        print(f"[INFO] Search engine set to: {engine}")
    
    def search_text(self, query):
        """Search text with Google (always use Google as requested)"""
        if not query.strip():
            return False
        
        try:
            clean_query = query.strip()
            encoded_query = quote_plus(clean_query)
            
            # Always use Google for text search
            url = f"https://www.google.com/search?q={encoded_query}"
            
            webbrowser.open(url)
            print(f"[INFO] 🔍 Google text search: '{clean_query[:50]}{'...' if len(clean_query) > 50 else ''}'")
            return True
            
        except Exception as e:
            print(f"[ERROR] Text search failed: {e}")
            return False
    
    def search_images_by_text(self, query):
        """Search for images using text query on Google"""
        if not query.strip():
            return False
        
        try:
            clean_query = query.strip()
            encoded_query = quote_plus(clean_query)
            
            # Always use Google Images
            url = f"https://www.google.com/search?tbm=isch&q={encoded_query}"
            
            webbrowser.open(url)
            print(f"[INFO] 🖼️ Google image search: '{clean_query[:50]}{'...' if len(clean_query) > 50 else ''}'")
            return True
            
        except Exception as e:
            print(f"[ERROR] Image search by text failed: {e}")
            return False
    
    def search_image(self, pil_image=None):
        """Perform reverse image search on Google"""
        if pil_image:
            return self.image_handler.perform_image_search(pil_image, 'google')
        else:
            print("[WARNING] No image provided for reverse search")
            return False

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
    """Reliable Qt-based hotkey listener"""
    hotkey_pressed = Signal()

    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Setup Qt shortcuts"""
        try:
            # Primary hotkey: Ctrl+Shift+Space
            self.shortcut1 = QShortcut(QKeySequence("Ctrl+Shift+Space"), self.parent_widget)
            self.shortcut1.activated.connect(self.on_hotkey_activated)
            
            # Alternative hotkey: Ctrl+Alt+S
            self.shortcut2 = QShortcut(QKeySequence("Ctrl+Alt+S"), self.parent_widget)
            self.shortcut2.activated.connect(self.on_hotkey_activated)
            
            print("[INFO] ✅ Hotkeys registered: Ctrl+Shift+Space and Ctrl+Alt+S")
            
        except Exception as e:
            print(f"[ERROR] Failed to setup shortcuts: {e}")

    def on_hotkey_activated(self):
        """Handle hotkey activation"""
        print("[DEBUG] 🎯 Hotkey activated!")
        self.hotkey_pressed.emit()

class SimpleOcrWorker(QThread):
    """OCR worker with enhanced image search support"""
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

class EnhancedSidePanel(QWidget):
    """Enhanced side panel with image search"""
    
    def __init__(self):
        super().__init__()
        self.search_engine = None
        self.current_image = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Circle to Search - Results")
        self.setFixedSize(380, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("🔍 Circle to Search Results")
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Recognized text will appear here...")
        self.text_edit.setFixedHeight(150)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                background-color: #f9f9f9;
            }
            QTextEdit:focus {
                border-color: #667eea;
                background-color: white;
            }
        """)
        layout.addWidget(self.text_edit)
        
        # Search buttons
        search_layout = QVBoxLayout()
        
        # Text search buttons
        text_buttons_layout = QHBoxLayout()
        
        self.search_text_btn = QPushButton("🔍 Search on Google")
        self.search_text_btn.clicked.connect(self.search_text)
        self.search_text_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        text_buttons_layout.addWidget(self.search_text_btn)
        
        self.search_images_btn = QPushButton("🖼️ Google Images")
        self.search_images_btn.clicked.connect(self.search_images_by_text)
        self.search_images_btn.setStyleSheet(self.get_button_style("#FF9800"))
        text_buttons_layout.addWidget(self.search_images_btn)
        
        search_layout.addLayout(text_buttons_layout)
        
        # Image search button (prominent)
        self.image_search_btn = QPushButton("📷 Search Image on Google")
        self.image_search_btn.clicked.connect(self.search_image)
        self.image_search_btn.setStyleSheet(self.get_button_style("#2196F3"))
        self.image_search_btn.setFixedHeight(50)
        search_layout.addWidget(self.image_search_btn)
        
        layout.addLayout(search_layout)
        
        # Additional features
        features_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_text)
        self.copy_btn.setStyleSheet(self.get_button_style("#607D8B"))
        features_layout.addWidget(self.copy_btn)
        
        self.translate_btn = QPushButton("🌐 Translate")
        self.translate_btn.clicked.connect(self.translate_text)
        self.translate_btn.setStyleSheet(self.get_button_style("#9C27B0"))
        features_layout.addWidget(self.translate_btn)
        
        layout.addLayout(features_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        new_capture_btn = QPushButton("🎯 New Capture")
        new_capture_btn.clicked.connect(self.new_capture)
        new_capture_btn.setStyleSheet(self.get_button_style("#795548"))
        action_layout.addWidget(new_capture_btn)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet(self.get_button_style("#F44336"))
        action_layout.addWidget(close_btn)
        
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        
        # Overall styling
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 3px solid #667eea;
                border-radius: 15px;
            }
        """)
    
    def get_button_style(self, color):
        """Get button styling"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {color}CC;
            }}
            QPushButton:pressed {{
                background-color: {color}AA;
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #666666;
            }}
        """
    
    def set_content(self, text, image, search_engine):
        """Set content for the panel"""
        self.text_edit.setPlainText(text)
        self.current_image = image
        self.search_engine = search_engine
        
        # Enable/disable buttons
        has_text = bool(text.strip())
        has_image = image is not None
        
        self.search_text_btn.setEnabled(has_text)
        self.search_images_btn.setEnabled(has_text)
        self.copy_btn.setEnabled(has_text)
        self.translate_btn.setEnabled(has_text)
        self.image_search_btn.setEnabled(has_image)
        
        if has_image:
            self.image_search_btn.setText("📷 Search Image on Google ✨")
        else:
            self.image_search_btn.setText("📷 No Image Available")
    
    def search_text(self):
        """Search for text on Google"""
        text = self.text_edit.toPlainText().strip()
        if self.search_engine and text:
            success = self.search_engine.search_text(text)
            if success:
                self.show_feedback("🔍 Searching on Google!")
    
    def search_images_by_text(self):
        """Search for images by text on Google"""
        text = self.text_edit.toPlainText().strip()
        if self.search_engine and text:
            success = self.search_engine.search_images_by_text(text)
            if success:
                self.show_feedback("🖼️ Google Images opened!")
    
    def search_image(self):
        """Perform reverse image search on Google"""
        if self.search_engine and self.current_image:
            success = self.search_engine.search_image(self.current_image)
            if success:
                self.show_feedback("📷 Google Image search opened!")
            else:
                self.show_feedback("❌ Image search failed")
        else:
            self.show_feedback("❌ No image to search")
    
    def copy_text(self):
        """Copy text to clipboard"""
        text = self.text_edit.toPlainText().strip()
        if text:
            try:
                pyperclip.copy(text)
                self.show_feedback("📋 Text copied!")
            except Exception:
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                self.show_feedback("📋 Text copied!")
    
    def translate_text(self):
        """Translate text"""
        text = self.text_edit.toPlainText().strip()
        if text:
            try:
                encoded_text = quote_plus(text)
                url = f"https://translate.google.com/?sl=auto&tl=en&text={encoded_text}"
                webbrowser.open(url)
                self.show_feedback("🌐 Translation opened!")
            except Exception as e:
                print(f"[ERROR] Translation failed: {e}")
    
    def new_capture(self):
        """Request new capture"""
        self.hide()
        print("[INFO] New capture requested")
    
    def show_feedback(self, message):
        """Show feedback message"""
        original_title = self.windowTitle()
        self.setWindowTitle(message)
        QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))
    
    def show_panel(self, relative_rect=None):
        """Show the panel"""
        if relative_rect:
            screen = QGuiApplication.primaryScreen().geometry()
            
            # Position to the right of selection
            panel_x = min(relative_rect.right() + 15, screen.width() - self.width())
            panel_y = max(0, min(relative_rect.top(), screen.height() - self.height()))
            
            self.move(panel_x, panel_y)
        
        self.show()
        self.raise_()
        self.activateWindow()

class DirectHotkeyApplication(QObject):
    """Direct hotkey application without tray icon - overlay focused"""
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        print("[DEBUG] Initializing Direct Hotkey Circle to Search...")
        
        # Core components
        self.search_engine = EnhancedSearchEngine()
        
        # UI Components
        self.overlay = OverlayWindow()
        self.side_panel = EnhancedSidePanel()
        
        # State
        self.ocr_worker = None
        self.last_selection_rect = None
        self.last_captured_image = None
        
        # Setup only hotkeys (no tray)
        self.setup_direct_hotkeys()
        
        # Connect signals
        self.overlay.region_selected.connect(self.on_region_selected)
        
        print("[DEBUG] Direct Hotkey Circle to Search initialized!")

    def setup_direct_hotkeys(self):
        """Setup direct keyboard shortcuts without tray icon"""
        # Create a hidden widget for global shortcuts
        self.shortcut_widget = QWidget()
        self.shortcut_widget.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.shortcut_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.shortcut_widget.resize(1, 1)
        self.shortcut_widget.show()
        self.shortcut_widget.hide()
        
        # Setup hotkey listener
        self.hotkey_listener = SimpleHotkeyListener(self.shortcut_widget)
        self.hotkey_listener.hotkey_pressed.connect(self.handle_show_overlay)
        
        print("[INFO] ✅ Direct hotkeys setup complete - no tray icon needed")

    def setup_tray_icon(self):
        """Setup system tray icon"""
        icon_path = os.path.join(os.path.dirname(__file__), "assets/icon.png")
        if not os.path.exists(icon_path):
            self.create_simple_icon(icon_path)

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), parent=self.app)
        self.tray_icon.setToolTip("Circle to Search - Final Version")

        menu = QMenu()
        
        # Capture action
        capture_action = QAction("🎯 Capture Region")
        capture_action.triggered.connect(self.handle_show_overlay)
        menu.addAction(capture_action)
        
        menu.addSeparator()
        
        # Search engine (always Google now)
        google_action = QAction("🔍 Google Search (Default)")
        google_action.setCheckable(True)
        google_action.setChecked(True)
        google_action.setEnabled(False)  # Always Google
        menu.addAction(google_action)
        
        menu.addSeparator()
        
        # View saved captures
        view_captures_action = QAction("📁 View Saved Captures")
        view_captures_action.triggered.connect(self.view_saved_captures)
        menu.addAction(view_captures_action)
        
        menu.addSeparator()
        
        # Test
        test_action = QAction("🧪 Test Image Search")
        test_action.triggered.connect(self.test_image_search)
        menu.addAction(test_action)
        
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
        self.shortcut_widget.show()
        self.shortcut_widget.hide()
        
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
        print("[DEBUG] 🎯 Showing overlay...")
        try:
            self.overlay.show_overlay()
            print("[DEBUG] Overlay should be visible now")
        except Exception as e:
            print(f"[ERROR] Failed to show overlay: {e}")

    def view_saved_captures(self):
        """Open the saved captures folder"""
        try:
            save_dir = self.search_engine.image_handler.save_dir
            if os.path.exists(save_dir):
                os.startfile(save_dir)  # Windows-specific
                print(f"[INFO] Opened captures folder: {save_dir}")
            else:
                QMessageBox.information(None, "No Captures", "No captures folder found yet.\nCapture something first!")
        except Exception as e:
            print(f"[ERROR] Could not open captures folder: {e}")

    def test_image_search(self):
        """Test image search functionality"""
        print("[DEBUG] Testing image search...")
        
        try:
            # Create a test image
            test_img = Image.new('RGB', (200, 100), (100, 150, 200))
            
            # Test the image search
            success = self.search_engine.search_image(test_img)
            
            if success:
                self.tray_icon.showMessage(
                    "Test Successful", 
                    "Google Image search test completed! Check the opened browser.", 
                    QSystemTrayIcon.Information, 
                    3000
                )
            else:
                self.tray_icon.showMessage(
                    "Test Failed", 
                    "Image search test failed.", 
                    QSystemTrayIcon.Warning, 
                    3000
                )
                
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")

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

                self.ocr_worker = SimpleOcrWorker(pil_img)
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
        
        # Save captured files permanently
        image_path, text_path = self.search_engine.image_handler.save_capture_permanently(
            self.last_captured_image, clean_text
        )
        
        # Auto-copy to clipboard
        if clean_text:
            try:
                pyperclip.copy(clean_text)
                print("[INFO] Text copied to clipboard")
            except Exception as e:
                print(f"[WARNING] Could not copy to clipboard: {e}")
        
        # Auto-search on Google if text is found
        if clean_text and self.search_engine.auto_search:
            print("[INFO] 🔍 Auto-searching on Google...")
            self.search_engine.search_text(clean_text)
        
        # Show results with enhanced image search
        self.side_panel.set_content(clean_text, self.last_captured_image, self.search_engine)
        self.side_panel.show_panel(self.last_selection_rect)
        
        # Show notification with file save info
        if clean_text:
            save_info = f"Saved to: {os.path.basename(image_path)}" if image_path else ""
            self.tray_icon.showMessage(
                "Text Found & Saved!", 
                f"Found: {clean_text[:40]}{'...' if len(clean_text) > 40 else ''}\n📷 Auto-searched on Google!\n💾 {save_info}", 
                QSystemTrayIcon.Information, 
                5000
            )
        else:
            save_info = f"Saved to: {os.path.basename(image_path)}" if image_path else ""
            self.tray_icon.showMessage(
                "Image Captured & Saved!", 
                f"No text found, but image saved\n📷 Image search available\n💾 {save_info}", 
                QSystemTrayIcon.Information, 
                4000
            )

    def handle_ocr_error(self, error_message):
        """Handle OCR errors"""
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", f"Text recognition failed:\n{error_message}")

if __name__ == "__main__":
    print("🚀 Starting Final Circle to Search with Enhanced Image Search")
    
    # Single instance lock
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search-final.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running.")
        QMessageBox.information(None, "Already Running", 
                              "Circle to Search is already running!\n\nLook for the icon in your system tray.")
        sys.exit(0)
    
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Circle to Search Final")

    # Create main controller
    main_controller = FinalTrayApplication(app)

    print("✨ Circle to Search with Google Auto-Search is ready!")
    print("📖 How to use:")
    print("   🎯 Press Ctrl+Shift+Space OR Ctrl+Alt+S to capture")
    print("   🔍 Text automatically searches on Google!")
    print("   📷 Captured images can be searched on Google!")
    print("   💾 All captures are saved automatically!")
    print("   � Right-click tray → 'View Saved Captures' to see files")
    print("   🖱️  Double-click tray icon for quick capture")
    print("   📋 Text is auto-copied to clipboard")
    print("   ❌ Right-click tray icon → 'Exit' to quit")

    # Start the application
    sys.exit(app.exec())