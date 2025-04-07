from PyQt5.QtWidgets import QMainWindow, QLabel, QLineEdit, QInputDialog, QPushButton, QVBoxLayout, QApplication, QWidget, QMessageBox, QFrame, QCheckBox
from PyQt5.QtCore import Qt , QTimer
from PyQt5.QtGui import QFont
from config.utils_constants import DATABASE_PATH
from admin.login_attempt_tracker import LoginAttemptTracker
from students.student_dashboard import StudentDashboard
import time
import sqlite3
import hashlib
import bcrypt

def get_dark_mode_setting():
    """Fetches dark mode setting from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'dark_mode'")
    result = cursor.fetchone()
    conn.close()
    return result[0] == "1" if result else False

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Login")
        self.setFixedSize(400, 350)  # ✅ Set a modern, non-resizable window

        self.login_attempt_tracker=LoginAttemptTracker()

        self.setStyleSheet(QApplication.instance().styleSheet())  # ✅ Inherit global QSS

        self.dark_mode_enabled = get_dark_mode_setting()

        # Central Widget & Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)

        # Container Frame
        container = QFrame(self)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        container_layout.setAlignment(Qt.AlignCenter)

        # Title Label
        title_label = QLabel("AI Attendance System Login", self)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)

        # Username Field
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("👤Enter Student ID")
        self.username_input.setFont(QFont("Arial", 12))
        container_layout.addWidget(self.username_input)

        # Password Field
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("🔑 Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Arial", 12))
        container_layout.addWidget(self.password_input)

        self.show_password_checkbox = QCheckBox("Show Password")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        container_layout.addWidget(self.show_password_checkbox)

        # Login Button
        self.login_button = QPushButton("Login", self)
        self.login_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.authenticate)  # ✅ Connect to authentication method
        container_layout.addWidget(self.login_button)


        # Add Container to Main Layout
        main_layout.addWidget(container)

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def authenticate(self):
        """Enhanced authentication with persistent login attempt tracking."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Input validation
        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return

        # Check for lockout
        if self.login_attempt_tracker.is_locked_out(username):
            remaining_time = self.login_attempt_tracker.get_remaining_lockout_time(username)
            QMessageBox.warning(self, "Account Locked", 
                f"Too many failed attempts. Please wait {remaining_time} seconds before trying again.")
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Admin authentication
            cursor.execute("SELECT password FROM admin WHERE username = ?", (username,))
            admin_result = cursor.fetchone()

            if admin_result:
                stored_hash = admin_result[0]
                # Check if password matches using bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    self.open_admin_dashboard()
                    self.login_attempt_tracker.reset_attempts(username)
                    return
                else:
                    self.handle_failed_login(username)
                    return
            # Student authentication
            cursor.execute("SELECT password FROM students WHERE student_id = ?", (username,))
            student_result = cursor.fetchone()

            if student_result:
                stored_password = student_result[0]

                if not stored_password:  # First-time login handling
                    self.prompt_password_change(username)
                    self.login_attempt_tracker.reset_attempts(username)
                elif stored_password == hashed_input:
                    self.open_student_dashboard(username)
                    self.login_attempt_tracker.reset_attempts(username)
                    self.close()
                else:
                    self.handle_failed_login(username)
            else:
                QMessageBox.warning(self, "Login Failed", "User not found.")
                self.handle_failed_login(username)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {str(e)}")
        finally:
            conn.close()

    def open_student_dashboard(self, username):
        self.student_dashboard = StudentDashboard(username)  # Create dashboard instance
        self.student_dashboard.show()  # Show dashboard

    def handle_failed_login(self, username):
        """Handle and display failed login attempt."""
        # Record the failed attempt
        attempts, _ = self.login_attempt_tracker.record_failed_attempt(username)
        
        # Display specific error messages based on attempts
        if attempts == 1:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password. Try again.")
        elif attempts == 2:
            QMessageBox.warning(self, "Login Failed", "Second failed attempt. One more try before temporary lockout.")
        else:
            QMessageBox.warning(self, "Account Locked", 
                "Too many failed attempts. Please wait 5 minutes before trying again.")
            
    def reset_login_attempts(self, username):
        """Reset login attempts after successful authentication."""
        if hasattr(self, 'login_attempts') and username in self.login_attempts:
            del self.login_attempts[username]

    def prompt_password_change(self, student_id):
        """Prompt first-time students to create a new password."""
        new_password, ok = QInputDialog.getText(self, "Set Password", "Enter a new password:", QLineEdit.Password)
        
        if ok and new_password:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("UPDATE students SET password = ? WHERE student_id = ?", (hashed_password, student_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Password Set", "Your new password has been saved. Please log in again.")
        else:
            QMessageBox.warning(self, "Password Change Failed", "You must set a password to continue.")

    
    def open_admin_dashboard(self):
        """Opens the Admin Dashboard after successful login."""
        from admin.admin_dashboard import AdminDashboard
        self.admin_window = AdminDashboard()
        self.admin_window.show()
        self.close()
