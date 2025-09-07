# file: popover.py

import os
import sys
import json
import webbrowser

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QUrl, QObject, Slot, Property
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel

class Bridge(QObject):
    """Bridge for communication between Python and JavaScript in the popover."""
    @Slot(str)
    def onCopy(self, text):
        print(f"JS requested to copy text: {text[:30]}...")
        QApplication.clipboard().setText(text)

    @Slot(str)
    def onSearch(self, text):
        print(f"JS requested to search for: {text[:30]}...")
        url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
        webbrowser.open(url)

class PopoverWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool | # Don't show in taskbar
            Qt.WindowDoesNotAcceptFocus # Prevents stealing focus initially
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(350, 200)

        # WebEngine View
        self.web_view = QWebEngineView(self)
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        self.web_view.setGeometry(self.rect())
        
        # Setup WebChannel for Python-JS communication
        self.bridge = Bridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Load the HTML file
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "popover.html")
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(ui_path)))
    
    def set_text(self, text):
        """Sets the text in the popover's text area."""
        # We must escape the text to handle newlines, quotes, etc. in JS
        js_escaped_text = json.dumps(text)
        js_code = f"updateText({js_escaped_text});"
        self.web_view.page().runJavaScript(js_code)

    def show_at(self, position):
        """Shows the popover at the specified QPoint."""
        self.move(position)
        self.show()
        self.activateWindow() # Now we want it to have focus
        self.raise_()

    def focusOutEvent(self, event):
        """Hide the popover when it loses focus."""
        self.hide()