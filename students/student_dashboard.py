from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QStackedWidget, 
                             QVBoxLayout, QLabel, QSizePolicy, QPushButton, QMessageBox, QSpacerItem)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QTimer
from PyQt5.QtGui import QIcon, QFont
import datetime
import sqlite3
from students.students_attendance import StudentAttendancePage
from students.student_settings import StudentSettingsPage
from students.student_home_page import StudentHomePage

class Sidebar(QWidget):
    def __init__(self, parent, stacked_widget, student_id):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(70)  # Start in collapsed mode
        
        self.stacked_widget = stacked_widget
        self.student_id = student_id
        self.expanded = False
        
        # Layout setup
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 10, 5, 10)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Define sidebar buttons
        self.buttons = [
            {"icon": "icons/home.png", "text": "📊 Dashboard", "index": 0},
            {"icon": "icons/attendance.png", "text": "✅ Attendance", "index": 1},
            {"icon": "icons/settings.png", "text": "⚙️ Settings", "index": 2},
        ]
        
        # Create and add buttons
        self.sidebar_buttons = {}
        for button_info in self.buttons:
            btn = self.create_sidebar_button(
                button_info["icon"], 
                button_info["text"], 
                lambda index=button_info["index"]: self.switch_page(index)
            )
            
            self.sidebar_buttons[button_info["index"]] = btn
            self.layout.addWidget(btn)
        
        # Add spacer to push logout to bottom
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Logout button
        logout_btn = self.create_sidebar_button(
            "icons/logout.png", 
            "🚪 Logout", 
            self.logout
        )
        self.sidebar_buttons[-1] = logout_btn
        self.layout.addWidget(logout_btn)
        
        self.setLayout(self.layout)
        
        # Setup animation
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(250)
        
        # Enable hover detection
        self.setMouseTracking(True)
    
    def logout(self):
        """Handle logout process."""
        reply = QMessageBox.question(
            self, 
            'Confirm Logout', 
            'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Log logout attempt
        self.log_activity('student_logout')
        
        def secure_logout():
            """Perform secure logout operations."""
            # Clear sensitive data from memory (if any)
            self.clear_sensitive_data()
            
            # Find the top-level StudentDashboard window
            parent_window = self
            while parent_window.parent() is not None:
                parent_window = parent_window.parent()
            
                      
            # Create and show login window
            from admin.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            
            # Close the current dashboard
            parent_window.close()
        
        # Use QTimer for delayed, secure logout
        QTimer.singleShot(100, secure_logout)

    def log_activity(self, activity_type):
        """Log user activities."""
        try:
            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO activity_log (user_id, activity_type, timestamp) 
                VALUES (?, ?, ?)
            """, (self.student_id, activity_type, timestamp))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging activity: {e}")

    def clear_sensitive_data(self):
        """Clear any sensitive data from memory."""
        # Reset or clear any sensitive class attributes
        print("Sensitive data cleared during logout")

    def create_sidebar_button(self, icon_path, label, callback):
        """Creates a sidebar button with an icon and text label."""
        button = QPushButton("")  # Start with no text
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
    
    def switch_page(self, index):
        """Switch to the specified page in the stacked widget."""
        self.stacked_widget.setCurrentIndex(index)
        
        # Update button active states
        for btn_index, button in self.sidebar_buttons.items():
            is_active = btn_index == index
            button.setProperty("active", is_active)
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

class StudentDashboard(QWidget):
    def __init__(self, student_id):
        super().__init__()

        self.setWindowTitle("Student Dashboard")
        self.setGeometry(100, 100, 1000, 700)

        # Main Layout
        main_layout = QHBoxLayout()

        # Create Stacked Widget for Content
        self.stacked_widget = QStackedWidget()

        # Create Dashboard Pages
        self.dashboard_page = StudentHomePage(student_id)
        self.attendance_page = StudentAttendancePage(student_id)
        self.settings_page = StudentSettingsPage(student_id)

        # Setup Individual Pages
        self.setup_dashboard_page()
        self.setup_attendance_page()
        self.setup_settings_page()

        # Add Pages to Stacked Widget
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.attendance_page)
        self.stacked_widget.addWidget(self.settings_page)

        # Create Sidebar (pass stacked widget for navigation)
        self.sidebar = Sidebar(self, self.stacked_widget, student_id)

        # Add Sidebar and Stacked Widget to Main Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setLayout(main_layout)

    def setup_dashboard_page(self):
        layout = QVBoxLayout()
        title = QLabel("📊 Student Dashboard")
        title.setFont(QFont('Arial', 16))
        layout.addWidget(title)
        layout.addWidget(QLabel("Welcome to your personalized student dashboard"))
        self.dashboard_page.setLayout(layout)

    def setup_attendance_page(self):
        layout = QVBoxLayout()
        title = QLabel("✅ Attendance Records")
        title.setFont(QFont('Arial', 16))
        layout.addWidget(title)
        layout.addWidget(QLabel("View and track your class attendance"))
        self.attendance_page.setLayout(layout)

    def setup_settings_page(self):
        layout = QVBoxLayout()
        title = QLabel("⚙️ Settings")
        title.setFont(QFont('Arial', 16))
        layout.addWidget(title)
        layout.addWidget(QLabel("Customize your dashboard preferences"))
        self.settings_page.setLayout(layout)


