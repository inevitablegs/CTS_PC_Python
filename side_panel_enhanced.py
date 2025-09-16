# Enhanced Side Panel for Circle to Search
# Version 2.0 - More robust and feature-rich

import os
import sys
import json
import webbrowser
import pyperclip
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QApplication, QScrollArea, QFrame, QProgressBar,
    QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, QRect, QTimer, QObject, Slot
from PySide6.QtGui import QFont, QGuiApplication, QPixmap, QPainter
from PIL import Image

# Try to import enhanced modules
try:
    from core.image_search import ImageSearchHandler
    from utils.image_processing import ImageProcessor
    HAS_ENHANCED_MODULES = True
except ImportError:
    HAS_ENHANCED_MODULES = False
    print("[WARNING] Enhanced modules not found, using basic functionality")

class EnhancedSidePanelWindow(QWidget):
    """Enhanced side panel with better UI and more features"""
    
    def __init__(self):
        super().__init__()
        self.search_manager = None
        self.current_image = None
        self.confidence = 0.0
        self.current_engine = 'google'
        self.last_search_text = ""
        
        # Initialize enhanced modules if available
        if HAS_ENHANCED_MODULES:
            self.image_search_handler = ImageSearchHandler()
            self.image_processor = ImageProcessor()
        else:
            self.image_search_handler = None
            self.image_processor = None
        
        self.init_enhanced_ui()

    def init_enhanced_ui(self):
        """Initialize the enhanced user interface"""
        # Set window properties
        self.setWindowTitle("Circle to Search - Enhanced Results")
        self.setFixedSize(420, 650)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Header with gradient background
        self.create_header(main_layout)
        
        # Text display section
        self.create_text_section(main_layout)
        
        # Search options section
        self.create_search_section(main_layout)
        
        # Additional features section
        self.create_features_section(main_layout)
        
        # Action buttons
        self.create_action_buttons(main_layout)
        
        # Apply overall styling
        self.apply_styling()

    def create_header(self, layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                border: 2px solid #5a6fd8;
            }
        """)
        
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Title
        title_label = QLabel("🔍 Circle to Search")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white; margin: 0;")
        header_layout.addWidget(title_label)
        
        # Confidence and engine info
        info_layout = QHBoxLayout()
        
        self.confidence_label = QLabel("Confidence: --")
        self.confidence_label.setFont(QFont("Segoe UI", 9))
        self.confidence_label.setStyleSheet("color: #E8EAF6; font-weight: bold;")
        info_layout.addWidget(self.confidence_label)
        
        self.engine_label = QLabel("Engine: Google")
        self.engine_label.setFont(QFont("Segoe UI", 9))
        self.engine_label.setAlignment(Qt.AlignRight)
        self.engine_label.setStyleSheet("color: #E8EAF6; font-weight: bold;")
        info_layout.addWidget(self.engine_label)
        
        header_layout.addLayout(info_layout)
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def create_text_section(self, layout):
        """Create the text display section"""
        text_frame = QFrame()
        text_frame.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(10, 10, 10, 10)
        
        # Section label
        text_label = QLabel("📝 Recognized Text")
        text_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        text_label.setStyleSheet("color: #333; margin-bottom: 5px;")
        text_layout.addWidget(text_label)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Recognized text will appear here...\nYou can edit this text before searching.")
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setFixedHeight(120)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #BDBDBD;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                selection-background-color: #2196F3;
            }
            QTextEdit:focus {
                border-color: #2196F3;
                background-color: #F8F9FA;
            }
        """)
        text_layout.addWidget(self.text_edit)
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setFont(QFont("Segoe UI", 8))
        self.char_count_label.setAlignment(Qt.AlignRight)
        self.char_count_label.setStyleSheet("color: #666; margin-top: 5px;")
        text_layout.addWidget(self.char_count_label)
        
        # Connect text change to update character count
        self.text_edit.textChanged.connect(self.update_char_count)
        
        text_frame.setLayout(text_layout)
        layout.addWidget(text_frame)

    def create_search_section(self, layout):
        """Create the search options section"""
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        # Section label
        search_label = QLabel("🔍 Search Options")
        search_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        search_label.setStyleSheet("color: #333; margin-bottom: 8px;")
        search_layout.addWidget(search_label)
        
        # Primary search buttons
        primary_layout = QHBoxLayout()
        primary_layout.setSpacing(8)
        
        self.text_search_btn = self.create_styled_button("🔍 Search Text", "#4CAF50", "#45A049")
        self.text_search_btn.clicked.connect(self.search_text)
        primary_layout.addWidget(self.text_search_btn)
        
        self.image_search_btn = self.create_styled_button("📷 Search Image", "#2196F3", "#1976D2")
        self.image_search_btn.clicked.connect(self.search_image)
        primary_layout.addWidget(self.image_search_btn)
        
        search_layout.addLayout(primary_layout)
        
        # Secondary search buttons
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(8)
        
        self.images_by_text_btn = self.create_styled_button("🖼️ Find Images", "#FF9800", "#F57C00", small=True)
        self.images_by_text_btn.clicked.connect(self.search_images_by_text)
        secondary_layout.addWidget(self.images_by_text_btn)
        
        self.translate_btn = self.create_styled_button("🌐 Translate", "#9C27B0", "#7B1FA2", small=True)
        self.translate_btn.clicked.connect(self.translate_text)
        secondary_layout.addWidget(self.translate_btn)
        
        search_layout.addLayout(secondary_layout)
        
        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)

    def create_features_section(self, layout):
        """Create additional features section"""
        features_frame = QFrame()
        features_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        features_layout = QVBoxLayout()
        features_layout.setContentsMargins(10, 10, 10, 10)
        
        # Section label
        features_label = QLabel("⚡ Quick Actions")
        features_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        features_label.setStyleSheet("color: #333; margin-bottom: 8px;")
        features_layout.addWidget(features_label)
        
        # Feature buttons
        features_button_layout = QHBoxLayout()
        features_button_layout.setSpacing(6)
        
        self.copy_btn = self.create_styled_button("📋 Copy", "#607D8B", "#546E7A", small=True)
        self.copy_btn.clicked.connect(self.copy_text)
        features_button_layout.addWidget(self.copy_btn)
        
        self.save_btn = self.create_styled_button("💾 Save", "#795548", "#6D4C41", small=True)
        self.save_btn.clicked.connect(self.save_text)
        features_button_layout.addWidget(self.save_btn)
        
        self.clear_btn = self.create_styled_button("🧹 Clear", "#9E9E9E", "#757575", small=True)
        self.clear_btn.clicked.connect(self.clear_text)
        features_button_layout.addWidget(self.clear_btn)
        
        features_layout.addLayout(features_button_layout)
        
        features_frame.setLayout(features_layout)
        layout.addWidget(features_frame)

    def create_action_buttons(self, layout):
        """Create action buttons"""
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        new_capture_btn = self.create_styled_button("🎯 New Capture", "#607D8B", "#546E7A")
        new_capture_btn.clicked.connect(self.new_capture)
        action_layout.addWidget(new_capture_btn)
        
        close_btn = self.create_styled_button("❌ Close", "#F44336", "#D32F2F")
        close_btn.clicked.connect(self.hide_panel)
        action_layout.addWidget(close_btn)
        
        layout.addLayout(action_layout)

    def create_styled_button(self, text, color1, color2, small=False):
        """Create a styled button with gradient background"""
        button = QPushButton(text)
        
        if small:
            button.setFont(QFont("Segoe UI", 9, QFont.Bold))
            button.setFixedHeight(35)
        else:
            button.setFont(QFont("Segoe UI", 10, QFont.Bold))
            button.setFixedHeight(40)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color1}, stop:1 {color2});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color2}, stop:1 {color1});
            }}
            QPushButton:pressed {{
                background: {color2};
            }}
            QPushButton:disabled {{
                background: #CCCCCC;
                color: #666666;
            }}
        """)
        
        return button

    def apply_styling(self):
        """Apply overall window styling"""
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 3px solid #667eea;
                border-radius: 15px;
            }
        """)

    def set_enhanced_content(self, text: str, image=None, search_manager=None, confidence=0.0, engine='google'):
        """Set enhanced content with all the new features"""
        self.text_edit.setPlainText(text)
        self.current_image = image
        self.search_manager = search_manager
        self.confidence = confidence
        self.current_engine = engine
        self.last_search_text = text
        
        # Update confidence display
        self.update_confidence_display(confidence)
        
        # Update engine display
        self.engine_label.setText(f"Engine: {engine.title()}")
        
        # Enable/disable buttons based on content
        self.update_button_states()
        
        # Update character count
        self.update_char_count()

    def update_confidence_display(self, confidence):
        """Update confidence display with color coding"""
        if confidence > 0:
            confidence_text = f"Confidence: {confidence:.1%}"
            if confidence > 0.8:
                confidence_color = "#4CAF50"  # Green
                confidence_icon = "🟢"
            elif confidence > 0.6:
                confidence_color = "#FF9800"  # Orange  
                confidence_icon = "🟡"
            else:
                confidence_color = "#F44336"  # Red
                confidence_icon = "🔴"
            
            self.confidence_label.setText(f"{confidence_icon} {confidence_text}")
            self.confidence_label.setStyleSheet(f"color: {confidence_color}; font-weight: bold;")
        else:
            self.confidence_label.setText("Confidence: --")
            self.confidence_label.setStyleSheet("color: #E8EAF6; font-weight: bold;")

    def update_button_states(self):
        """Update button enabled/disabled states"""
        text = self.text_edit.toPlainText().strip()
        has_text = bool(text)
        has_image = self.current_image is not None
        
        self.text_search_btn.setEnabled(has_text)
        self.images_by_text_btn.setEnabled(has_text)
        self.translate_btn.setEnabled(has_text)
        self.copy_btn.setEnabled(has_text)
        self.save_btn.setEnabled(has_text)
        self.image_search_btn.setEnabled(has_image)

    def update_char_count(self):
        """Update character count display"""
        text = self.text_edit.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        
        self.char_count_label.setText(f"{char_count} characters • {word_count} words")
        
        # Update button states when text changes
        self.update_button_states()

    # Search Methods
    def search_text(self):
        """Enhanced text search"""
        text = self.text_edit.toPlainText().strip()
        if self.search_manager and text:
            try:
                result = self.search_manager.search_text(text)
                if result:
                    self.show_feedback("🔍 Search opened in browser!", success=True)
                    print(f"[INFO] Text search: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                else:
                    self.show_feedback("❌ Search failed", success=False)
            except Exception as e:
                print(f"[ERROR] Search failed: {e}")
                self.show_feedback("❌ Search error", success=False)

    def search_images_by_text(self):
        """Search for images using text"""
        text = self.text_edit.toPlainText().strip()
        if self.search_manager and text:
            try:
                if hasattr(self.search_manager, 'search_images_by_text'):
                    result = self.search_manager.search_images_by_text(text)
                else:
                    # Fallback to regular image search
                    result = self.search_manager.search_text(f"{text} images")
                
                if result:
                    self.show_feedback("🖼️ Image search opened!", success=True)
                else:
                    self.show_feedback("❌ Image search failed", success=False)
            except Exception as e:
                print(f"[ERROR] Image search failed: {e}")
                self.show_feedback("❌ Image search error", success=False)

    def search_image(self):
        """Enhanced reverse image search"""
        if self.search_manager and self.current_image:
            try:
                if self.image_search_handler and self.image_processor:
                    # Enhanced image processing
                    enhanced_image = self.image_processor.enhance_for_search(self.current_image)
                    image_bytes, temp_path = self.image_search_handler.prepare_image_for_search(enhanced_image)
                    result = self.search_manager.search_image(image_data=image_bytes)
                    self.image_search_handler.cleanup_temp_files()
                else:
                    # Basic image search
                    result = self.search_manager.search_image()
                
                if result:
                    self.show_feedback("📷 Reverse image search opened!", success=True)
                else:
                    self.show_feedback("❌ Image search failed", success=False)
                    
            except Exception as e:
                print(f"[ERROR] Image search error: {e}")
                self.show_feedback("❌ Image search error", success=False)

    def translate_text(self):
        """Translate text using Google Translate"""
        text = self.text_edit.toPlainText().strip()
        if text:
            try:
                import urllib.parse
                encoded_text = urllib.parse.quote_plus(text)
                translate_url = f"https://translate.google.com/?sl=auto&tl=en&text={encoded_text}"
                webbrowser.open(translate_url)
                self.show_feedback("🌐 Google Translate opened!", success=True)
            except Exception as e:
                print(f"[ERROR] Translate failed: {e}")
                self.show_feedback("❌ Translate error", success=False)

    # Utility Methods
    def copy_text(self):
        """Copy text to clipboard with enhanced feedback"""
        text = self.text_edit.toPlainText().strip()
        if text:
            try:
                # Try pyperclip first
                pyperclip.copy(text)
                self.show_feedback("📋 Text copied to clipboard!", success=True)
                print(f"[INFO] Copied to clipboard: {len(text)} characters")
            except ImportError:
                # Fallback to Qt clipboard
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                self.show_feedback("📋 Text copied to clipboard!", success=True)
            except Exception as e:
                print(f"[ERROR] Copy failed: {e}")
                self.show_feedback("❌ Copy failed", success=False)

    def save_text(self):
        """Save text to file"""
        text = self.text_edit.toPlainText().strip()
        if text:
            try:
                from datetime import datetime
                filename = f"circle_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                # Save to desktop
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                filepath = os.path.join(desktop, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Circle to Search Results\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Confidence: {self.confidence:.1%}\n")
                    f.write(f"Engine: {self.current_engine}\n")
                    f.write(f"\n--- Recognized Text ---\n")
                    f.write(text)
                
                self.show_feedback(f"💾 Saved as {filename}!", success=True)
                print(f"[INFO] Text saved to: {filepath}")
                
            except Exception as e:
                print(f"[ERROR] Save failed: {e}")
                self.show_feedback("❌ Save failed", success=False)

    def clear_text(self):
        """Clear the text editor"""
        self.text_edit.clear()
        self.show_feedback("🧹 Text cleared", success=True)

    def new_capture(self):
        """Start a new capture"""
        self.hide_panel()
        # Signal to start new capture
        QTimer.singleShot(300, self.trigger_new_capture)

    def trigger_new_capture(self):
        """Trigger new capture - to be connected to main app"""
        print("[INFO] New capture requested")
        # This would be connected to the main app's capture function

    def show_feedback(self, message, success=True):
        """Show enhanced feedback with better visual indication"""
        original_title = self.windowTitle()
        
        if success:
            self.setWindowTitle(f"✅ {message}")
            # Brief highlight effect could be added here
        else:
            self.setWindowTitle(f"❌ {message}")
        
        # Reset title after 3 seconds
        QTimer.singleShot(3000, lambda: self.setWindowTitle(original_title))

    def show_panel(self, relative_rect=None):
        """Show the panel with enhanced positioning"""
        if relative_rect:
            # Smart positioning
            screen = QGuiApplication.primaryScreen().geometry()
            
            # Try to position to the right first
            panel_x = relative_rect.right() + 15
            panel_y = max(0, relative_rect.top())
            
            # If it goes off screen, try left side
            if panel_x + self.width() > screen.width():
                panel_x = max(0, relative_rect.left() - self.width() - 15)
            
            # Ensure it fits vertically
            if panel_y + self.height() > screen.height():
                panel_y = max(0, screen.height() - self.height())
            
            self.move(panel_x, panel_y)
        
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_panel(self):
        """Hide the panel"""
        self.hide()

# Alias for backward compatibility
SidePanelWindow = EnhancedSidePanelWindow