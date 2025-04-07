import os
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QObject, pyqtSignal, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRect
from PyQt5.QtGui import QColor

class ThemeManager(QObject):
    # Add a signal for theme changes
    theme_changed = pyqtSignal(str)
    
    def __init__(self, app, database_path):
        """
        Initialize theme manager.
        
        Args:
            app (QApplication): The Qt application instance
            database_path (str): Path to the application database
        """
        super().__init__()  # Initialize QObject
        self.app = app
        self.database_path = database_path
        self.current_theme = "light"  # Default theme
        self.themes = {
            "light": "styles/style.qss",
            "dark": "styles/dark.qss"
        }
        
        # Flag to track if animations are in progress
        self.animation_in_progress = False
    
    def load_theme_from_settings(self):
        """
        Load theme based on settings in the database.
        
        Returns:
            str: The name of the loaded theme
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'dark_mode'")
            result = cursor.fetchone()
            conn.close()
            
            # Determine theme based on setting value
            theme_name = "dark" if result and result[0] == "1" else "light"
            self.load_theme(theme_name)
            return theme_name
            
        except sqlite3.Error as e:
            print(f"⚠️ Database error when loading theme: {e}")
            # Fall back to light theme
            self.load_theme("light")
            return "light"
    
    def load_theme(self, theme_name):
        """
        Load a specific theme.
        
        Args:
            theme_name (str): The name of the theme to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        if theme_name not in self.themes:
            print(f"❌ Theme '{theme_name}' not found!")
            return False
        
        theme_path = self.themes[theme_name]
        
        # Check if the theme file exists
        if not os.path.exists(theme_path):
            print(f"❌ Theme file not found: {theme_path}")
            return False
        
        # Load stylesheet
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
            
            # Apply stylesheet
            self.app.setStyleSheet(stylesheet)
            self.current_theme = theme_name
            print(f"✅ Applied theme: {theme_name}")
            
            # Force style update on all top-level widgets
            self._update_all_widgets()
            
            return True
        except Exception as e:
            print(f"❌ Error loading theme file: {e}")
            return False
        
    def get_current_theme_name(self):
        """
        Get the name of the current theme.
        
        Returns:
            str: The name of the current theme
        """
        return self.current_theme
    
    def toggle_theme(self):
        """
        Toggle between light and dark themes and save to database.
        
        Returns:
            str: The name of the new theme
        """
        # Prevent multiple theme changes during animation
        if self.animation_in_progress:
            print("⚠️ Theme change already in progress")
            return self.current_theme
            
        new_theme = "dark" if self.current_theme == "light" else "light"
        
        # Create fade out animation
        self._animate_theme_change(new_theme)
        
        # Save the new theme preference to the database
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE settings SET setting_value = ? WHERE setting_key = 'dark_mode'", 
                ("1" if new_theme == "dark" else "0",)
            )
            conn.commit()
            conn.close()
            print(f"✅ Saved theme preference: {new_theme}")
            
            # Emit the theme_changed signal
            self.theme_changed.emit(new_theme)
            
        except sqlite3.Error as e:
            print(f"⚠️ Database error when saving theme: {e}")
        
        return new_theme
    
    def _animate_theme_change(self, new_theme):
        """
        Apply theme change with improved performance
        
        Args:
            new_theme (str): The name of the new theme
        """
        self.animation_in_progress = True
        
        try:
            # Load new theme stylesheet
            with open(self.themes[new_theme], "r", encoding="utf-8") as f:
                new_stylesheet = f.read()
            
            # Direct application without animation for better performance
            self.app.setStyleSheet(new_stylesheet)
            self.current_theme = new_theme
            
            # Force style update on all widgets
            self._update_all_widgets()
        finally:
            # Always mark animation as complete, even if an error occurs
            self.animation_in_progress = False
    
        
    def _update_all_widgets(self):
        """
        Force style refresh on all top-level widgets and their children.
        """
        # Just request a style update without recursively forcing all children
        for widget in QApplication.topLevelWidgets():
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()