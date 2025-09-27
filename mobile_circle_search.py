# Mobile-Style Circle to Search for Desktop
# Replicating Google's Circle to Search with AI-powered features

import sys
import os
import threading
import mss
import easyocr
import numpy as np
import webbrowser
import pyperclip
import tempfile
import json
import base64
from datetime import datetime
from urllib.parse import quote_plus

# PySide6 Imports
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QScrollArea, QMessageBox,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem,
    QButtonGroup, QRadioButton
)
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QPen, QBrush, QColor, 
    QGuiApplication, QCursor, QIcon, QShortcut, QKeySequence
)
from PySide6.QtCore import (
    Qt, QObject, Signal, QThread, QTimer, QRect, 
    QRectF, QPointF, QSize, QLockFile, QDir
)

# Global hotkey
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

from PIL import Image, ImageDraw, ImageFont

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

class MobileStyleOverlay(QWidget):
    """Mobile-style overlay with Circle to Search functionality"""
    
    region_selected = Signal(QRect, str)  # rect, mode (circle, text, translate, etc.)
    
    def __init__(self):
        super().__init__()
        self.start_point = None
        self.end_point = None
        self.current_mode = "circle"  # circle, text, translate, copy
        self.screenshot = None
        self.init_overlay()
    
    def init_overlay(self):
        """Initialize the mobile-style overlay"""
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
    def show_overlay(self):
        """Show overlay with current screenshot"""
        try:
            # Capture full screen
            screen = QGuiApplication.primaryScreen()
            self.screenshot = screen.grabWindow(0)
            
            # Show fullscreen
            self.showFullScreen()
            self.raise_()
            self.activateWindow()
            
            print("[DEBUG] Mobile-style overlay activated")
        except Exception as e:
            print(f"[ERROR] Failed to show overlay: {e}")
    
    def paintEvent(self, event):
        """Paint the overlay with mobile-style UI"""
        painter = QPainter(self)
        
        if self.screenshot:
            # Draw screenshot as background
            painter.drawPixmap(0, 0, self.screenshot)
            
            # Draw dark overlay
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            
        # Draw selection if active
        if self.start_point and self.end_point:
            self.draw_selection(painter)
        
        # Draw mobile-style UI
        self.draw_mobile_ui(painter)
    
    def draw_selection(self, painter):
        """Draw selection area like mobile Circle to Search"""
        rect = QRect(self.start_point, self.end_point).normalized()
        
        # Clear selection area
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        if self.current_mode == "circle":
            # Draw circle selection
            painter.setBrush(QBrush(Qt.transparent))
            painter.drawEllipse(rect)
        else:
            # Draw rectangle selection
            painter.fillRect(rect, Qt.transparent)
        
        # Reset composition mode
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Draw selection border
        pen = QPen(QColor(66, 133, 244), 3)  # Google Blue
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        if self.current_mode == "circle":
            painter.drawEllipse(rect)
        else:
            painter.drawRect(rect)
        
        # Draw corner handles like mobile
        self.draw_handles(painter, rect)
    
    def draw_handles(self, painter, rect):
        """Draw mobile-style corner handles"""
        handle_size = 12
        pen = QPen(QColor(66, 133, 244), 2)
        brush = QBrush(Qt.white)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        # Corner handles
        corners = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]
        
        for corner in corners:
            handle_rect = QRect(corner.x() - handle_size//2, corner.y() - handle_size//2, 
                              handle_size, handle_size)
            painter.drawEllipse(handle_rect)
    
    def draw_mobile_ui(self, painter):
        """Draw mobile-style UI elements"""
        if not (self.start_point and self.end_point):
            # Draw instruction text
            font = QFont("Segoe UI", 16)
            painter.setFont(font)
            painter.setPen(Qt.white)
            
            text = "Circle to Search • Drag to select"
            text_rect = self.rect()
            text_rect.setHeight(100)
            text_rect.moveBottom(self.height() - 100)
            
            painter.drawText(text_rect, Qt.AlignCenter, text)
            
            # Draw mode selector at bottom
            self.draw_mode_selector(painter)
    
    def draw_mode_selector(self, painter):
        """Draw mobile-style mode selector"""
        # Background for mode selector
        selector_rect = QRect(50, self.height() - 120, self.width() - 100, 60)
        painter.fillRect(selector_rect, QColor(0, 0, 0, 150))
        painter.setPen(QPen(Qt.white, 1))
        painter.drawRect(selector_rect)
        
        # Mode buttons
        modes = [
            ("🔍", "circle", "Circle to Search"),
            ("📝", "text", "Select Text"),
            ("🌐", "translate", "Translate"),
            ("📋", "copy", "Copy")
        ]
        
        button_width = (selector_rect.width() - 40) // len(modes)
        
        for i, (icon, mode, label) in enumerate(modes):
            x = selector_rect.x() + 20 + i * button_width
            y = selector_rect.y() + 10
            
            # Highlight current mode
            if mode == self.current_mode:
                painter.fillRect(x - 5, y - 5, button_width - 10, 50, QColor(66, 133, 244, 100))
            
            # Draw icon
            font = QFont("Segoe UI Emoji", 20)
            painter.setFont(font)
            painter.setPen(Qt.white)
            painter.drawText(x + 10, y + 30, icon)
            
            # Draw label
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            painter.drawText(x, y + 45, button_width, 15, Qt.AlignCenter, label)
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection"""
        if event.button() == Qt.LeftButton:
            # Check if clicking on mode selector
            if self.is_mode_selector_click(event.pos()):
                self.handle_mode_click(event.pos())
                return
            
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for selection"""
        if self.start_point:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize selection"""
        if event.button() == Qt.LeftButton and self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            
            # Minimum selection size
            if rect.width() > 20 and rect.height() > 20:
                self.region_selected.emit(rect, self.current_mode)
                self.hide()
            
            self.start_point = None
            self.end_point = None
    
    def is_mode_selector_click(self, pos):
        """Check if click is on mode selector"""
        selector_rect = QRect(50, self.height() - 120, self.width() - 100, 60)
        return selector_rect.contains(pos)
    
    def handle_mode_click(self, pos):
        """Handle click on mode selector"""
        selector_rect = QRect(50, self.height() - 120, self.width() - 100, 60)
        relative_x = pos.x() - selector_rect.x()
        
        modes = ["circle", "text", "translate", "copy"]
        button_width = (selector_rect.width() - 40) // len(modes)
        mode_index = (relative_x - 20) // button_width
        
        if 0 <= mode_index < len(modes):
            self.current_mode = modes[mode_index]
            print(f"[INFO] Mode changed to: {self.current_mode}")
            self.update()
    
    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key_Escape:
            self.hide()

class AISearchHandler:
    """AI-powered search handler mimicking Google's Circle to Search"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.save_dir = self.create_save_directory()
    
    def create_save_directory(self):
        """Create directory for saved searches"""
        try:
            documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            save_path = os.path.join(documents_path, "CircleToSearch_AI")
            os.makedirs(save_path, exist_ok=True)
            return save_path
        except Exception as e:
            print(f"[ERROR] Could not create save directory: {e}")
            return tempfile.gettempdir()
    
    def ask_about_image(self, image: Image.Image, question="What is this?"):
        """AI-powered 'Ask about this image' feature"""
        try:
            # Save image for analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(self.save_dir, f"ask_{timestamp}.jpg")
            image.save(image_path, "JPEG", quality=90)
            
            # Open Google Lens with specific search
            lens_url = "https://lens.google.com/"
            webbrowser.open(lens_url)
            
            # Copy image to clipboard for easy upload
            self.copy_image_to_clipboard(image)
            
            print(f"[INFO] 🤖 Ask about image: '{question}'")
            print(f"[INFO] Image saved: {image_path}")
            print(f"[INFO] Google Lens opened - paste your image!")
            
            return True
        except Exception as e:
            print(f"[ERROR] Ask about image failed: {e}")
            return False
    
    def visual_search(self, image: Image.Image, search_type="general"):
        """Perform visual search like mobile Circle to Search"""
        try:
            # Save for visual search
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(self.save_dir, f"visual_{timestamp}.jpg")
            image.save(image_path, "JPEG", quality=95)
            
            # Copy to clipboard
            self.copy_image_to_clipboard(image)
            
            # Open appropriate search
            if search_type == "shopping":
                url = "https://lens.google.com/search?p=AbrfA8qxKCOT7Lm4vLRPd_vR8lWB9w=="
            elif search_type == "translate":
                url = "https://translate.google.com/?op=images"
            else:
                url = "https://lens.google.com/"
            
            webbrowser.open(url)
            
            print(f"[INFO] 🔍 Visual search ({search_type})")
            print(f"[INFO] Image ready for upload - paste it in the opened page!")
            
            return True
        except Exception as e:
            print(f"[ERROR] Visual search failed: {e}")
            return False
    
    def copy_image_to_clipboard(self, image: Image.Image):
        """Copy image to clipboard for easy pasting"""
        try:
            import io
            import win32clipboard
            
            # Convert to bitmap
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Remove BMP header
            output.close()
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            return True
        except ImportError:
            print("[WARNING] win32clipboard not available")
            return False
        except Exception as e:
            print(f"[ERROR] Clipboard copy failed: {e}")
            return False
    
    def translate_image_text(self, image: Image.Image, target_lang="en"):
        """Translate text in image"""
        try:
            # Save and copy image
            self.copy_image_to_clipboard(image)
            
            # Open Google Translate camera
            translate_url = "https://translate.google.com/?op=images"
            webbrowser.open(translate_url)
            
            print("[INFO] 🌐 Google Translate opened - paste your image!")
            return True
        except Exception as e:
            print(f"[ERROR] Translation failed: {e}")
            return False

class MobileStyleSidePanel(QWidget):
    """Mobile-style side panel with AI features"""
    
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.current_text = ""
        self.search_handler = AISearchHandler()
        self.init_ui()
    
    def init_ui(self):
        """Initialize mobile-style UI"""
        self.setWindowTitle("Circle to Search • AI Results")
        self.setFixedSize(400, 700)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.create_header(layout)
        
        # Content area
        self.create_content_area(layout)
        
        # AI Actions
        self.create_ai_actions(layout)
        
        # Quick Actions
        self.create_quick_actions(layout)
        
        self.setLayout(layout)
        self.apply_mobile_styling()
    
    def create_header(self, layout):
        """Create mobile-style header"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4285F4, stop:1 #34A853);
                border-radius: 0;
            }
        """)
        
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title = QLabel("Circle to Search")
        title.setFont(QFont("Google Sans", 18, QFont.Bold))
        title.setStyleSheet("color: white; margin: 0;")
        header_layout.addWidget(title)
        
        # Subtitle
        self.subtitle = QLabel("AI-powered visual search")
        self.subtitle.setFont(QFont("Google Sans", 11))
        self.subtitle.setStyleSheet("color: rgba(255,255,255,0.9);")
        header_layout.addWidget(self.subtitle)
        
        header.setLayout(header_layout)
        layout.addWidget(header)
    
    def create_content_area(self, layout):
        """Create content display area"""
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
            }
        """)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Text display
        self.text_display = QTextEdit()
        self.text_display.setPlaceholderText("Select text or image to see AI-powered results...")
        self.text_display.setFixedHeight(120)
        self.text_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #E8EAED;
                border-radius: 12px;
                padding: 15px;
                font-family: 'Google Sans', sans-serif;
                font-size: 14px;
                background: #F8F9FA;
            }
            QTextEdit:focus {
                border-color: #4285F4;
                background: white;
            }
        """)
        content_layout.addWidget(self.text_display)
        
        content_frame.setLayout(content_layout)
        layout.addWidget(content_frame)
    
    def create_ai_actions(self, layout):
        """Create AI-powered action buttons"""
        ai_frame = QFrame()
        ai_frame.setStyleSheet("background: white; border: none;")
        
        ai_layout = QVBoxLayout()
        ai_layout.setContentsMargins(20, 0, 20, 20)
        
        # AI Actions label
        ai_label = QLabel("🤖 AI Actions")
        ai_label.setFont(QFont("Google Sans", 14, QFont.Bold))
        ai_label.setStyleSheet("color: #202124; margin-bottom: 10px;")
        ai_layout.addWidget(ai_label)
        
        # AI Action buttons
        ai_buttons_layout = QVBoxLayout()
        ai_buttons_layout.setSpacing(8)
        
        # Ask about this image
        self.ask_btn = self.create_ai_button("🧠 Ask about this image", "#4285F4")
        self.ask_btn.clicked.connect(self.ask_about_image)
        ai_buttons_layout.addWidget(self.ask_btn)
        
        # Visual search
        self.visual_search_btn = self.create_ai_button("👁️ Visual search", "#34A853")
        self.visual_search_btn.clicked.connect(self.visual_search)
        ai_buttons_layout.addWidget(self.visual_search_btn)
        
        # Shop with image
        self.shop_btn = self.create_ai_button("🛒 Shop with Google", "#EA4335")
        self.shop_btn.clicked.connect(self.shop_with_image)
        ai_buttons_layout.addWidget(self.shop_btn)
        
        ai_layout.addLayout(ai_buttons_layout)
        ai_frame.setLayout(ai_layout)
        layout.addWidget(ai_frame)
    
    def create_quick_actions(self, layout):
        """Create quick action buttons"""
        quick_frame = QFrame()
        quick_frame.setStyleSheet("background: #F8F9FA; border: none;")
        
        quick_layout = QVBoxLayout()
        quick_layout.setContentsMargins(20, 20, 20, 20)
        
        # Quick Actions label
        quick_label = QLabel("⚡ Quick Actions")
        quick_label.setFont(QFont("Google Sans", 14, QFont.Bold))
        quick_label.setStyleSheet("color: #202124; margin-bottom: 10px;")
        quick_layout.addWidget(quick_label)
        
        # Quick action buttons in grid
        quick_grid = QHBoxLayout()
        quick_grid.setSpacing(10)
        
        # Row 1
        self.search_btn = self.create_quick_button("🔍", "Search")
        self.search_btn.clicked.connect(self.search_text)
        quick_grid.addWidget(self.search_btn)
        
        self.translate_btn = self.create_quick_button("🌐", "Translate")
        self.translate_btn.clicked.connect(self.translate_text)
        quick_grid.addWidget(self.translate_btn)
        
        self.copy_btn = self.create_quick_button("📋", "Copy")
        self.copy_btn.clicked.connect(self.copy_text)
        quick_grid.addWidget(self.copy_btn)
        
        self.close_btn = self.create_quick_button("❌", "Close")
        self.close_btn.clicked.connect(self.hide)
        quick_grid.addWidget(self.close_btn)
        
        quick_layout.addLayout(quick_grid)
        quick_frame.setLayout(quick_layout)
        layout.addWidget(quick_frame)
    
    def create_ai_button(self, text, color):
        """Create AI action button"""
        button = QPushButton(text)
        button.setFixedHeight(50)
        button.setFont(QFont("Google Sans", 12, QFont.Bold))
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {color}DD;
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background: {color}BB;
            }}
            QPushButton:disabled {{
                background: #E8EAED;
                color: #9AA0A6;
            }}
        """)
        return button
    
    def create_quick_button(self, icon, text):
        """Create quick action button"""
        button = QPushButton(f"{icon}\n{text}")
        button.setFixedSize(80, 80)
        button.setFont(QFont("Google Sans", 9))
        button.setStyleSheet("""
            QPushButton {
                background: white;
                border: 2px solid #E8EAED;
                border-radius: 16px;
                color: #5F6368;
            }
            QPushButton:hover {
                border-color: #4285F4;
                background: #F8F9FA;
            }
            QPushButton:pressed {
                background: #E8F0FE;
            }
        """)
        return button
    
    def apply_mobile_styling(self):
        """Apply overall mobile-style styling"""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Google Sans', 'Segoe UI', sans-serif;
            }
        """)
    
    def set_content(self, text, image, mode="circle"):
        """Set content and update UI"""
        self.current_text = text
        self.current_image = image
        
        self.text_display.setPlainText(text)
        
        # Update subtitle based on content
        if text and image:
            self.subtitle.setText("Text and image detected")
        elif text:
            self.subtitle.setText("Text detected")
        elif image:
            self.subtitle.setText("Image captured")
        else:
            self.subtitle.setText("AI-powered visual search")
        
        # Enable/disable buttons
        has_text = bool(text.strip())
        has_image = image is not None
        
        self.search_btn.setEnabled(has_text)
        self.translate_btn.setEnabled(has_text)
        self.copy_btn.setEnabled(has_text)
        
        self.ask_btn.setEnabled(has_image)
        self.visual_search_btn.setEnabled(has_image)
        self.shop_btn.setEnabled(has_image)
    
    # Action Methods
    def ask_about_image(self):
        """Ask AI about the image"""
        if self.current_image:
            success = self.search_handler.ask_about_image(self.current_image)
            if success:
                self.show_feedback("🧠 AI analysis started!")
    
    def visual_search(self):
        """Perform visual search"""
        if self.current_image:
            success = self.search_handler.visual_search(self.current_image)
            if success:
                self.show_feedback("👁️ Visual search opened!")
    
    def shop_with_image(self):
        """Shop with the image"""
        if self.current_image:
            success = self.search_handler.visual_search(self.current_image, "shopping")
            if success:
                self.show_feedback("🛒 Shopping search opened!")
    
    def search_text(self):
        """Search text on Google"""
        text = self.text_display.toPlainText().strip()
        if text:
            url = f"https://www.google.com/search?q={quote_plus(text)}"
            webbrowser.open(url)
            self.show_feedback("🔍 Google search opened!")
    
    def translate_text(self):
        """Translate text or image"""
        if self.current_image:
            success = self.search_handler.translate_image_text(self.current_image)
            if success:
                self.show_feedback("🌐 Google Translate opened!")
        elif self.current_text:
            url = f"https://translate.google.com/?sl=auto&tl=en&text={quote_plus(self.current_text)}"
            webbrowser.open(url)
            self.show_feedback("🌐 Translation opened!")
    
    def copy_text(self):
        """Copy text to clipboard"""
        text = self.text_display.toPlainText().strip()
        if text:
            try:
                pyperclip.copy(text)
                self.show_feedback("📋 Text copied!")
            except:
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                self.show_feedback("📋 Text copied!")
    
    def show_feedback(self, message):
        """Show feedback message"""
        original_title = self.windowTitle()
        self.setWindowTitle(message)
        QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))
    
    def show_panel(self, relative_rect=None):
        """Show the panel"""
        if relative_rect:
            screen = QGuiApplication.primaryScreen().geometry()
            panel_x = min(relative_rect.right() + 20, screen.width() - self.width())
            panel_y = max(0, min(relative_rect.top(), screen.height() - self.height()))
            self.move(panel_x, panel_y)
        
        self.show()
        self.raise_()
        self.activateWindow()

class OCRWorker(QThread):
    """OCR processing worker"""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, pil_image):
        super().__init__()
        self.pil_image = pil_image

    def run(self):
        try:
            reader = get_ocr_reader()
            image_np = np.array(self.pil_image)
            result = reader.readtext(image_np)
            
            recognized_texts = [text for bbox, text, conf in result if conf > 0.3]
            full_text = "\n".join(recognized_texts)
            
            self.finished.emit(full_text)
        except Exception as e:
            self.error.emit(f"OCR Error: {str(e)}")

class GlobalHotkeyListener(QObject):
    """Global hotkey listener"""
    hotkey_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.active = False

    def start_listening(self):
        if not PYNPUT_AVAILABLE:
            return False
            
        try:
            self.active = True
            thread = threading.Thread(target=self._run_listener, daemon=True)
            thread.start()
            return True
        except Exception as e:
            print(f"[ERROR] Hotkey failed: {e}")
            return False

    def _run_listener(self):
        try:
            with keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+<space>': self._on_hotkey,
                '<ctrl>+<alt>+s': self._on_hotkey
            }) as listener:
                while self.active:
                    threading.Event().wait(0.1)
        except Exception as e:
            print(f"[ERROR] Hotkey listener error: {e}")

    def _on_hotkey(self):
        if self.active:
            self.hotkey_pressed.emit()

class MobileCircleToSearch(QObject):
    """Main application mimicking mobile Circle to Search"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        # Components
        self.overlay = MobileStyleOverlay()
        self.side_panel = MobileStyleSidePanel()
        self.search_handler = AISearchHandler()
        
        # State
        self.ocr_worker = None
        self.last_image = None
        
        # Setup
        self.setup_hotkeys()
        self.overlay.region_selected.connect(self.on_region_selected)
        
        print("[INFO] Mobile-style Circle to Search initialized!")
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        if PYNPUT_AVAILABLE:
            self.hotkey_listener = GlobalHotkeyListener()
            self.hotkey_listener.hotkey_pressed.connect(self.show_circle_to_search)
            success = self.hotkey_listener.start_listening()
            
            if success:
                print("[INFO] ✅ Global hotkeys active: Ctrl+Shift+Space, Ctrl+Alt+S")
            else:
                print("[WARNING] Hotkeys failed to start")
        else:
            print("[WARNING] Global hotkeys not available")
    
    def show_circle_to_search(self):
        """Show Circle to Search overlay"""
        print("[DEBUG] 🎯 Circle to Search activated!")
        self.overlay.show_overlay()
    
    def on_region_selected(self, rect, mode):
        """Handle region selection with mode"""
        print(f"[DEBUG] Region selected: {rect}, Mode: {mode}")
        
        # Capture the selected region
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
                self.last_image = pil_img.copy()
                
                # Handle based on mode
                if mode == "circle":
                    self.handle_circle_search(pil_img, rect)
                elif mode == "text":
                    self.handle_text_extraction(pil_img, rect)
                elif mode == "translate":
                    self.handle_translate(pil_img, rect)
                elif mode == "copy":
                    self.handle_copy(pil_img, rect)
                    
        except Exception as e:
            print(f"[ERROR] Capture failed: {e}")
    
    def handle_circle_search(self, image, rect):
        """Handle Circle to Search (AI analysis)"""
        print("[INFO] 🔍 Circle to Search - AI analysis")
        
        # Perform OCR
        if self.ocr_worker and self.ocr_worker.isRunning():
            self.ocr_worker.quit()
            self.ocr_worker.wait()
        
        self.ocr_worker = OCRWorker(image)
        self.ocr_worker.finished.connect(lambda text: self.show_ai_results(text, image, "circle"))
        self.ocr_worker.error.connect(lambda err: self.show_ai_results("", image, "circle"))
        self.ocr_worker.start()
    
    def handle_text_extraction(self, image, rect):
        """Handle text extraction"""
        print("[INFO] 📝 Text extraction")
        
        if self.ocr_worker and self.ocr_worker.isRunning():
            self.ocr_worker.quit()
            self.ocr_worker.wait()
        
        self.ocr_worker = OCRWorker(image)
        self.ocr_worker.finished.connect(lambda text: self.show_ai_results(text, image, "text"))
        self.ocr_worker.error.connect(lambda err: print(f"[ERROR] OCR failed: {err}"))
        self.ocr_worker.start()
    
    def handle_translate(self, image, rect):
        """Handle translation"""
        print("[INFO] 🌐 Translation")
        self.search_handler.translate_image_text(image)
    
    def handle_copy(self, image, rect):
        """Handle copy to clipboard"""
        print("[INFO] 📋 Copy to clipboard")
        
        # Copy image to clipboard
        success = self.search_handler.copy_image_to_clipboard(image)
        if success:
            print("[INFO] ✅ Image copied to clipboard!")
        
        # Also extract and copy text
        if self.ocr_worker and self.ocr_worker.isRunning():
            self.ocr_worker.quit()
            self.ocr_worker.wait()
        
        self.ocr_worker = OCRWorker(image)
        self.ocr_worker.finished.connect(self.copy_extracted_text)
        self.ocr_worker.start()
    
    def copy_extracted_text(self, text):
        """Copy extracted text to clipboard"""
        if text.strip():
            try:
                pyperclip.copy(text)
                print(f"[INFO] ✅ Text copied: '{text[:50]}...'")
            except:
                print("[WARNING] Could not copy text to clipboard")
    
    def show_ai_results(self, text, image, mode):
        """Show AI results in side panel"""
        self.side_panel.set_content(text, image, mode)
        self.side_panel.show_panel()
        
        # Auto-actions based on mode
        if mode == "circle" and text.strip():
            # Auto-search for Circle to Search
            url = f"https://www.google.com/search?q={quote_plus(text)}"
            webbrowser.open(url)
            print(f"[INFO] 🔍 Auto-searched: '{text[:50]}...'")

if __name__ == "__main__":
    print("🚀 Starting Mobile-Style Circle to Search")
    
    # Single instance check
    lock_file = QLockFile(os.path.join(QDir.tempPath(), "mobile-circle-search.lock"))
    if not lock_file.tryLock(100):
        print("[ERROR] Already running!")
        sys.exit(0)
    
    # Create app
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Mobile Circle to Search")
    
    # Create main app
    circle_search = MobileCircleToSearch(app)
    
    print("✨ Mobile-Style Circle to Search Ready!")
    print("📱 Features:")
    print("   🎯 Press Ctrl+Shift+Space for Circle to Search")
    print("   🔍 Circle mode: AI-powered analysis")  
    print("   📝 Text mode: Extract text")
    print("   🌐 Translate mode: Instant translation")
    print("   📋 Copy mode: Copy to clipboard")
    print("   🧠 Ask about this image")
    print("   👁️ Visual search")
    print("   🛒 Shop with Google")
    print("   ❌ Press Ctrl+C to quit")
    
    sys.exit(app.exec())