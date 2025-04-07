import sys
import sqlite3
from PyQt5.QtWidgets import (QHBoxLayout, 
                           QPushButton, QDialog, QFormLayout, QLineEdit,
                           QMessageBox)
from PyQt5.QtCore import Qt
from config.utils_constants import DATABASE_PATH

class CourseDialog(QDialog):
    def __init__(self, parent=None, course_code=None):
        super().__init__(parent)
        
        self.course_code = course_code
        self.is_edit_mode = course_code is not None
        
        if self.is_edit_mode:
            self.setWindowTitle("Edit Course")
        else:
            self.setWindowTitle("Add New Course")
        
        self.setGeometry(300, 200, 400, 200)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_course_data()
    
    def setup_ui(self):
        """Set up the dialog UI elements"""
        layout = QFormLayout()
        
        # Course code input
        self.course_code_input = QLineEdit()
        layout.addRow("Course Code:", self.course_code_input)
        
        # Course name input
        self.course_name_input = QLineEdit()
        layout.addRow("Course Name:", self.course_name_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_course)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        
        self.setLayout(layout)
    
    def load_course_data(self):
        """Load existing course data for editing"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT course_name 
                FROM courses WHERE course_code = ?
            """, (self.course_code,))
            
            course = cursor.fetchone()
            conn.close()
            
            if not course:
                QMessageBox.warning(self, "Error", "Course not found")
                self.reject()
                return
            
            # Set values in the form
            course_name = course[0]
            
            self.course_code_input.setText(self.course_code)
            self.course_code_input.setReadOnly(True)  # Cannot change primary key in edit mode
            self.course_name_input.setText(course_name or "")
                
        except Exception as e:
            print(f"❌ Error loading course data: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load course data: {e}")
            self.reject()
    
    def save_course(self):
        """Save the course to the database"""
        try:
            course_code = self.course_code_input.text().strip()
            course_name = self.course_name_input.text().strip()
            
            # Validate input
            if not course_code:
                QMessageBox.warning(self, "Input Error", "Course code is required")
                return
                
            if not course_name:
                QMessageBox.warning(self, "Input Error", "Course name is required")
                return
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Check for duplicate course codes (only in add mode)
            if not self.is_edit_mode:
                cursor.execute("SELECT COUNT(*) FROM courses WHERE course_code = ?", (course_code,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Duplicate Course", f"A course with the code '{course_code}' already exists")
                    return
            
            if self.is_edit_mode:
                # Update existing course
                cursor.execute("""
                    UPDATE courses SET 
                    course_name = ?
                    WHERE course_code = ?
                """, (course_name, self.course_code))
                
                message = "Course updated successfully"
            else:
                # Insert new course
                cursor.execute("""
                    INSERT INTO courses 
                    (course_code, course_name) 
                    VALUES (?, ?)
                """, (course_code, course_name))
                
                message = "Course created successfully"
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Success", message)
            self.accept()
            
        except Exception as e:
            print(f"❌ Error saving course: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not save course: {e}")