# Enhanced Overlay for Circle to Search
# Version 2.0 - Better visual feedback and user experience

import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, 
    QCursor, QPainterPath, QLinearGradient, QGuiApplication
)

class EnhancedOverlayWindow(QWidget):
    """Enhanced overlay with better visual feedback and animations"""
    
    region_selected = Signal(QRect)

    def __init__(self):
        super().__init__()
        
        # Selection state
        self.selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selection_rect = QRect()
        
        # Visual enhancements
        self.animation_opacity = 0.0
        self.crosshair_visible = True
        self.grid_visible = False
        
        # Timers for animations
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_crosshair)
        
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.update_fade)
        
        # Animation properties
        self.fade_direction = 1
        self.fade_step = 0.05
        
        self.init_ui()

    def init_ui(self):
        """Initialize the enhanced overlay UI"""
        # Make the overlay cover all screens
        screen = QGuiApplication.primaryScreen()
        total_geometry = screen.virtualGeometry()
        
        self.setGeometry(total_geometry)
        
        # Window properties
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        
        # Make background transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Set cursor
        self.setCursor(QCursor(Qt.CrossCursor))

    def show_overlay(self):
        """Show overlay with enhanced effects"""
        print("[DEBUG] Showing enhanced overlay...")
        
        # Reset state
        self.selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selection_rect = QRect()
        
        # Remove transparent input flag to enable interaction
        self.setWindowFlag(Qt.WindowTransparentForInput, False)
        
        # Show and animate
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Start animations
        self.start_animations()
        
        # Set focus
        self.setFocus()
        self.grabKeyboard()
        self.grabMouse()

    def start_animations(self):
        """Start visual animations"""
        # Start crosshair blinking
        self.blink_timer.start(800)  # Blink every 800ms
        
        # Start fade animation
        self.animation_opacity = 0.0
        self.fade_direction = 1
        self.fade_timer.start(50)  # Update every 50ms

    def stop_animations(self):
        """Stop all animations"""
        self.blink_timer.stop()
        self.fade_timer.stop()

    def toggle_crosshair(self):
        """Toggle crosshair visibility for blinking effect"""
        self.crosshair_visible = not self.crosshair_visible
        self.update()

    def update_fade(self):
        """Update fade animation"""
        self.animation_opacity += self.fade_step * self.fade_direction
        
        if self.animation_opacity >= 1.0:
            self.animation_opacity = 1.0
            self.fade_direction = -1
        elif self.animation_opacity <= 0.3:
            self.animation_opacity = 0.3
            self.fade_direction = 1
        
        self.update()

    def hide_overlay(self):
        """Hide overlay with cleanup"""
        self.stop_animations()
        
        # Release mouse and keyboard
        self.releaseMouse()
        self.releaseKeyboard()
        
        # Hide
        self.hide()
        
        # Re-enable transparent input
        self.setWindowFlag(Qt.WindowTransparentForInput, True)

    def mousePressEvent(self, event):
        """Enhanced mouse press handling"""
        if event.button() == Qt.LeftButton:
            self.selecting = True
            self.start_point = event.globalPos()
            self.end_point = self.start_point
            self.selection_rect = QRect()
            
            # Stop blinking during selection
            self.blink_timer.stop()
            self.crosshair_visible = True
            
            print(f"[DEBUG] Selection started at: {self.start_point}")
            self.update()

    def mouseMoveEvent(self, event):
        """Enhanced mouse move handling with live preview"""
        if self.selecting:
            self.end_point = event.globalPos()
            
            # Create selection rectangle
            self.selection_rect = QRect(
                min(self.start_point.x(), self.end_point.x()),
                min(self.start_point.y(), self.end_point.y()),
                abs(self.end_point.x() - self.start_point.x()),
                abs(self.end_point.y() - self.start_point.y())
            )
            
            self.update()

    def mouseReleaseEvent(self, event):
        """Enhanced mouse release handling"""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            
            # Minimum selection size check
            min_size = 10
            if (self.selection_rect.width() >= min_size and 
                self.selection_rect.height() >= min_size):
                
                print(f"[DEBUG] Valid selection: {self.selection_rect}")
                
                # Convert global coordinates to local screen coordinates
                local_rect = QRect(
                    self.selection_rect.x() - self.geometry().x(),
                    self.selection_rect.y() - self.geometry().y(),
                    self.selection_rect.width(),
                    self.selection_rect.height()
                )
                
                # Emit signal with local coordinates
                self.region_selected.emit(local_rect)
                
                # Hide overlay after short delay to show selection feedback
                QTimer.singleShot(200, self.hide_overlay)
            else:
                print("[DEBUG] Selection too small, ignoring")
                self.selection_rect = QRect()
                self.update()
                
                # Restart blinking
                self.blink_timer.start(800)

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key_Escape:
            print("[DEBUG] Escape pressed, hiding overlay")
            self.hide_overlay()
        elif event.key() == Qt.Key_G:
            # Toggle grid
            self.grid_visible = not self.grid_visible
            self.update()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        """Enhanced paint event with better visuals"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background with semi-transparent overlay
        overlay_color = QColor(0, 0, 0, int(60 * self.animation_opacity))
        painter.fillRect(self.rect(), overlay_color)
        
        # Draw grid if enabled
        if self.grid_visible:
            self.draw_grid(painter)
        
        # Draw crosshair if visible and not selecting
        if self.crosshair_visible and not self.selecting:
            self.draw_crosshair(painter)
        
        # Draw selection rectangle
        if self.selecting and not self.selection_rect.isEmpty():
            self.draw_selection(painter)
        
        # Draw instructions
        self.draw_instructions(painter)

    def draw_grid(self, painter):
        """Draw helpful grid lines"""
        pen = QPen(QColor(255, 255, 255, 30))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Draw grid every 50 pixels
        grid_size = 50
        
        # Vertical lines
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        
        # Horizontal lines
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)

    def draw_crosshair(self, painter):
        """Draw animated crosshair at cursor position"""
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        
        # Crosshair properties
        crosshair_size = 20
        opacity = int(255 * self.animation_opacity)
        
        # Create gradient pen
        pen = QPen(QColor(255, 255, 255, opacity))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw crosshair
        painter.drawLine(
            cursor_pos.x() - crosshair_size, cursor_pos.y(),
            cursor_pos.x() + crosshair_size, cursor_pos.y()
        )
        painter.drawLine(
            cursor_pos.x(), cursor_pos.y() - crosshair_size,
            cursor_pos.x(), cursor_pos.y() + crosshair_size
        )
        
        # Draw center dot
        center_pen = QPen(QColor(255, 100, 100, opacity))
        center_pen.setWidth(4)
        painter.setPen(center_pen)
        painter.drawPoint(cursor_pos)

    def draw_selection(self, painter):
        """Draw enhanced selection rectangle"""
        if self.selection_rect.isEmpty():
            return
        
        # Convert to local coordinates
        local_rect = QRect(
            self.selection_rect.x() - self.geometry().x(),
            self.selection_rect.y() - self.geometry().y(),
            self.selection_rect.width(),
            self.selection_rect.height()
        )
        
        # Fill selection with semi-transparent blue
        fill_color = QColor(33, 150, 243, 40)
        painter.fillRect(local_rect, fill_color)
        
        # Draw selection border with gradient
        gradient = QLinearGradient(local_rect.topLeft(), local_rect.bottomRight())
        gradient.setColorAt(0, QColor(33, 150, 243, 255))
        gradient.setColorAt(1, QColor(21, 101, 192, 255))
        
        pen = QPen(QBrush(gradient), 3)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(local_rect)
        
        # Draw corner handles
        self.draw_corner_handles(painter, local_rect)
        
        # Draw size info
        self.draw_size_info(painter, local_rect)

    def draw_corner_handles(self, painter, rect):
        """Draw corner resize handles"""
        handle_size = 8
        handle_color = QColor(255, 255, 255, 200)
        
        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QBrush(handle_color))
        
        # Corner positions
        corners = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]
        
        for corner in corners:
            handle_rect = QRect(
                corner.x() - handle_size // 2,
                corner.y() - handle_size // 2,
                handle_size,
                handle_size
            )
            painter.drawEllipse(handle_rect)

    def draw_size_info(self, painter, rect):
        """Draw selection size information"""
        if rect.width() < 50 or rect.height() < 50:
            return
        
        # Prepare text
        size_text = f"{rect.width()} × {rect.height()}"
        
        # Font and metrics
        font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font)
        
        fm = painter.fontMetrics()
        text_rect = fm.boundingRect(size_text)
        
        # Position text in center of selection
        text_x = rect.center().x() - text_rect.width() // 2
        text_y = rect.center().y() + text_rect.height() // 2
        
        # Draw text background
        bg_rect = QRect(
            text_x - 8, text_y - text_rect.height() - 4,
            text_rect.width() + 16, text_rect.height() + 8
        )
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRoundedRect(bg_rect, 4, 4)
        
        # Draw text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(text_x, text_y, size_text)

    def draw_instructions(self, painter):
        """Draw helpful instructions"""
        if self.selecting:
            return
        
        instructions = [
            "🎯 Click and drag to select region",
            "⌨️ Press G to toggle grid",
            "🚫 Press Esc to cancel"
        ]
        
        # Font and properties
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255, 200)))
        
        # Draw instructions in top-left corner
        y_offset = 30
        for instruction in instructions:
            # Background for better readability
            fm = painter.fontMetrics()
            text_rect = fm.boundingRect(instruction)
            bg_rect = QRect(15, y_offset - text_rect.height(), 
                          text_rect.width() + 20, text_rect.height() + 10)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.drawRoundedRect(bg_rect, 5, 5)
            
            # Draw text
            painter.setPen(QPen(QColor(255, 255, 255, 200)))
            painter.drawText(25, y_offset, instruction)
            y_offset += 35

# Alias for backward compatibility
OverlayWindow = EnhancedOverlayWindow