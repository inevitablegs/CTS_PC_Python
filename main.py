# file: main.py (RESTRUCTURED AND FINAL)

import sys
import os
import threading
import webbrowser
from pynput import keyboard
import io

# --- PySide6 Imports ---
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtCore import (
    QObject, Signal, QThread, QTimer, QLockFile, QDir, QRect, Qt
)

# --- Local Imports ---
from overlay import OverlayWindow
from popover import PopoverWindow
from PIL import Image
import mss
import mss.tools

# --- OCR Imports (already present in your code) ---
from PIL.Image import Image as PILImage
import asyncio
from winsdk.windows.graphics.imaging import BitmapDecoder, BitmapPixelFormat, BitmapAlphaMode, SoftwareBitmap
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.storage.streams import InMemoryRandomAccessStream



import easyocr
import numpy

# --- LAZY LOADER FOR THE OCR MODEL ---
# This is a global placeholder. We'll initialize the model once on the first use.
# This keeps the application startup very fast.
# We specify gpu=False to ensure it runs on all systems without needing a special GPU setup.
EASYOCR_READER = None


def get_ocr_reader():
    """Creates or returns the singleton OCR reader instance."""
    global EASYOCR_READER
    if EASYOCR_READER is None:
        print("[INFO] Initializing EasyOCR Reader for the first time... (this may take a moment)")
        # You can add more languages here, e.g., ['en', 'ch_sim', 'fr']
        EASYOCR_READER = easyocr.Reader(['en'], gpu=False)
        print("[INFO] EasyOCR Reader initialized.")
    return EASYOCR_READER
# ---
# NOTE: The HotkeyListener and OcrWorker classes remain the same.
# I am including them here so you can replace the whole file easily.
# ---

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

class OcrWorker(QThread):
    """Runs OCR in a background thread to avoid freezing the GUI."""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, pil_image: PILImage):
        super().__init__()
        self.pil_image = pil_image

    async def perform_ocr(self):
        try:
            stream = InMemoryRandomAccessStream()
            rgba_image = self.pil_image.convert("RGBA")
            r, g, b, a = rgba_image.split()
            bgra_image = Image.merge("RGBA", (b, g, r, a))
            
            await stream.write_async(bgra_image.tobytes())
            stream.seek(0)
            
            decoder = await BitmapDecoder.create_async(stream)
            software_bitmap = await decoder.get_software_bitmap_async()

            engine = OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                self.error.emit("Could not create OCR Engine. Check language packs.")
                return

            result = await engine.recognize_async(software_bitmap)
            self.finished.emit(result.text)
        except Exception as e:
            self.error.emit(f"An error occurred during OCR: {e}")
        
    async def perform_ocr(self):
        """
        The core async OCR logic, using a robust in-memory PNG conversion.
        """
        try:
            # 1. Save the Pillow image to an in-memory PNG byte stream.
            #    This is a very reliable way to format image data.
            byte_stream = io.BytesIO()
            self.pil_image.convert("RGBA").save(byte_stream, format="PNG")
            
            # 2. Create a Windows Runtime stream from the PNG bytes.
            winrt_stream = InMemoryRandomAccessStream()
            await winrt_stream.write_async(byte_stream.getvalue())
            winrt_stream.seek(0) # IMPORTANT: Rewind the stream to the beginning

            # 3. Use BitmapDecoder to reliably create a SoftwareBitmap.
            #    This lets Windows handle the parsing of the PNG data.
            decoder = await BitmapDecoder.create_async(winrt_stream)
            software_bitmap = await decoder.get_software_bitmap_async(
                BitmapPixelFormat.BGRA8, 
                BitmapAlphaMode.PREMULTIPLIED
            )

            # 4. Initialize OCR Engine and process the image.
            engine = OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                self.error.emit("Could not create OCR Engine. Check your Windows language packs.")
                return

            result = await engine.recognize_async(software_bitmap)
            self.finished.emit(result.text)
        except Exception as e:
            # repr(e) gives more detailed error info
            self.error.emit(f"An error occurred during OCR: {repr(e)}")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.perform_ocr())


# --- THE RESTRUCTURED MAIN APPLICATION CLASS ---
class TrayApplication(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        print("[DEBUG] Initializing TrayApplication...")
        
        # Now we create widgets, which is safe because QApplication already exists.
        self.overlay = OverlayWindow()
        self.popover = PopoverWindow()
        
        self.overlay.region_selected.connect(self.on_region_selected)

        self.ocr_worker = None
        self.last_selection_rect = None

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
        capture_action = QAction("Capture Region", parent=self.app)
        capture_action.triggered.connect(self.handle_show_overlay)
        menu.addAction(capture_action)

        exit_action = QAction("Exit", parent=self.app)
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        print("[DEBUG] Tray icon should be visible now.")

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
                print("✅ In-memory image captured. Starting OCR worker...")
                
                if self.ocr_worker and self.ocr_worker.isRunning():
                    self.ocr_worker.quit()
                    self.ocr_worker.wait()

                # Use the new, robust EasyOCR worker
                self.ocr_worker = EasyOcrWorker(pil_img)
                self.ocr_worker.finished.connect(self.handle_ocr_result)
                self.ocr_worker.error.connect(self.handle_ocr_error)
                self.ocr_worker.start()
        except mss.exception.ScreenShotError as e:
            print(f"[ERROR] MSS screen capture failed: {e}")

    def handle_ocr_result(self, ocr_text):
        clean_text = ocr_text.strip()
        print(f"Recognized Text: {clean_text}")
        if not clean_text:
            return
        
        self.popover.set_text(clean_text)
        self.popover.show_at(self.last_selection_rect.bottomLeft())

    def handle_ocr_error(self, error_message):
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", error_message)


# --- The New Worker Class ---
class EasyOcrWorker(QThread):
    """Runs EasyOCR in a background thread."""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, pil_image: PILImage):
        super().__init__()
        self.pil_image = pil_image

    def run(self):
        """Entry point for the thread."""
        try:
            # 1. Get the initialized OCR reader. The first time this runs, it will be slow.
            reader = get_ocr_reader()

            # 2. Convert the Pillow image to a NumPy array, which EasyOCR expects.
            image_np = numpy.array(self.pil_image)

            # 3. Perform OCR. result is a list of (bbox, text, confidence).
            result = reader.readtext(image_np)

            # 4. Extract and join the recognized text.
            recognized_texts = [text for bbox, text, conf in result]
            full_text = "\n".join(recognized_texts)

            self.finished.emit(full_text)

        except Exception as e:
            self.error.emit(f"An error occurred during EasyOCR: {repr(e)}")

# --- THE NEW, FOOLPROOF MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # 1. Set DPI policies before anything else.
    if sys.platform == "win32":
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    print("--- Starting Application ---")
    
    # 2. Handle single instance lock.
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running. Exiting.")
        sys.exit(0)
    
    # 3. Create the QApplication object FIRST. This is the fix.
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 4. THEN create our application controller.
    main_controller = TrayApplication(app)

    # 5. Start the event loop.
    sys.exit(app.exec())