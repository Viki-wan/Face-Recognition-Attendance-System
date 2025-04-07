from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QPushButton, 
                            QComboBox, QDialog)
from PyQt5.QtCore import Qt, QTimer
from config.utils_constants import *
import sqlite3
import time as system_time
from datetime import datetime
from config.utils import enhance_image


class ClassSessionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Class Session")
        self.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout()
        
        # Class Selection
        self.course_combo = QComboBox()
        self.instructor_combo = QComboBox()
        self.class_combo = QComboBox()
        
        # Populate Dropdowns
        self.populate_dropdowns()
        
        layout.addWidget(QLabel("Select Course:"))
        layout.addWidget(self.course_combo)
        layout.addWidget(QLabel("Select Instructor:"))
        layout.addWidget(self.instructor_combo)
        layout.addWidget(QLabel("Select Class:"))
        layout.addWidget(self.class_combo)
        
        # Confirm Button
        self.confirm_btn = QPushButton("Start Attendance")
        self.confirm_btn.clicked.connect(self.accept)
        layout.addWidget(self.confirm_btn)
        
        self.setLayout(layout)
        
        self.selected_session = None

    def populate_dropdowns(self):
        """Populate dropdowns from database."""
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Fetch courses
        cursor.execute("SELECT course_code, course_name FROM courses")
        courses = cursor.fetchall()
        self.course_combo.addItems([course[1] for course in courses])
        
        # Fetch instructors
        cursor.execute("SELECT instructor_id, instructor_name FROM instructors")
        instructors = cursor.fetchall()
        self.instructor_combo.addItems([instructor[1] for instructor in instructors])
        
        # Add signals to update class combo when course or instructor changes
        self.course_combo.currentIndexChanged.connect(self.update_class_combo)
        self.instructor_combo.currentIndexChanged.connect(self.update_class_combo)
        
        # Initial update of classes
        self.update_class_combo()
        
        conn.close()

    def update_class_combo(self):
        """Update class combo box based on selected course and instructor."""
        self.class_combo.clear()
        
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get course_code for selected course_name
        cursor.execute("SELECT course_code FROM courses WHERE course_name = ?", 
                      (self.course_combo.currentText(),))
        course_code_result = cursor.fetchone()
        if not course_code_result:
            conn.close()
            return
        
        course_code = course_code_result[0]
        
        # Get instructor_id for selected instructor_name
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_name = ?", 
                      (self.instructor_combo.currentText(),))
        instructor_id_result = cursor.fetchone()
        if not instructor_id_result:
            conn.close()
            return
        
        instructor_id = instructor_id_result[0]
        
        # Find classes that match the course and instructor
        cursor.execute("""
            SELECT c.class_name 
            FROM classes c
            JOIN class_instructors ci ON c.class_id = ci.class_id
            JOIN instructor_courses ic ON ic.instructor_id = ci.instructor_id AND ic.course_code = c.course_code
            WHERE c.course_code = ? AND ci.instructor_id = ?
        """, (course_code, instructor_id))
        
        classes = [row[0] for row in cursor.fetchall()]
        
        # If no classes found with both filters, show all classes for the course
        if not classes:
            cursor.execute("SELECT class_name FROM classes WHERE course_code = ?", (course_code,))
            classes = [row[0] for row in cursor.fetchall()]
        
        self.class_combo.addItems(classes)
        conn.close()

    def get_selected_session(self):
        """Return selected session details."""
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Get course_code for selected course_name
        cursor.execute("SELECT course_code FROM courses WHERE course_name = ?", 
                      (self.course_combo.currentText(),))
        course_code = cursor.fetchone()[0]
        
        # Get instructor_id for selected instructor_name
        cursor.execute("SELECT instructor_id FROM instructors WHERE instructor_name = ?", 
                      (self.instructor_combo.currentText(),))
        instructor_id = cursor.fetchone()[0]
        
        # Get class_id for selected class_name and course_code
        cursor.execute("SELECT class_id FROM classes WHERE class_name = ? AND course_code = ?", 
                      (self.class_combo.currentText(), course_code))
        class_id_result = cursor.fetchone()
        
        conn.close()
        
        if not class_id_result:
            return None
            
        class_id = class_id_result[0]
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Create a new session record structure to return
        session_details = {
            'class_id': class_id,
            'date': current_date,
            'start_time': current_time,
            'end_time': None,  # Will be set when session ends
            'status': 'active',
            'course_code': course_code,
            'instructor_id': instructor_id,
            'course_name': self.course_combo.currentText(),
            'instructor_name': self.instructor_combo.currentText(),
            'class_name': self.class_combo.currentText()
        }
        
        return session_details