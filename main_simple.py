# file: main_simple.py (Simplified version without Windows SDK)

import sys
import os
import threading
import asyncio
import mss
import easyocr
import numpy
from pynput import keyboard

# PySide6 Imports
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtCore import (
    QObject, Signal, QThread, QTimer, QLockFile, QDir, QRect, Qt
)

# Local Imports
from overlay import OverlayWindow
from side_panel import SidePanelWindow
from PIL import Image

# New imports for enhanced functionality
from core.search_engines import SearchEngineManager
from core.image_search import ImageSearchHandler
from utils.image_processing import ImageProcessor

# --- LAZY LOADER FOR THE OCR MODEL ---
EASYOCR_READER = None

def get_ocr_reader():
    """Creates or returns the singleton OCR reader instance."""
    global EASYOCR_READER
    if EASYOCR_READER is None:
        print("[INFO] Initializing EasyOCR Reader for the first time... (this may take a moment)")
        EASYOCR_READER = easyocr.Reader(['en'], gpu=False)
        print("[INFO] EasyOCR Reader initialized.")
    return EASYOCR_READER

class HotkeyListener(QObject):
    """Listens for global hotkeys in a separate thread."""
    hotkey_pressed = Signal()

    def __init__(self, hotkey_combination):
        super().__init__()
        self.hotkey_combination = hotkey_combination
        self.listener = None

    def start_listening(self):
        listener_thread = threading.Thread(target=self._run, daemon=True)
        listener_thread.start()

    def _run(self):
        try:
            with keyboard.GlobalHotKeys({self.hotkey_combination: self._on_activate}) as self.listener:
                self.listener.join()
        except Exception as e:
            print(f"[ERROR] Failed to start hotkey listener: {e}")

    def _on_activate(self):
        self.hotkey_pressed.emit()

class EasyOcrWorker(QThread):
    """Runs EasyOCR in a background thread."""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, pil_image):
        super().__init__()
        self.pil_image = pil_image

    def run(self):
        """Entry point for the thread."""
        try:
            # Get the initialized OCR reader
            reader = get_ocr_reader()

            # Convert the Pillow image to a NumPy array, which EasyOCR expects
            image_np = numpy.array(self.pil_image)

            # Perform OCR
            result = reader.readtext(image_np)

            # Extract and join the recognized text
            recognized_texts = [text for bbox, text, conf in result]
            full_text = "\n".join(recognized_texts)

            self.finished.emit(full_text)

        except Exception as e:
            self.error.emit(f"An error occurred during EasyOCR: {repr(e)}")

class TrayApplication(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        print("[DEBUG] Initializing TrayApplication...")
        
        # Initialize search components
        self.search_manager = SearchEngineManager()
        self.image_search_handler = ImageSearchHandler()
        self.image_processor = ImageProcessor()
        
        # Create widgets
        self.overlay = OverlayWindow()
        self.side_panel = SidePanelWindow()
        
        self.overlay.region_selected.connect(self.on_region_selected)

        self.ocr_worker = None
        self.last_selection_rect = None
        self.last_captured_image = None

        self.setup_tray_icon()
        self.setup_hotkey_listener()
        print("[DEBUG] TrayApplication initialized successfully.")

    def setup_tray_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "assets/icon.png")
        if not os.path.exists(icon_path):
            print(f"[FATAL ERROR] Icon file not found at: {icon_path}")
            sys.exit(1)

        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), parent=self.app)
        self.tray_icon.setToolTip("Circle-to-Search")

        menu = QMenu()
        
        # Capture options
        capture_action = QAction("Capture Region")
        capture_action.triggered.connect(self.handle_show_overlay)
        menu.addAction(capture_action)
        
        menu.addSeparator()
        
        # Search engine selection
        search_menu = QMenu("Search Engine")
        
        google_action = QAction("Google")
        google_action.setCheckable(True)
        google_action.setChecked(True)
        google_action.triggered.connect(lambda: self.set_search_engine('google'))
        search_menu.addAction(google_action)
        
        bing_action = QAction("Bing")
        bing_action.setCheckable(True)
        bing_action.triggered.connect(lambda: self.set_search_engine('bing'))
        search_menu.addAction(bing_action)
        
        menu.addMenu(search_menu)
        menu.addSeparator()

        exit_action = QAction("Exit")
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        print("[DEBUG] Tray icon should be visible now.")

    def set_search_engine(self, engine_name: str):
        """Set the current search engine"""
        self.search_manager.set_engine(engine_name)
        print(f"[INFO] Search engine set to: {engine_name}")

    def setup_hotkey_listener(self):
        self.hotkey_listener = HotkeyListener('<ctrl>+<alt>+s')
        self.hotkey_listener.hotkey_pressed.connect(self.handle_show_overlay)
        self.hotkey_listener.start_listening()

    def handle_show_overlay(self):
        self.overlay.show_overlay()

    def on_region_selected(self, rect: QRect):
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
        
        try:
            with mss.mss() as sct:
                sct_img = sct.grab(capture_rect)
                pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                # Store the original image for image search
                self.last_captured_image = pil_img.copy()
                
                print("✅ In-memory image captured. Starting OCR worker...")
                
                if self.ocr_worker and self.ocr_worker.isRunning():
                    self.ocr_worker.quit()
                    self.ocr_worker.wait()

                # Enhance image for OCR
                enhanced_img = self.image_processor.enhance_for_ocr(pil_img.copy())
                
                # Use EasyOCR worker
                self.ocr_worker = EasyOcrWorker(enhanced_img)
                self.ocr_worker.finished.connect(self.handle_ocr_result)
                self.ocr_worker.error.connect(self.handle_ocr_error)
                self.ocr_worker.start()
        except Exception as e:
            print(f"[ERROR] Screen capture failed: {e}")

    def handle_ocr_result(self, ocr_text):
        clean_text = ocr_text.strip()
        print(f"Recognized Text: {clean_text}")
        
        # Pass both text and image to side panel
        self.side_panel.set_content(clean_text, self.last_captured_image, self.search_manager)
        self.side_panel.show_panel(self.last_selection_rect)

    def handle_ocr_error(self, error_message):
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", error_message)

if __name__ == "__main__":
    # Set DPI policies before anything else
    if sys.platform == "win32":
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    print("--- Starting Circle to Search Application ---")
    
    # Handle single instance lock
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running. Exiting.")
        sys.exit(0)
    
    # Create the QApplication object
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Create our application controller
    main_controller = TrayApplication(app)

    print("🚀 Application started successfully!")
    print("📝 Instructions:")
    print("   - Look for the Circle to Search icon in your system tray")
    print("   - Right-click the tray icon to access options")
    print("   - Press Ctrl+Alt+S to start screen capture")
    print("   - Use left mouse button to drag and select text/image region")
    print("   - The app will perform OCR and offer search options")
    print("\n✨ Ready to use! Press Ctrl+C in terminal to exit.")

    # Start the event loop
    sys.exit(app.exec())