from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QApplication, QSizePolicy
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation
from PyQt5.QtGui import QIcon

class Sidebar(QWidget):
    def __init__(self, parent, content_area):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(70)  # Start in collapsed mode

        # Apply stylesheet from global application stylesheet
        self.setStyleSheet(QApplication.instance().styleSheet())  
        
        self.parent = parent
        self.content_area = content_area  # Reference to stacked content area
        self.expanded = False  # Track sidebar state
        
        # Layout setup
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 10, 5, 10)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Define sidebar buttons with consistent structure
        self.buttons = [
            {"icon": "icons/home.png", "text": "🏠 Home", "target": "home"},
            {"icon": "icons/register.png", "text": "📌 Register", "target": "register"},
            {"icon": "icons/attendance.png", "text": "📋 Attendance", "target": "attendance"},
            {"icon": "icons/start.png", "text": "📡 Start", "target": "start_attendance"},
            {"icon": "icons/unknown.png", "text": "❓ Unknown", "target": "review_unknown"},
            {"icon": "icons/settings.png", "text": "⚙ Settings", "target": "settings"},
            {"icon": "icons/resources.png", "text": "Manage Academic Resources", "target": "academic_resource_manager"}
        ]
        
        # Create and add buttons
        self.sidebar_buttons = {}
        for button_info in self.buttons:
            btn = self.create_sidebar_button(
                button_info["icon"], 
                button_info["text"], 
                lambda target=button_info["target"]: parent.switch_window(target)
            )
            self.sidebar_buttons[button_info["target"]] = btn
            self.layout.addWidget(btn)
        
        self.setLayout(self.layout)
        
        # Setup animation
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(250)  # Slightly faster for better UX
        
        # Enable hover detection
        self.setMouseTracking(True)
    
    def create_sidebar_button(self, icon_path, label, callback):
        """Creates a sidebar button with an icon and text label."""
        button = QPushButton("")  # Start with no text, will update on expand
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(28, 28))
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(65)
        button.clicked.connect(lambda: self.on_button_click(callback, label))
        
        # Store the full label as a property
        button.setProperty("fullLabel", label)
        
        return button
    
    def on_button_click(self, callback, label):
        """Handles button clicks with logging and callback execution."""
        print(f"✅ Sidebar button clicked: {label}")
        callback()
    
    def set_active_window(self, window_name):
        """Updates the active button based on current window."""
        for target, button in self.sidebar_buttons.items():
            is_active = target == window_name
            button.setProperty("active", is_active)
            # Force style refresh
            button.style().unpolish(button)
            button.style().polish(button)
    
    def enterEvent(self, event):
        """Expand the sidebar on hover"""
        self.animation.stop()
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(200)  # Expanded width
        self.animation.start()
        self.update_button_text(True)
    
    def leaveEvent(self, event):
        """Collapse the sidebar when not hovered"""
        self.animation.stop()
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(70)  # Collapsed width
        self.animation.start()
        self.update_button_text(False)
    
    def update_button_text(self, expanded):
        """Updates button text visibility based on sidebar state."""
        for btn in self.sidebar_buttons.values():
            btn.setText("" if not expanded else btn.property("fullLabel"))