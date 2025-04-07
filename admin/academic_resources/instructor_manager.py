import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QTableWidgetItem, QPushButton, QLabel, QMessageBox, 
                           QLineEdit, QGroupBox, QDialog, QComboBox, QApplication)
from PyQt5.QtCore import Qt
from config.utils_constants import DATABASE_PATH
from admin.academic_resources.instructor_dialog import InstructorDialog
from PyQt5.QtWidgets import QMenu, QHeaderView, QDialog, QVBoxLayout, QListWidget
from PyQt5.QtCore import Qt

class InstructorManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Instructor Management")
        
        # Apply the stylesheet to the entire widget
        self.setStyleSheet(QApplication.instance().styleSheet())

        # Main layout
        layout = QVBoxLayout()
        
        # Title and description with object names
        title_label = QLabel("Instructor Management", self)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        description_label = QLabel("Manage instructors and their course assignments", self)
        description_label.setObjectName("description_label")
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        
        # Filter and search section
        filter_group = QGroupBox("Search and Filter")
        filter_group.setObjectName("filter_group")
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("search_edit")
        self.search_edit.setPlaceholderText("Search by name, email, or phone...")
        filter_layout.addWidget(self.search_edit)
        
        self.course_filter = QComboBox()
        self.course_filter.setObjectName("course_filter")
        self.course_filter.addItem("All Courses", None)
        self.load_courses_for_filter()
        self.course_filter.setPlaceholderText("Filter by course...")
        filter_layout.addWidget(self.course_filter)
        
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("search_button")
        self.search_button.setProperty("class", "primary_button")
        self.search_button.clicked.connect(self.load_instructors)
        filter_layout.addWidget(self.search_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("reset_button")
        self.reset_button.setProperty("class", "primary_button")
        self.reset_button.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_button)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Table for displaying instructors
        self.instructors_table = QTableWidget()
        self.instructors_table.setObjectName("instructors_table")
        self.instructors_table.setProperty("class", "instructors_table")
        self.instructors_table.setColumnCount(5)

        # In the __init__ method, after creating the sessions_table:
        self.instructors_table.horizontalHeader().setDefaultSectionSize(120)  # Default column width
        self.instructors_table.verticalHeader().setDefaultSectionSize(60)     # Default row height

        self.instructors_table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Phone", "Actions"])
        self.instructors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.instructors_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.instructors_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.instructors_table)

        self.instructors_table.setSortingEnabled(True)
        self.instructors_table.horizontalHeader().setSectionsClickable(True)
        
        self.instructors_table.setColumnWidth(0, 40)  # #
        self.instructors_table.setColumnWidth(1, 40)  # ID
        self.instructors_table.setColumnWidth(2, 150)  # Name
        self.instructors_table.setColumnWidth(3, 180)  # Email
        self.instructors_table.setColumnWidth(4, 120)  # Phone
        self.instructors_table.setColumnWidth(5, 300)  # Assigned Courses
        self.instructors_table.setColumnWidth(6, 220)  # Actions - wider to fit both buttons

        self.instructors_table.verticalHeader().setDefaultSectionSize(60)
        self.instructors_table.setAlternatingRowColors(True)

        # Buttons for managing instructors
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add New Instructor")
        self.add_button.setObjectName("add_button")
        self.add_button.setProperty("class", "primary_button")
        self.add_button.clicked.connect(self.add_instructor)
        buttons_layout.addWidget(self.add_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("refresh_button")
        self.refresh_button.setProperty("class", "primary_button")
        self.refresh_button.clicked.connect(self.load_instructors)
        buttons_layout.addWidget(self.refresh_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        self.load_instructors()
 
                
        # Add alternating row colors for better readability
        self.instructors_table.setAlternatingRowColors(True)
        
        # Sticky/frozen header that remains visible when scrolling
        self.instructors_table.horizontalHeader().setFixedHeight(40)
        self.instructors_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)    
           
    def load_courses_for_filter(self):
        """Load courses for the filter dropdown"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT course_code, course_name FROM courses ORDER BY course_name")
            courses = cursor.fetchall()
            conn.close()
            
            for course in courses:
                course_code, course_name = course
                self.course_filter.addItem(f"{course_name} ({course_code})", course_code)
                
        except Exception as e:
            print(f"❌ Error loading courses for filter: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load courses: {e}")
    
    def reset_filters(self):
        """Reset all filters to their default values"""
        self.search_edit.clear()
        self.course_filter.setCurrentIndex(0)
        self.load_instructors()
    
    def load_instructors(self):
        """Load instructors based on filter criteria"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get search text and course filter
            search_text = self.search_edit.text().strip()
            course_code = self.course_filter.currentData()
            
            # Basic query to get all instructors
            if course_code:
                # Filter by course
                query = """
                    SELECT DISTINCT i.instructor_id, i.instructor_name, i.email, i.phone
                    FROM instructors i
                    JOIN instructor_courses ic ON i.instructor_id = ic.instructor_id
                    WHERE ic.course_code = ?
                """
                params = [course_code]
                
                if search_text:
                    query += """ AND (
                        i.instructor_name LIKE ? OR 
                        i.email LIKE ? OR 
                        i.phone LIKE ?
                    )"""
                    params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])
            else:
                # No course filter
                if search_text:
                    query = """
                        SELECT instructor_id, instructor_name, email, phone
                        FROM instructors
                        WHERE instructor_name LIKE ? OR email LIKE ? OR phone LIKE ?
                    """
                    params = [f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"]
                else:
                    query = "SELECT instructor_id, instructor_name, email, phone FROM instructors"
                    params = []
            
            query += " ORDER BY instructor_name"
            
            cursor.execute(query, params)
            instructors = cursor.fetchall()
            
            # For each instructor, get their assigned courses
            instructor_courses = {}
            for instructor in instructors:
                instructor_id = instructor[0]
                cursor.execute("""
                    SELECT c.course_code, c.course_name
                    FROM instructor_courses ic
                    JOIN courses c ON ic.course_code = c.course_code
                    WHERE ic.instructor_id = ?
                """, (instructor_id,))
                courses = cursor.fetchall()
                instructor_courses[instructor_id] = courses
            
            conn.close()
            
            # Display instructors in the table
            self.display_instructors(instructors, instructor_courses)
            
        except Exception as e:
            print(f"❌ Error loading instructors: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load instructors: {e}")
    
    def display_instructors(self, instructors, instructor_courses):
        """Display instructors in the table with their courses"""
        self.instructors_table.setRowCount(0)
        
        # Add an extra column for courses if not already there
        if self.instructors_table.columnCount() < 6:
            self.instructors_table.setColumnCount(6)
            self.instructors_table.setHorizontalHeaderLabels(
                ["ID", "Name", "Email", "Phone", "Assigned Courses", "Actions"])
        
        for row_index, instructor in enumerate(instructors):
            instructor_id, name, email, phone = instructor
            
            self.instructors_table.insertRow(row_index)
            
            # Set instructor data in the table
            self.instructors_table.setItem(row_index, 0, QTableWidgetItem(str(instructor_id)))
            self.instructors_table.setItem(row_index, 1, QTableWidgetItem(name))
            self.instructors_table.setItem(row_index, 2, QTableWidgetItem(email or ""))
            self.instructors_table.setItem(row_index, 3, QTableWidgetItem(phone or ""))
            
            # Format assigned courses
            courses = instructor_courses.get(instructor_id, [])
            course_text = ", ".join([f"{name} ({code})" for code, name in courses])
            self.instructors_table.setItem(row_index, 4, QTableWidgetItem(course_text))
            
            # Add action buttons
            action_cell = QWidget()
            action_layout = QHBoxLayout(action_cell)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_button = QPushButton("Edit")
            edit_button.setObjectName(f"edit_button_{instructor_id}")
            edit_button.setProperty("class", "action_button")
            edit_button.setProperty("instructor_id", instructor_id)
            edit_button.clicked.connect(lambda _, iid=instructor_id: self.edit_instructor(iid))
            action_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Delete")
            delete_button.setObjectName(f"delete_button_{instructor_id}")
            delete_button.setProperty("class", "action_button")
            delete_button.setProperty("instructor_id", instructor_id)
            delete_button.clicked.connect(lambda _, iid=instructor_id: self.delete_instructor(iid))
            action_layout.addWidget(delete_button)
            
            action_cell.setLayout(action_layout)
            self.instructors_table.setCellWidget(row_index, 5, action_cell) 
                   
        # Resize columns to content
        self.instructors_table.resizeColumnsToContents()
    
    def add_instructor(self):
        """Open dialog to add a new instructor"""
        dialog = InstructorDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            self.load_instructors()
    
    def edit_instructor(self, instructor_id):
        """Open dialog to edit an existing instructor"""
        dialog = InstructorDialog(self, instructor_id=instructor_id)
        
        if dialog.exec_() == QDialog.Accepted:
            self.load_instructors()
    
    def delete_instructor(self, instructor_id):
        """Delete an instructor after confirmation"""
        # First check if instructor is assigned to any classes
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.class_name 
                FROM class_instructors ci
                JOIN classes c ON ci.class_id = c.class_id
                WHERE ci.instructor_id = ?
            """, (instructor_id,))
            
            assigned_classes = cursor.fetchall()
            conn.close()
            
            if assigned_classes:
                class_names = ", ".join([c[0] for c in assigned_classes])
                QMessageBox.warning(
                    self, 
                    "Cannot Delete",
                    f"This instructor is assigned to the following classes: {class_names}\n\n"
                    "Please remove the instructor from these classes before deleting."
                )
                return
            
        except Exception as e:
            print(f"❌ Error checking instructor classes: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not check instructor classes: {e}")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            "Are you sure you want to delete this instructor?\n\n"
            "This will also remove all course assignments for this instructor.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Delete instructor courses
                cursor.execute("DELETE FROM instructor_courses WHERE instructor_id = ?", (instructor_id,))
                
                # Delete instructor
                cursor.execute("DELETE FROM instructors WHERE instructor_id = ?", (instructor_id,))
                
                # Commit transaction
                cursor.execute("COMMIT")
                conn.close()
                
                QMessageBox.information(self, "Success", "Instructor deleted successfully")
                self.load_instructors()
                
            except Exception as e:
                print(f"❌ Error deleting instructor: {e}")
                QMessageBox.warning(self, "Database Error", f"Could not delete instructor: {e}")
                
                # Rollback in case of error
                try:
                    cursor.execute("ROLLBACK")
                except:
                    pass