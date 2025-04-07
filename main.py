import os
import sys
import sqlite3
from PyQt5.QtWidgets import QApplication
from admin.login_window import LoginWindow
from styles.theme_manager import ThemeManager


DATABASE_PATH = "attendance.db"  # Ensure this points to your actual DB path

def load_settings():
    """Loads settings from the database."""
    settings = {}
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM settings")
        settings = dict(cursor.fetchall())
        conn.close()
    except sqlite3.Error as e:
        print(f"⚠️ Database error: {e}")
    
    return settings

def main():
    """Initialize and start the application."""
    app = QApplication(sys.argv)

    # Initialize theme manager with database path
    theme_manager = ThemeManager(app, DATABASE_PATH)
    
    # Load theme based on database settings
    theme_manager.load_theme_from_settings()
    
    # Make theme manager available app-wide by storing it as an application property
    app.setProperty("theme_manager", theme_manager)

    # Start with the login window
    login_window = LoginWindow()
    login_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()