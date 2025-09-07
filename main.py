# file: main.py (MODIFIED FOR DEBUGGING)

import sys
import os
import threading
from pynput import keyboard

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal, QTimer, QLockFile, QDir, Qt, QRect, QThread
from PySide6.QtGui import QGuiApplication # Make sure this is imported at the top

from overlay import OverlayWindow

# --- Phase 2 (Screen Capture) Preview ---
import mss
import mss.tools
from PIL import Image
# ---

# This is a key change to make signals work reliably from other threads
# It allows us to pass arguments (like QRect) safely across threads
from PySide6.QtCore import QCoreApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)


from PIL.Image import Image as PILImage
import asyncio
from winsdk.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode, BitmapDecoder
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.storage.streams import DataReader, InMemoryRandomAccessStream


from popover import PopoverWindow

class HotkeyListener(QObject):
    """Listens for global hotkeys in a separate thread."""
    hotkey_pressed = Signal()

    def __init__(self, hotkey_combination):
        super().__init__()
        self.hotkey_combination = hotkey_combination
        self.listener = None
        print(f"[DEBUG] Hotkey listener created for: {self.hotkey_combination}")

    def start_listening(self):
        print("[DEBUG] Attempting to start hotkey listener thread...")
        listener_thread = threading.Thread(target=self._run, daemon=True)
        listener_thread.start()

    def _run(self):
        print("[DEBUG] Hotkey listener thread is now running.")
        try:
            with keyboard.GlobalHotKeys({self.hotkey_combination: self._on_activate}) as self.listener:
                self.listener.join()
        except Exception as e:
            print(f"[ERROR] Failed to start hotkey listener: {e}")
            print("[ERROR] This might be a permissions issue or another app using the hotkey.")


    def _on_activate(self):
        print("✅ [DEBUG] HOTKEY DETECTED in listener thread!")
        # GUI operations must be done in the main thread, so we emit a signal
        self.hotkey_pressed.emit()


class TrayApplication:
    def __init__(self):
        print("[DEBUG] Initializing TrayApplication...")
        self.popover = PopoverWindow()
        self.last_selection_rect = None
        self.ocr_worker = None
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.overlay = OverlayWindow()
        self.overlay.region_selected.connect(self.on_region_selected)
        
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

        self.hotkey_listener = HotkeyListener('<ctrl>+<shift>+ ')
        self.hotkey_listener.hotkey_pressed.connect(self.handle_show_overlay)
        self.hotkey_listener.start_listening()
        print("[DEBUG] TrayApplication initialized successfully.")

    def handle_show_overlay(self):
        print("[DEBUG] Hotkey signal received in main thread. Showing overlay...")
        self.overlay.show_overlay()

    # file: main.py

    # ... (keep all the other code the same) ...

    

    def on_region_selected(self, rect: QRect):
        """
        Captures the region to an in-memory object and starts the OCR process.
        """
        print("\n--- CAPTURE INITIATED ---")
        self.last_selection_rect = rect # Store rect for positioning the popover

        # ... (The DPI calculation code is still needed) ...
        selection_center = rect.center()
        screen = QGuiApplication.screenAt(selection_center)
        if not screen:
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
                
                print("✅ In-memory image captured. Starting OCR worker...")
                
                # --- TRIGGER PHASE 3 ---
                # Stop any previous worker
                if self.ocr_worker and self.ocr_worker.isRunning():
                    self.ocr_worker.quit()
                    self.ocr_worker.wait()

                self.ocr_worker = OcrWorker(pil_img)
                self.ocr_worker.finished.connect(self.handle_ocr_result)
                self.ocr_worker.error.connect(self.handle_ocr_error)
                self.ocr_worker.start()

        except mss.exception.ScreenShotError as e:
            print(f"[ERROR] MSS screen capture failed: {e}")

    # ... (the rest of your TrayApplication class definition) ...
    # self.overlay.region_selected.connect(self.on_region_selected) # This line should already exist

    def handle_ocr_result(self, ocr_text):
        """Receives text and shows it in the popover."""
        print(f"--- OCR FINISHED ---")
        clean_text = ocr_text.strip()
        print(f"Recognized Text: {clean_text}")

        if not clean_text:
            print("No text recognized.")
            return

        # --- TRIGGER PHASE 4 ---
        self.popover.set_text(clean_text)
        # Position popover below the selection area
        self.popover.show_at(self.last_selection_rect.bottomLeft())

    def handle_ocr_error(self, error_message):
        """Receives error messages from the OCR worker."""
        print(f"[ERROR] OCR failed: {error_message}")
        QMessageBox.warning(None, "OCR Error", error_message)

    def run(self):
        print("[DEBUG] Starting Qt application event loop...")
        return self.app.exec()



class OcrWorker(QThread):
    """Runs OCR in a background thread to avoid freezing the GUI."""
    finished = Signal(str) # Signal to emit recognized text
    error = Signal(str)    # Signal to emit error messages

    def __init__(self, pil_image: PILImage):
        super().__init__()
        self.pil_image = pil_image

    async def perform_ocr(self):
        """The core async OCR logic using Windows.Media.Ocr."""
        try:
            # 1. Convert Pillow image to a format Windows OCR can understand
            stream = InMemoryRandomAccessStream()
            # Pillow images are RGB, but we need BGRA for SoftwareBitmap
            rgba_image = self.pil_image.convert("RGBA")
            # Invert channels from RGBA to BGRA
            r, g, b, a = rgba_image.split()
            bgra_image = Image.merge("RGBA", (b, g, r, a))
            
            await stream.write_async(bgra_image.tobytes())
            stream.seek(0)
            
            decoder = await BitmapDecoder.create_async(stream)
            software_bitmap = await decoder.get_software_bitmap_async()

            # 2. Initialize OCR Engine and process the image
            engine = OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                self.error.emit("Could not create OCR Engine. Check language packs.")
                return

            result = await engine.recognize_async(software_bitmap)
            self.finished.emit(result.text)
        except Exception as e:
            self.error.emit(f"An error occurred during OCR: {e}")

    def run(self):
        """Entry point for the thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.perform_ocr())

# file: main.py (at the very bottom)

if __name__ == "__main__":
    # Set High DPI scaling policies before creating the application object.
    if sys.platform == "win32":
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QGuiApplication
        
        # This one is still useful for non-integer scaling
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        # This one is deprecated and can be removed.
        # QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling) 
    
    print("--- Starting Application ---")
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "circle-to-search.lock"))
    
    if not lock_file.tryLock(100):
        print("[ERROR] Another instance is already running. Exiting.")
        sys.exit(0)

    tray_app = TrayApplication()
    sys.exit(tray_app.run())