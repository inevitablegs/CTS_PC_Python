import sys
import os
import threading
import mss
import easyocr
import numpy
import webbrowser
import pyperclip
import tempfile
import time
from urllib.parse import quote_plus

# PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QMessageBox, 
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtCore import QObject, Signal, QThread, QTimer, QLockFile, QDir, QRect, Qt

# Global hotkey import
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("[WARNING] pynput not available, using fallback method")

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

# Enhanced Search Engine with Google Focus
class EnhancedSearchEngine:
    """Enhanced search engine with Google focus and proper image search"""
    
    def __init__(self):
        self.image_handler = ImageSearchHandler()
        self.auto_search = True  # Auto search on Google by default
    
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

class GlobalHotkeyListener(QObject):
    """Global hotkey listener using pynput for system-wide shortcuts"""
    hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.active = False
        self.listener = None

    def start_listening(self):
        """Start global hotkey listening"""
        if not PYNPUT_AVAILABLE:
            print("[ERROR] pynput not available for global hotkeys")
            return False
            
        if self.active:
            return True
            
        try:
            self.active = True
            # Start listener in a separate thread
            listener_thread = threading.Thread(target=self._run_listener, daemon=True)
            listener_thread.start()
            print("[INFO] ✅ Global hotkeys started: Ctrl+Shift+Space and Ctrl+Alt+S")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start global hotkeys: {e}")
            return False

    def _run_listener(self):
        """Run the global hotkey listener"""
        try:
            with keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+<space>': self._on_hotkey,
                '<ctrl>+<alt>+s': self._on_hotkey
            }) as self.listener:
                while self.active:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Hotkey listener error: {e}")

    def _on_hotkey(self):
        """Handle hotkey activation"""
        if self.active:
            print("[DEBUG] 🎯 Global hotkey activated!")
            self.hotkey_pressed.emit()

    def stop_listening(self):
        """Stop hotkey listening"""
        self.active = False
        if self.listener:
            try:
                self.listener.stop()
            except:
                pass

class FallbackHotkeyListener(QObject):
    """Fallback hotkey listener for when pynput is not available"""
    hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_fallback)
        
    def start_listening(self):
        """Start fallback method"""
        print("[INFO] ⚠️ Using fallback hotkey method - limited functionality")
        print("[INFO] Press F12 to activate capture instead")
        # Create a visible widget for F12 key
        self.widget = QWidget()
        self.widget.setWindowTitle("Circle to Search - Press F12 to Capture")
        self.widget.setFixedSize(400, 100)
        self.widget.show()
        
        # Add F12 shortcut to the widget
        from PySide6.QtGui import QShortcut, QKeySequence
        self.f12_shortcut = QShortcut(QKeySequence("F12"), self.widget)
        self.f12_shortcut.activated.connect(self._on_hotkey)
        
        return True
    
    def _check_fallback(self):
        """Check for fallback activation"""
        pass
    
    def _on_hotkey(self):
        """Handle fallback hotkey"""
        print("[DEBUG] 🎯 F12 hotkey activated!")
        self.hotkey_pressed.emit()
    
    def stop_listening(self):
        """Stop fallback listening"""
        if hasattr(self, 'widget'):
            self.widget.close()

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
    """Enhanced side panel with Google-focused search"""
    
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
        
        self.close_btn = QPushButton("❌ Close")
        self.close_btn.clicked.connect(self.hide)
        self.close_btn.setStyleSheet(self.get_button_style("#F44336"))
        action_layout.addWidget(self.close_btn)
        
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
        # Try global hotkey first
        if PYNPUT_AVAILABLE:
            self.hotkey_listener = GlobalHotkeyListener()
            success = self.hotkey_listener.start_listening()
        else:
            success = False
            
        # Fallback if global hotkeys fail
        if not success:
            print("[WARNING] Global hotkeys failed, using fallback method")
            self.hotkey_listener = FallbackHotkeyListener()
            self.hotkey_listener.start_listening()
        
        # Connect signals
        self.hotkey_listener.hotkey_pressed.connect(self.handle_show_overlay)
        
        print("[INFO] ✅ Hotkey setup complete")

    def handle_show_overlay(self):
        """Show the capture overlay directly"""
        print("[DEBUG] 🎯 Showing overlay (direct hotkey)...")
        print("[INFO] *** HOTKEY WORKING! *** Overlay should appear now...")
        try:
            self.overlay.show_overlay()
            print("[DEBUG] Overlay activated via hotkey")
        except Exception as e:
            print(f"[ERROR] Failed to show overlay: {e}")
            # Show a simple message box as fallback
            QMessageBox.information(None, "Capture", "Hotkey activated! Click OK to capture screenshot manually.")

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
        
        # Auto-copy to clipboard (no saving)
        if clean_text:
            try:
                pyperclip.copy(clean_text)
                print("[INFO] Text copied to clipboard")
            except Exception as e:
                print(f"[WARNING] Could not copy to clipboard: {e}")
        
        # Direct browser search - no panel, no saving
        if clean_text:
            print("[INFO] 🔍 Opening Google search directly...")
            self.search_engine.search_text(clean_text)
            print(f"✅ Text Found: {clean_text[:40]}{'...' if len(clean_text) > 40 else ''}")
            print(f"🔍 Google search opened directly!")
        else:
            # If no text, open Google Images for reverse image search
            if self.last_captured_image:
                print("[INFO] 📷 No text found - opening Google Images for image search...")
                self.search_engine.search_image(self.last_captured_image)
                print(f"📷 Image Captured!")
                print("📷 Google Images opened for reverse search!")

    def handle_ocr_error(self, error_message):
        """Handle OCR errors"""
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", f"Text recognition failed:\n{error_message}")

if __name__ == "__main__":
    print("🚀 Starting Direct Hotkey Circle to Search (No Tray Icon)")
    
    # Single instance lock
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search-direct.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running.")
        sys.exit(0)
    
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Circle to Search Direct")

    # Create main controller (no tray icon)
    main_controller = DirectHotkeyApplication(app)

    print("✨ Direct Hotkey Circle to Search is ready!")
    print("📖 How to use:")
    print("   🎯 Press Ctrl+Shift+Space OR Ctrl+Alt+S to capture")
    print("   🔍 Text automatically searches on Google!")
    print("   📷 Images automatically open Google Images!")
    print("   📋 Text is auto-copied to clipboard")
    print("   ❌ Press Ctrl+C in terminal to quit")

    # Start the application
    sys.exit(app.exec())