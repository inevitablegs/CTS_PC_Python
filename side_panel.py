# file: side_panel.py

import os
import sys
import json
import webbrowser

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QApplication, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QRect, QTimer, QObject, Slot
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

from core.image_search import ImageSearchHandler
from utils.image_processing import ImageProcessor

class Bridge(QObject):
    """Bridge for communication between Python and JavaScript."""
    # Signal to notify the main window to close
    closed = Signal()

    @Slot()
    def onClose(self):
        print("JS requested to close the panel.")
        self.closed.emit()

    @Slot(str)
    def onCopy(self, text):
        print(f"JS requested to copy text: {text[:30]}...")
        QApplication.clipboard().setText(text)

    @Slot(str)
    def onSearch(self, text):
        print(f"JS requested to search for: {text[:30]}...")
        url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
        webbrowser.open(url)


class SidePanelWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.search_manager = None
        self.current_image = None
        
        # Initialize these if the classes exist
        try:
            from core.image_search import ImageSearchHandler
            from utils.image_processing import ImageProcessor
            self.image_search_handler = ImageSearchHandler()
            self.image_processor = ImageProcessor()
        except ImportError:
            print("[WARNING] Image search modules not found, using basic functionality")
            self.image_search_handler = None
            self.image_processor = None
        
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Circle to Search - Results")
        self.setFixedSize(350, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Create main layout (fix the naming issue)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Title label
        title_label = QLabel("🔍 Search Results")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Text display area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Recognized text will appear here...")
        self.text_edit.setFont(QFont("Arial", 10))
        self.text_edit.setMaximumHeight(200)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        main_layout.addWidget(self.text_edit)
        
        # Search buttons layout
        search_layout = QHBoxLayout()
        
        self.text_search_btn = QPushButton("🔍 Search Text")
        self.text_search_btn.clicked.connect(self.search_text)
        self.text_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        search_layout.addWidget(self.text_search_btn)
        
        self.image_search_btn = QPushButton("📷 Search Image")
        self.image_search_btn.clicked.connect(self.search_image)
        self.image_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        search_layout.addWidget(self.image_search_btn)
        
        main_layout.addLayout(search_layout)
        
        # Close button
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.hide_panel)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        main_layout.addWidget(close_btn)
        
        # Set overall window style
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 10px;
            }
        """)

    def set_text(self, text):
        js_escaped_text = json.dumps(text)
        js_code = f"updateText({js_escaped_text});"
        self.web_view.page().runJavaScript(js_code)

    def show_panel(self, selection_rect: QRect):
        """Calculates geometry and shows the panel on the correct screen."""
        # Find the screen where the selection was made
        screen = QGuiApplication.screenAt(selection_rect.center())
        if not screen:
            screen = QGuiApplication.primaryScreen()
        
        # Use availableGeometry to avoid overlapping with the taskbar
        screen_geom = screen.availableGeometry()

        # Calculate dimensions (1/4 of screen width, full height)
        panel_width = screen_geom.width() // 4
        panel_height = screen_geom.height()
        
        # Calculate position (docked to the right)
        pos_x = screen_geom.right() - panel_width
        pos_y = screen_geom.top()

        self.setGeometry(pos_x, pos_y, panel_width, panel_height)
        self.web_view.setGeometry(self.rect()) # Ensure webview fills the panel

        self.show()
        self.activateWindow()
        self.raise_()

    def set_content(self, text: str, image=None, search_manager=None):
        """Set both text and image content"""
        self.text_edit.setPlainText(text)
        self.current_image = image
        self.search_manager = search_manager
        
        # Enable/disable buttons based on content
        self.text_search_btn.setEnabled(bool(text.strip()))
        self.image_search_btn.setEnabled(image is not None)

    def search_text(self):
        """Search using the recognized text"""
        if self.search_manager and self.text_edit.toPlainText().strip():
            query = self.text_edit.toPlainText().strip()
            self.search_manager.search_text(query)
            print(f"[INFO] Searching text: {query}")

    def search_image(self):
        """Search using the captured image with enhanced functionality"""
        if self.current_image:
            try:
                print("[INFO] Starting enhanced image search...")
                
                if self.image_search_handler:
                    # Use enhanced search handler
                    current_engine = self.search_manager.get_current_engine() if self.search_manager else "google"
                    result_url = self.image_search_handler.perform_advanced_search(
                        self.current_image, 
                        current_engine
                    )
                    
                    if result_url:
                        print(f"[INFO] Enhanced image search initiated: {result_url}")
                    else:
                        print("[WARNING] Enhanced image search failed, using fallback")
                        self._fallback_image_search()
                else:
                    # Fallback to basic image search
                    self._fallback_image_search()
                
            except Exception as e:
                print(f"[ERROR] Image search error: {e}")
                self._fallback_image_search()
        else:
            print("[WARNING] No image available for search")
    
    def _fallback_image_search(self):
        """Fallback image search method"""
        print("[INFO] Using fallback image search - opening Google Images")
        import webbrowser
        webbrowser.open("https://images.google.com/")
        print("📖 Click the camera icon 📷 in Google Images to upload your screenshot")

    def show_panel(self, relative_rect=None):
        """Show the side panel"""
        if relative_rect:
            # Position panel to the right of the selection
            screen = QGuiApplication.primaryScreen().geometry()
            panel_x = min(relative_rect.right() + 10, screen.width() - self.width())
            panel_y = max(0, relative_rect.top())
            
            self.move(panel_x, panel_y)
        
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_panel(self):
        """Hide the side panel"""
        self.hide()

# Test the side panel independently
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    panel = SidePanelWindow()
    panel.set_content("Test text content", None, None)
    panel.show()
    
    sys.exit(app.exec())