from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
import math

class LoadingSpinner(QWidget):
    """Custom animated loading spinner widget"""
    def __init__(self, parent=None, size=64, num_dots=8, dot_size=10, color=QColor(255, 255, 255)):
        super().__init__(parent)
        
        # Configuration
        self.setFixedSize(size, size)
        self.num_dots = num_dots
        self.dot_size = dot_size
        self.color = color
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Animation setup
        self._counter = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._speed = 80  # milliseconds per frame
        
        # Set up the animation
        self.start_animation()
    
    def start_animation(self):
        """Start the spinner animation"""
        if not self._timer.isActive():
            self._timer.start(self._speed)
            self.show()
    
    def stop_animation(self):
        """Stop the spinner animation"""
        if self._timer.isActive():
            self._timer.stop()
    
    def _rotate(self):
        """Update rotation counter and trigger repaint"""
        self._counter = (self._counter + 1) % self.num_dots
        self.update()
    
    def paintEvent(self, event):
        """Draw the spinner with fading dots"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = (min(width, height) - self.dot_size) / 2
        
        # Calculate position for each dot
        for i in range(self.num_dots):
            # Calculate alpha based on distance from current counter
            distance = (i - self._counter) % self.num_dots
            alpha = 255 - (distance * (255 // self.num_dots))
            
            # Set color with calculated alpha
            dot_color = QColor(self.color)
            dot_color.setAlpha(max(alpha, 30))  # Minimum alpha of 30 for visibility
            
            # Calculate dot position on the circle
            angle = 2 * 3.14159 * i / self.num_dots
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Draw the dot
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(QRectF(x - self.dot_size/2, y - self.dot_size/2, self.dot_size, self.dot_size))


class ThemeTransitionOverlay(QWidget):
    """Overlay with progress animation for theme transitions that works well in both light and dark modes"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ThemeTransitionOverlay")
        
        # Use a fixed size for the overlay
        self.setFixedSize(400, 250)
        
        # Center it within the parent
        if parent:
            self.move(
                (parent.width() - self.width()) // 2,
                (parent.height() - self.height()) // 2
            )
        
        # Set up the overlay appearance with adaptive styling
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Create animated spinner widget with theme-aware colors
        self.spinner = self.create_theme_aware_spinner()
        spinner_container = QWidget()
        spinner_layout = QHBoxLayout(spinner_container)
        spinner_layout.setAlignment(Qt.AlignCenter)
        spinner_layout.addWidget(self.spinner)
        
        # Create message labels
        self.message_label = QLabel("Applying Theme...")
        self.message_label.setObjectName("MessageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        
        self.sub_message_label = QLabel("Please wait while we update the interface")
        self.sub_message_label.setObjectName("SubMessageLabel")
        self.sub_message_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(spinner_container)
        layout.addWidget(self.message_label)
        layout.addWidget(self.sub_message_label)
        
        # Fade in animation setup
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Initially hide
        self.hide()
        
        # Update styles based on current theme
        self.update_theme_styles()
    
    def create_theme_aware_spinner(self):
        """Creates a spinner that will be visible in both light and dark themes"""
        # Default to a color that will work in both themes
        theme_manager = QApplication.instance().property("theme_manager")
        is_dark = theme_manager and theme_manager.get_current_theme_name() == "dark"
        
        # Choose appropriate colors based on theme
        if is_dark:
            spinner_color = QColor(255, 255, 255)  # White for dark theme
            self.background_color = QColor(40, 44, 52, 220)  # Dark background with alpha
            self.text_color = QColor(255, 255, 255)  # White text
            self.subtext_color = QColor(200, 200, 200)  # Light gray subtext
        else:
            spinner_color = QColor(52, 152, 219)  # Blue for light theme (#3498db)
            self.background_color = QColor(255, 255, 255, 240)  # Light background with alpha
            self.text_color = QColor(44, 62, 80)  # Dark text (#2c3e50)
            self.subtext_color = QColor(127, 140, 141)  # Gray subtext (#7f8c8d)
        
        return LoadingSpinner(self, size=80, num_dots=10, dot_size=8, color=spinner_color)
    
    def update_theme_styles(self):
        """Updates styling based on the current theme"""
        theme_manager = QApplication.instance().property("theme_manager")
        is_dark = theme_manager and theme_manager.get_current_theme_name() == "dark"
        
        if is_dark:
            self.setStyleSheet("""
                QWidget#ThemeTransitionOverlay {
                    background-color: rgba(40, 44, 52, 220);
                    border: 1px solid rgba(255, 255, 255, 30);
                    border-radius: 15px;
                }
                QLabel#MessageLabel {
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }
                QLabel#SubMessageLabel {
                    color: rgba(200, 200, 200, 200);
                    font-size: 14px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget#ThemeTransitionOverlay {
                    background-color: rgba(255, 255, 255, 240);
                    border: 1px solid rgba(0, 0, 0, 30);
                    border-radius: 15px;
                }
                QLabel#MessageLabel {
                    color: #2c3e50;
                    font-size: 18px;
                    font-weight: bold;
                }
                QLabel#SubMessageLabel {
                    color: #7f8c8d;
                    font-size: 14px;
                }
            """)
    
    def paintEvent(self, event):
        """Custom paint event to draw shadow and border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 15, 15)
        
        # Draw shadow (only in light mode)
        theme_manager = QApplication.instance().property("theme_manager")
        is_dark = theme_manager and theme_manager.get_current_theme_name() == "dark"
        
        if not is_dark:
            shadow_color = QColor(0, 0, 0, 30)
            for i in range(10):
                painter.setPen(Qt.NoPen)
                shadow_path = QPainterPath()
                shadow_path.addRoundedRect(QRectF(10-i, 10-i, self.width()-20+i*2, self.height()-20+i*2), 15, 15)
                shadow_color.setAlpha(max(30 - i*3, 0))
                painter.setBrush(QBrush(shadow_color))
                painter.drawPath(shadow_path)
        
        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.background_color))
        painter.drawPath(path)
        
        # Draw border
        border_color = QColor(255, 255, 255, 30) if is_dark else QColor(0, 0, 0, 30)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
    
    def showEvent(self, event):
        """Start animations when overlay is shown"""
        super().showEvent(event)
        # Update theme styles before showing
        self.update_theme_styles()
        # Start animations
        self.opacity_anim.start()
        self.spinner.start_animation()
    
    def show_with_message(self, message=None, sub_message=None):
        """Show overlay with custom message"""
        if message:
            self.message_label.setText(message)
        if sub_message:
            self.sub_message_label.setText(sub_message)
        self.show()
    
    def hideEvent(self, event):
        """Stop animations when overlay is hidden"""
        self.spinner.stop_animation()
        super().hideEvent(event)