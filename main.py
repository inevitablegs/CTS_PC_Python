# Enhanced Circle to Search Application
# Version 2.0 - More Robust, Feature-Rich, and User-Friendly

import sys
import os
import threading
import asyncio
import io
import mss
import easyocr
import numpy
import json
import webbrowser
import pyperclip
import time
from datetime import datetime
from pynput import keyboard
from urllib.parse import quote_plus

# PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget, 
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QCheckBox, QSlider, QSpinBox, QTabWidget,
    QListWidget, QListWidgetItem, QProgressBar, QFrame
)
from PySide6.QtGui import (
    QIcon, QAction, QGuiApplication, QFont, QPixmap, QPainter,
    QColor, QPen, QCursor, QKeySequence, QShortcut
)
from PySide6.QtCore import (
    QObject, Signal, QThread, QTimer, QLockFile, QDir, QRect, Qt,
    QSettings, QStandardPaths, QSize
)

# Local Imports
from overlay_enhanced import EnhancedOverlayWindow
from side_panel_enhanced import EnhancedSidePanelWindow
from PIL import Image

# Enhanced imports
from core.search_engines import SearchEngineManager
from core.image_search import ImageSearchHandler
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

class EnhancedSearchEngine:
    """Enhanced search engine with better Google integration"""
    
    def __init__(self):
        self.base_urls = {
            'google_text': 'https://www.google.com/search',
            'google_images': 'https://www.google.com/search?tbm=isch',
            'google_lens': 'https://lens.google.com/',
            'bing_text': 'https://www.bing.com/search',
            'bing_images': 'https://www.bing.com/images/search'
        }
    
    def search_text(self, query, engine='google'):
        """Enhanced text search with better URL formatting"""
        if not query.strip():
            return False
            
        try:
            # Clean and encode the query
            clean_query = query.strip()
            encoded_query = quote_plus(clean_query)
            
            if engine == 'google':
                url = f"{self.base_urls['google_text']}?q={encoded_query}"
            else:  # bing
                url = f"{self.base_urls['bing_text']}?q={encoded_query}"
            
            webbrowser.open(url)
            print(f"[INFO] Opened {engine} search for: '{clean_query}'")
            return True
            
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return False
    
    def search_image(self, image_data=None, pil_image=None, engine='google'):
        """Enhanced image search with actual image upload"""
        try:
            if pil_image:
                # Use the enhanced image search handler
                from core.image_search import ImageSearchHandler
                handler = ImageSearchHandler()
                
                # Perform advanced search with the actual image
                search_url = handler.perform_advanced_search(pil_image, engine)
                
                if search_url:
                    print(f"[INFO] {engine.title()} image search opened with captured image!")
                    return True
                else:
                    # Fallback to regular URL opening
                    if engine == 'google':
                        webbrowser.open(self.base_urls['google_lens'])
                    else:
                        webbrowser.open('https://www.bing.com/visualsearch')
                    print(f"[INFO] Opened {engine} image search (fallback)")
                    return True
            else:
                # No image provided, just open the search page
                if engine == 'google':
                    webbrowser.open(self.base_urls['google_lens'])
                else:
                    webbrowser.open('https://www.bing.com/visualsearch')
                print(f"[INFO] Opened {engine} image search")
                return True
            
        except Exception as e:
            print(f"[ERROR] Image search failed: {e}")
            return False

class SettingsManager:
    """Manages application settings"""
    
    def __init__(self):
        self.settings = QSettings('CircleToSearch', 'Settings')
        self.load_defaults()
    
    def load_defaults(self):
        """Load default settings"""
        defaults = {
            'hotkey': 'ctrl+shift+space',
            'search_engine': 'google',
            'auto_copy': True,
            'show_notifications': True,
            'ocr_language': 'en',
            'capture_sound': True,
            'history_size': 50
        }
        
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
    
    def get(self, key, default=None):
        return self.settings.value(key, default)
    
    def set(self, key, value):
        self.settings.setValue(key, value)

class SearchHistory:
    """Manages search history"""
    
    def __init__(self, max_size=50):
        self.max_size = max_size
        self.history = []
        self.load_history()
    
    def add_search(self, text, timestamp=None):
        """Add a search to history"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Remove if already exists
        self.history = [h for h in self.history if h['text'] != text]
        
        # Add to beginning
        self.history.insert(0, {
            'text': text,
            'timestamp': timestamp
        })
        
        # Limit size
        if len(self.history) > self.max_size:
            self.history = self.history[:self.max_size]
        
        self.save_history()
    
    def get_history(self):
        return self.history
    
    def clear_history(self):
        self.history = []
        self.save_history()
    
    def load_history(self):
        """Load history from file"""
        try:
            history_file = os.path.join(QStandardPaths.writableLocation(
                QStandardPaths.AppDataLocation), 'search_history.json')
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"[WARNING] Could not load history: {e}")
            self.history = []
    
    def save_history(self):
        """Save history to file"""
        try:
            app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            os.makedirs(app_data_dir, exist_ok=True)
            
            history_file = os.path.join(app_data_dir, 'search_history.json')
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] Could not save history: {e}")

class NotificationManager:
    """Manages notifications and user feedback"""
    
    @staticmethod
    def show_notification(title, message, duration=3000):
        """Show system tray notification"""
        try:
            app = QApplication.instance()
            if app and hasattr(app, 'tray_icon'):
                app.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, duration)
        except Exception as e:
            print(f"[WARNING] Could not show notification: {e}")
    
    @staticmethod
    def show_capture_feedback():
        """Show visual feedback for capture"""
        NotificationManager.show_notification(
            "Circle to Search", 
            "Region captured! Processing...", 
            2000
        )

class EnhancedHotkeyListener(QObject):
    """Enhanced hotkey listener with configurable keys"""
    hotkey_pressed = Signal()

    def __init__(self, hotkey_combination='<ctrl>+<shift>+<space>'):
        super().__init__()
        self.hotkey_combination = hotkey_combination
        self.listener = None
        self.active = False

    def start_listening(self):
        if not self.active:
            self.active = True
            listener_thread = threading.Thread(target=self._run, daemon=True)
            listener_thread.start()
            print(f"[INFO] Hotkey listener started: {self.hotkey_combination}")

    def stop_listening(self):
        self.active = False
        if self.listener:
            self.listener.stop()

    def _run(self):
        try:
            with keyboard.GlobalHotKeys({self.hotkey_combination: self._on_activate}) as self.listener:
                while self.active:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Failed to start hotkey listener: {e}")

    def _on_activate(self):
        if self.active:
            print(f"[DEBUG] Hotkey activated: {self.hotkey_combination}")
            self.hotkey_pressed.emit()

    def update_hotkey(self, new_hotkey):
        """Update the hotkey combination"""
        was_active = self.active
        if was_active:
            self.stop_listening()
        
        self.hotkey_combination = new_hotkey
        
        if was_active:
            self.start_listening()

class EnhancedOcrWorker(QThread):
    """Enhanced OCR worker with multiple engines and languages"""
    finished = Signal(str, float)  # text, confidence
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, pil_image, language='en'):
        super().__init__()
        self.pil_image = pil_image
        self.language = language

    def run(self):
        """Enhanced OCR processing"""
        try:
            self.progress.emit(25)
            
            # Get OCR reader
            reader = get_ocr_reader()
            self.progress.emit(50)

            # Convert image to numpy array
            image_np = numpy.array(self.pil_image)
            self.progress.emit(75)

            # Perform OCR with confidence scores
            result = reader.readtext(image_np)
            
            # Extract text and calculate average confidence
            recognized_texts = []
            confidences = []
            
            for bbox, text, confidence in result:
                if confidence > 0.3:  # Filter low-confidence results
                    recognized_texts.append(text)
                    confidences.append(confidence)
            
            full_text = "\n".join(recognized_texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            self.progress.emit(100)
            self.finished.emit(full_text, avg_confidence)

        except Exception as e:
            self.error.emit(f"OCR Error: {repr(e)}")

class SettingsWindow(QWidget):
    """Enhanced settings window"""
    
    def __init__(self, settings_manager, hotkey_listener):
        super().__init__()
        self.settings_manager = settings_manager
        self.hotkey_listener = hotkey_listener
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Circle to Search - Settings")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        
        # Tabs
        tabs = QTabWidget()
        
        # General Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        # Hotkey setting
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Hotkey:"))
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems([
            "Ctrl+Shift+Space",
            "Ctrl+Alt+S", 
            "Ctrl+Shift+C",
            "Alt+Space"
        ])
        current_hotkey = self.settings_manager.get('hotkey', 'ctrl+shift+space')
        if 'shift' in current_hotkey and 'space' in current_hotkey:
            self.hotkey_combo.setCurrentText("Ctrl+Shift+Space")
        hotkey_layout.addWidget(self.hotkey_combo)
        general_layout.addLayout(hotkey_layout)
        
        # Search engine
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Search Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Google", "Bing"])
        self.engine_combo.setCurrentText(self.settings_manager.get('search_engine', 'google').title())
        engine_layout.addWidget(self.engine_combo)
        general_layout.addLayout(engine_layout)
        
        # Auto-copy checkbox
        self.auto_copy_check = QCheckBox("Auto-copy recognized text to clipboard")
        self.auto_copy_check.setChecked(self.settings_manager.get('auto_copy', True))
        general_layout.addWidget(self.auto_copy_check)
        
        # Notifications checkbox
        self.notifications_check = QCheckBox("Show notifications")
        self.notifications_check.setChecked(self.settings_manager.get('show_notifications', True))
        general_layout.addWidget(self.notifications_check)
        
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "General")
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        
        layout.addWidget(tabs)
        layout.addWidget(save_btn)
        self.setLayout(layout)
    
    def save_settings(self):
        """Save all settings"""
        # Update hotkey
        hotkey_text = self.hotkey_combo.currentText()
        hotkey_map = {
            "Ctrl+Shift+Space": "<ctrl>+<shift>+<space>",
            "Ctrl+Alt+S": "<ctrl>+<alt>+s",
            "Ctrl+Shift+C": "<ctrl>+<shift>+c",
            "Alt+Space": "<alt>+<space>"
        }
        
        new_hotkey = hotkey_map.get(hotkey_text, "<ctrl>+<shift>+<space>")
        self.settings_manager.set('hotkey', new_hotkey)
        self.hotkey_listener.update_hotkey(new_hotkey)
        
        # Save other settings
        self.settings_manager.set('search_engine', self.engine_combo.currentText().lower())
        self.settings_manager.set('auto_copy', self.auto_copy_check.isChecked())
        self.settings_manager.set('show_notifications', self.notifications_check.isChecked())
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.close()

class EnhancedTrayApplication(QObject):
    """Enhanced main application class"""
    
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        print("[DEBUG] Initializing Enhanced Circle to Search...")
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.search_history = SearchHistory()
        self.search_engine = EnhancedSearchEngine()
        self.image_search_handler = ImageSearchHandler()
        self.image_processor = ImageProcessor()
        
        # UI Components
        self.overlay = EnhancedOverlayWindow()
        self.side_panel = EnhancedSidePanelWindow()
        self.settings_window = None
        
        # State
        self.ocr_worker = None
        self.last_selection_rect = None
        self.last_captured_image = None
        self.last_ocr_text = ""
        
        # Connect signals
        self.overlay.region_selected.connect(self.on_region_selected)
        
        # Setup
        self.setup_tray_icon()
        self.setup_hotkey_listener()
        
        print("[DEBUG] Enhanced Circle to Search initialized!")
        print(f"[INFO] Hotkey: {self.settings_manager.get('hotkey')}")

    def setup_tray_icon(self):
        """Setup enhanced system tray icon"""
        icon_path = os.path.join(os.path.dirname(__file__), "assets/icon.png")
        if not os.path.exists(icon_path):
            # Create a simple icon if missing
            self.create_default_icon(icon_path)

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), parent=self.app)
        self.tray_icon.setToolTip("Circle to Search - Enhanced")
        
        # Store reference for notifications
        self.app.tray_icon = self.tray_icon

        menu = QMenu()
        
        # Quick capture
        capture_action = QAction("🎯 Quick Capture")
        capture_action.triggered.connect(self.handle_show_overlay)
        capture_action.setShortcut(QKeySequence("Ctrl+Shift+Space"))
        menu.addAction(capture_action)
        
        menu.addSeparator()
        
        # Search history
        history_action = QAction("📜 Search History")
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)
        
        menu.addSeparator()
        
        # Search engines submenu
        search_menu = QMenu("🔍 Search Engine")
        
        google_action = QAction("Google")
        google_action.setCheckable(True)
        google_action.setChecked(self.settings_manager.get('search_engine') == 'google')
        google_action.triggered.connect(lambda: self.set_search_engine('google'))
        search_menu.addAction(google_action)
        
        bing_action = QAction("Bing")
        bing_action.setCheckable(True)
        bing_action.setChecked(self.settings_manager.get('search_engine') == 'bing')
        bing_action.triggered.connect(lambda: self.set_search_engine('bing'))
        search_menu.addAction(bing_action)
        
        menu.addMenu(search_menu)
        
        # Settings
        settings_action = QAction("⚙️ Settings")
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # About
        about_action = QAction("ℹ️ About")
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # Exit
        exit_action = QAction("❌ Exit")
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
        # Double-click to capture
        self.tray_icon.activated.connect(self.on_tray_activated)

    def create_default_icon(self, icon_path):
        """Create a default icon if none exists"""
        try:
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            
            # Create a simple icon using PIL
            from PIL import Image, ImageDraw
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw a search circle
            draw.ellipse([8, 8, 56, 56], outline=(0, 120, 255, 255), width=4)
            draw.ellipse([38, 38, 48, 48], fill=(0, 120, 255, 255))
            
            img.save(icon_path)
        except Exception as e:
            print(f"[WARNING] Could not create default icon: {e}")

    def setup_hotkey_listener(self):
        """Setup enhanced hotkey listener"""
        hotkey = self.settings_manager.get('hotkey', '<ctrl>+<shift>+<space>')
        self.hotkey_listener = EnhancedHotkeyListener(hotkey)
        self.hotkey_listener.hotkey_pressed.connect(self.handle_show_overlay)
        self.hotkey_listener.start_listening()

    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.handle_show_overlay()

    def handle_show_overlay(self):
        """Show the capture overlay"""
        print("[DEBUG] Showing capture overlay...")
        self.overlay.show_overlay()

    def on_region_selected(self, rect: QRect):
        """Handle region selection with enhanced feedback"""
        print(f"[DEBUG] Region selected: {rect}")
        
        self.last_selection_rect = rect
        selection_center = rect.center()
        screen = QGuiApplication.screenAt(selection_center) or QGuiApplication.primaryScreen()
        pixel_ratio = screen.devicePixelRatio()
        
        capture_rect = {
            "top": int(rect.top() * pixel_ratio),
            "left": int(rect.left() * pixel_ratio),
            "width": int(rect.width() * pixel_ratio),
            "height": int(rect.height() * pixel_ratio),
        }
        
        # Show feedback
        if self.settings_manager.get('show_notifications', True):
            NotificationManager.show_capture_feedback()
        
        try:
            with mss.mss() as sct:
                sct_img = sct.grab(capture_rect)
                pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Store the original image
                self.last_captured_image = pil_img.copy()
                
                print("✅ Image captured, starting OCR...")
                
                # Stop any running OCR
                if self.ocr_worker and self.ocr_worker.isRunning():
                    self.ocr_worker.quit()
                    self.ocr_worker.wait()

                # Enhance image for OCR
                enhanced_img = self.image_processor.enhance_for_ocr(pil_img.copy())
                
                # Start OCR
                self.ocr_worker = EnhancedOcrWorker(enhanced_img)
                self.ocr_worker.finished.connect(self.handle_ocr_result)
                self.ocr_worker.error.connect(self.handle_ocr_error)
                self.ocr_worker.start()
                
        except Exception as e:
            print(f"[ERROR] Screen capture failed: {e}")
            QMessageBox.warning(None, "Capture Error", f"Failed to capture screen: {e}")

    def handle_ocr_result(self, ocr_text, confidence):
        """Handle OCR results with enhanced features"""
        clean_text = ocr_text.strip()
        print(f"✅ OCR Result (confidence: {confidence:.2f}): {clean_text}")
        
        self.last_ocr_text = clean_text
        
        # Auto-copy if enabled
        if self.settings_manager.get('auto_copy', True) and clean_text:
            try:
                pyperclip.copy(clean_text)
                print("[INFO] Text copied to clipboard")
            except Exception as e:
                print(f"[WARNING] Could not copy to clipboard: {e}")
        
        # Add to history
        if clean_text:
            self.search_history.add_search(clean_text)
        
        # Show results in enhanced side panel
        self.show_enhanced_side_panel(clean_text, confidence)
        
        # Show notification
        if self.settings_manager.get('show_notifications', True):
            if clean_text:
                NotificationManager.show_notification(
                    "Text Recognized", 
                    f"Found: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}", 
                    3000
                )
            else:
                NotificationManager.show_notification(
                    "No Text Found", 
                    "Try selecting a clearer text region", 
                    3000
                )

    def handle_ocr_error(self, error_message):
        """Handle OCR errors"""
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", f"Text recognition failed:\n{error_message}")

    def show_enhanced_side_panel(self, text, confidence):
        """Show enhanced side panel with more options"""
        # Update side panel with enhanced content
        self.side_panel.set_enhanced_content(
            text, 
            self.last_captured_image,  # Pass the actual captured PIL image
            self.search_engine,        # Pass our enhanced search engine
            confidence,
            self.settings_manager.get('search_engine', 'google')
        )
        self.side_panel.show_panel(self.last_selection_rect)

    def set_search_engine(self, engine_name: str):
        """Set the current search engine"""
        self.settings_manager.set('search_engine', engine_name)
        print(f"[INFO] Search engine set to: {engine_name}")
        
        # Update menu checkmarks
        menu = self.tray_icon.contextMenu()
        for action in menu.actions():
            if hasattr(action, 'menu') and action.menu():
                for sub_action in action.menu().actions():
                    if sub_action.text() in ['Google', 'Bing']:
                        sub_action.setChecked(sub_action.text().lower() == engine_name)

    def show_settings(self):
        """Show settings window"""
        if not self.settings_window:
            self.settings_window = SettingsWindow(self.settings_manager, self.hotkey_listener)
        
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()

    def show_history(self):
        """Show search history"""
        history = self.search_history.get_history()
        
        if not history:
            QMessageBox.information(None, "Search History", "No search history available.")
            return
        
        # Create simple history dialog
        history_text = "\n".join([
            f"{item['timestamp'][:19]}: {item['text'][:50]}{'...' if len(item['text']) > 50 else ''}"
            for item in history[:10]  # Show last 10
        ])
        
        QMessageBox.information(None, "Recent Searches", history_text)

    def show_about(self):
        """Show about dialog"""
        about_text = """
<h3>Circle to Search - Enhanced</h3>
<p><b>Version:</b> 2.0</p>
<p><b>Features:</b></p>
<ul>
<li>🎯 Quick screen capture with Ctrl+Shift+Space</li>
<li>🔍 Advanced OCR with confidence scoring</li>
<li>🌐 Smart Google and Bing search integration</li>
<li>📋 Auto-copy to clipboard</li>
<li>📜 Search history tracking</li>
<li>⚙️ Customizable settings</li>
<li>🔔 Smart notifications</li>
</ul>
<p><b>Usage:</b> Press Ctrl+Shift+Space anywhere to start capturing!</p>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("About Circle to Search")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

# Main execution
if __name__ == "__main__":
    # Set DPI policies
    if sys.platform == "win32":
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    
    print("🚀 Starting Enhanced Circle to Search v2.0")
    
    # Single instance lock
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search-enhanced.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running. Exiting.")
        QMessageBox.warning(None, "Already Running", 
                          "Circle to Search is already running!\n\nLook for the icon in your system tray.")
        sys.exit(0)
    
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Circle to Search Enhanced")
    app.setApplicationVersion("2.0")

    # Create main controller
    main_controller = EnhancedTrayApplication(app)

    print("✨ Enhanced Circle to Search is ready!")
    print("📖 Quick Guide:")
    print("   🎯 Press Ctrl+Shift+Space to capture any screen region")
    print("   🔍 Double-click tray icon for quick capture")
    print("   ⚙️ Right-click tray icon for settings and options")
    print("   📋 Text is automatically copied to clipboard")
    print("   🌐 Choose Google or Bing for smarter searches")

    # Start the application
    sys.exit(app.exec())