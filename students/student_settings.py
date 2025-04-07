import sqlite3
import hashlib
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox, QCheckBox, QGroupBox, QFormLayout, QScrollArea, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from config.utils_constants import DATABASE_PATH

class StudentSettingsPage(QWidget):
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        
        # Get theme manager
        self.theme_manager = QApplication.instance().property("theme_manager")
        
        # Setup UI
        self.init_ui()
        
        # Load initial settings
        self.load_initial_settings()
    
    def init_ui(self):
        """Initialize the user interface for student settings."""
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Scroll Area for Settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Scroll Content Widget
        scroll_content = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content)
        scroll_content_layout.setSpacing(15)
        
        # Title
        title = QLabel("⚙️ Student Settings")
        title.setFont(QFont('Arial', 16))
        title.setAlignment(Qt.AlignLeft)
        scroll_content_layout.addWidget(title)
        
        # Create settings sections
        scroll_content_layout.addWidget(self._create_profile_section())
        scroll_content_layout.addWidget(self._create_security_section())
        scroll_content_layout.addWidget(self._create_preferences_section())
        scroll_content_layout.addWidget(self._create_notifications_section())
        
        # Add stretch to push everything to the top
        scroll_content_layout.addStretch(1)
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Window properties
        self.setWindowTitle("Student Settings")
        self.resize(500, 600)
    
    def _create_profile_section(self):
        """Create profile information section."""
        profile_group = QGroupBox("👤 Profile Information")
        profile_layout = QFormLayout()
        profile_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.name_label = QLabel()
        self.id_label = QLabel(str(self.student_id))
        
        profile_layout.addRow("Name:", self.name_label)
        profile_layout.addRow("Student ID:", self.id_label)
        
        profile_group.setLayout(profile_layout)
        return profile_group
    
    def _create_security_section(self):
        """Create account security section."""
        security_group = QGroupBox("🔐 Account Security")
        security_layout = QVBoxLayout()
        
        # Password change form
        change_password_layout = QFormLayout()
        change_password_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        
        change_password_layout.addRow("Current Password:", self.current_password)
        change_password_layout.addRow("New Password:", self.new_password)
        change_password_layout.addRow("Confirm New Password:", self.confirm_password)
        
        change_password_btn = QPushButton("Change Password")
        change_password_btn.clicked.connect(self.change_password)
        
        security_layout.addLayout(change_password_layout)
        security_layout.addWidget(change_password_btn)
        
        security_group.setLayout(security_layout)
        return security_group
    
    def _create_preferences_section(self):
        """Create user preferences section."""
        preferences_group = QGroupBox("🎨 Preferences")
        preferences_layout = QVBoxLayout()
        
        # Dark Mode Toggle
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        preferences_layout.addWidget(self.dark_mode_checkbox)
        
        preferences_group.setLayout(preferences_layout)
        return preferences_group
    
    def _create_notifications_section(self):
        """Create notifications preferences section."""
        notifications_group = QGroupBox("🔔 Notification Preferences")
        notifications_layout = QVBoxLayout()
        
        # Email Notification Checkbox
        self.email_notify_checkbox = QCheckBox("Receive Email Notifications")
        notifications_layout.addWidget(self.email_notify_checkbox)
        
        # SMS Notification Checkbox
        self.sms_notify_checkbox = QCheckBox("Receive SMS Notifications")
        notifications_layout.addWidget(self.sms_notify_checkbox)
        
        notifications_group.setLayout(notifications_layout)
        return notifications_group
        
    def load_initial_settings(self):
        """Load student's initial settings and profile information."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Fetch student name
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (self.student_id,))
            name_result = cursor.fetchone()
            if name_result:
                self.name_label.setText(name_result[0])
            
            # Fetch dark mode setting
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'dark_mode'")
            dark_mode_result = cursor.fetchone()
            if dark_mode_result:
                self.dark_mode_checkbox.setChecked(dark_mode_result[0] == "1")
            
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Settings Error", f"Could not load settings: {e}")
    
    def change_password(self):
        """Handle secure password change process."""
        current_pwd = self.current_password.text().strip()
        new_pwd = self.new_password.text().strip()
        confirm_pwd = self.confirm_password.text().strip()
        
        # Comprehensive validation
        if not all([current_pwd, new_pwd, confirm_pwd]):
            QMessageBox.warning(self, "Password Change", "Please fill in all password fields.")
            return
        
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "Password Change", "New passwords do not match.")
            return
        
        if len(new_pwd) < 8:
            QMessageBox.warning(self, "Password Change", "New password must be at least 8 characters long.")
            return
        
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Hash passwords using SHA-256
            hashed_current = hashlib.sha256(current_pwd.encode()).hexdigest()
            hashed_new = hashlib.sha256(new_pwd.encode()).hexdigest()
            
            # Verify current password
            cursor.execute("SELECT password FROM students WHERE student_id = ?", (self.student_id,))
            stored_password = cursor.fetchone()[0]
            
            if stored_password != hashed_current:
                QMessageBox.warning(self, "Password Change", "Current password is incorrect.")
                conn.close()
                return
            
            # Update password
            cursor.execute("UPDATE students SET password = ? WHERE student_id = ?", 
                           (hashed_new, self.student_id))
            conn.commit()
            conn.close()
            
            # Clear password fields
            self.current_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()
            
            QMessageBox.information(self, "Password Change", "Password successfully updated!")
        
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {str(e)}")
    
    def toggle_dark_mode(self, state):
        """Toggle dark mode setting."""
        try:
            # Use theme manager if available
            if self.theme_manager:
                # Trigger theme change
                self.theme_manager.load_theme("dark" if state == 2 else "light")
            
            # Update database setting
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value) 
                VALUES ('dark_mode', ?)
            """, (str(int(state == 2)),))  # 2 means checked
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Dark Mode", 
                "Dark mode setting updated successfully.")
        
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Settings Error", f"Could not update dark mode: {e}")