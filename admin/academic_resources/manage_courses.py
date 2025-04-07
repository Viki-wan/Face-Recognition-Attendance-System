import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QTableWidgetItem, QPushButton, QLabel, QDialog, QMessageBox)
from PyQt5.QtCore import Qt
from config.utils_constants import DATABASE_PATH
from admin.academic_resources.course_dialog import CourseDialog

class CourseManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Course Management")
        
        # Main layout
        layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel("Course Management", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        description_label = QLabel("Manage courses", self)
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.create_course_button = QPushButton("➕ Add Course")
        self.create_course_button.clicked.connect(self.create_course)
        buttons_layout.addWidget(self.create_course_button)
        
        self.edit_course_button = QPushButton("✏️ Edit Selected")
        self.edit_course_button.clicked.connect(self.edit_course)
        buttons_layout.addWidget(self.edit_course_button)
        
        self.delete_course_button = QPushButton("🗑️ Delete Selected")
        self.delete_course_button.clicked.connect(self.delete_course)
        buttons_layout.addWidget(self.delete_course_button)
        
        self.refresh_course_button = QPushButton("🔄 Refresh")
        self.refresh_course_button.clicked.connect(self.load_courses)
        buttons_layout.addWidget(self.refresh_course_button)
        
        layout.addLayout(buttons_layout)
        
        # Courses table
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(2)
        self.courses_table.setHorizontalHeaderLabels([
            "Course Name", "Code"
        ])
        layout.addWidget(self.courses_table)
        
        # Set column widths
        self.courses_table.setColumnWidth(0, 350)  # Course Name
        self.courses_table.setColumnWidth(1, 150)  # Code
        
        self.setLayout(layout)
        
        # Load existing courses
        self.load_courses()
        
    def load_courses(self):
        """Load all courses from the database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get all courses ordered by name
            cursor.execute("""
                SELECT course_name, course_code
                FROM courses 
                ORDER BY course_name
            """)
            
            courses = cursor.fetchall()
            conn.close()
            
            # Clear table
            self.courses_table.setRowCount(0)
            
            # Populate table
            for row_num, course in enumerate(courses):
                self.courses_table.insertRow(row_num)
                for col_num, data in enumerate(course):
                    # Handle NULL values
                    if data is None:
                        data = ""
                    self.courses_table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
            
            print(f"✅ Loaded {len(courses)} courses")
            
        except Exception as e:
            print(f"❌ Error loading courses: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load courses: {e}")
    
    def create_course(self):
        """Open dialog to create a new course"""
        dialog = CourseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_courses()  # Refresh the table
    
    def edit_course(self):
        """Edit the selected course"""
        selected_rows = self.courses_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a course to edit")
            return
        
        # Get the course code from the second column
        row = selected_rows[0].row()
        course_code = self.courses_table.item(row, 1).text()
        
        dialog = CourseDialog(self, course_code=course_code)
        if dialog.exec_() == QDialog.Accepted:
            self.load_courses()  # Refresh the table
    
    def delete_course(self):
        """Delete the selected course"""
        selected_rows = self.courses_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a course to delete")
            return
        
        # Get the course information
        row = selected_rows[0].row()
        course_name = self.courses_table.item(row, 0).text()
        course_code = self.courses_table.item(row, 1).text()
        
        # Check if course is in use
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Check if course is assigned to any instructors
            cursor.execute("SELECT COUNT(*) FROM instructor_courses WHERE course_code = ?", (course_code,))
            instructor_count = cursor.fetchone()[0]
            
            # Check if course is used in any classes
            cursor.execute("SELECT COUNT(*) FROM classes WHERE course_code = ?", (course_code,))
            class_count = cursor.fetchone()[0]
            
            # Check if course is assigned to any students
            cursor.execute("SELECT COUNT(*) FROM student_courses WHERE course_code = ?", (course_code,))
            student_count = cursor.fetchone()[0]
            
            conn.close()
            
            if instructor_count > 0 or class_count > 0 or student_count > 0:
                QMessageBox.warning(
                    self, "Course In Use", 
                    f"Cannot delete '{course_name}' as it is:\n"
                    f"• Assigned to {instructor_count} instructor(s)\n"
                    f"• Used in {class_count} class(es)\n"
                    f"• Enrolled by {student_count} student(s)"
                )
                return
            
        except Exception as e:
            print(f"❌ Error checking course references: {e}")
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete the course '{course_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM courses WHERE course_code = ?", (course_code,))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Success", "Course deleted successfully")
                self.load_courses()  # Refresh the table
                
            except Exception as e:
                print(f"❌ Error deleting course: {e}")
                QMessageBox.warning(self, "Database Error", f"Could not delete course: {e}")