import sys
import sqlite3
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, 
                           QPushButton, QDialog, QFormLayout, QLineEdit,
                           QMessageBox, QComboBox, QListWidget, QListWidgetItem, QLabel, QSpinBox,
                           QGroupBox, QScrollArea, QWidget, QCheckBox, QFrame, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QIcon
import re
from config.utils_constants import DATABASE_PATH

class ClassDialog(QDialog):
    def __init__(self, parent=None, class_id=None):
        super().__init__(parent)
        
        # Get the global stylesheet
        self.setStyleSheet(QApplication.instance().styleSheet())
        
        self.class_id = class_id
        self.is_edit_mode = class_id is not None
        
        if self.is_edit_mode:
            self.setWindowTitle("Edit Class")
        else:
            self.setWindowTitle("Add New Class")
        
        # Allow resizing for better responsiveness
        self.setMinimumSize(650, 500)
        self.setGeometry(300, 200, 700, 550)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_class_data()
    
    def setup_ui(self):
        """Set up the dialog UI elements"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create a scroll area for the entire content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Create form layout for basic information
        basic_info_group = QGroupBox("Basic Information")
        basic_info_group.setFont(QFont("", 10, QFont.Bold))
        basic_info_layout = QFormLayout()
        basic_info_layout.setSpacing(12)
        basic_info_layout.setContentsMargins(20, 25, 20, 20)
        basic_info_layout.setLabelAlignment(Qt.AlignRight)
        
        # Class ID input (read-only if in edit mode)
        self.class_id_input = QLineEdit()
        self.class_id_input.setPlaceholderText("Enter class ID (e.g., MATH 102)")
        if self.is_edit_mode:
            self.class_id_input.setText(str(self.class_id))
            self.class_id_input.setReadOnly(True)
        else:
            self.class_id_input.setPlaceholderText("Auto-generated if empty")
            
        # Add help text in a layout
        format_label = QLabel("Format: DEPT 123 (e.g., MATH 102, COMP 230)")
        format_label.setStyleSheet("color: gray; font-size: 10pt;")
        
        id_layout = QVBoxLayout()
        id_layout.addWidget(self.class_id_input)
        id_layout.addWidget(format_label)
        basic_info_layout.addRow("Class ID: *", id_layout)
        
        self.class_id_input.textChanged.connect(self.format_class_id)
        
        # Class name input with required indicator
        self.class_name_input = QLineEdit()
        self.class_name_input.setPlaceholderText("Enter class name")
        basic_info_layout.addRow("Class Name: *", self.class_name_input)
                
        # Year selection (1-6)
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setMinimum(1)
        self.year_spinbox.setMaximum(6)
        self.year_spinbox.setValue(1)  # Default to first year
        self.year_spinbox.valueChanged.connect(self.update_semester_options)
        basic_info_layout.addRow("Year: *", self.year_spinbox)
        
        # Semester selection (dropdown with filtered options based on year)
        self.semester_combo = QComboBox()
        self.update_semester_options(1)  # Initialize with year 1 options
        basic_info_layout.addRow("Semester: *", self.semester_combo)

        # Apply consistent styling
        input_style = """
            QLineEdit, QComboBox, QSpinBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                background-color: #fcfcfc;
                min-height: 18px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #4a86e8;
                background-color: #f0f7ff;
            }
            QComboBox::drop-down {
                border: 0px;
                padding-right: 10px;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 15px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #444;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: 0px;
                width: 16px;
                height: 12px;
            }
        """
        basic_info_group.setStyleSheet(input_style)
        basic_info_group.setLayout(basic_info_layout)
        scroll_layout.addWidget(basic_info_group)
        
        # Course selection with improved styling
        course_group = QGroupBox("Course Selection")
        course_group.setFont(QFont("", 10, QFont.Bold))
        course_layout = QVBoxLayout()
        course_layout.setSpacing(15)
        course_layout.setContentsMargins(20, 25, 20, 20)
        
        # Add search field for courses
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Courses:")
        search_label.setFixedWidth(120)
        search_layout.addWidget(search_label)
        
        self.course_search = QLineEdit()
        self.course_search.setPlaceholderText("Type to filter courses...")
        self.course_search.textChanged.connect(self.filter_courses)
        search_layout.addWidget(self.course_search)
        
        course_layout.addLayout(search_layout)
        
        # Required indicator
        required_label = QLabel("* Please select at least one course")
        required_label.setStyleSheet("color: gray; font-style: italic;")
        course_layout.addWidget(required_label)
        
        # Available courses list with better styling
        self.course_list = QListWidget()
        self.course_list.setSelectionMode(QListWidget.NoSelection)  # We'll use checkboxes instead
        self.course_list.setAlternatingRowColors(True)
        self.course_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
                min-height: 150px;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 5px;
            }
            QListWidget::item:alternate {
                background-color: #f9f9f9;
            }
        """)
        self.load_courses(self.course_list)
        course_layout.addWidget(self.course_list)
        
        course_group.setLayout(course_layout)
        scroll_layout.addWidget(course_group)
        
        # Instructor selection with improved styling
        instructor_group = QGroupBox("Instructor Assignment")
        instructor_group.setFont(QFont("", 10, QFont.Bold))
        instructor_layout = QVBoxLayout()
        instructor_layout.setSpacing(15)
        instructor_layout.setContentsMargins(20, 25, 20, 20)
        
        instructor_help = QLabel("Select a course above to see available instructors")
        instructor_help.setStyleSheet("color: gray; font-style: italic;")
        instructor_layout.addWidget(instructor_help)
        
        instructor_selection = QHBoxLayout()
        instructor_selection.setSpacing(10)
        
        instructor_label = QLabel("Available Instructors:")
        instructor_label.setFixedWidth(120)
        instructor_selection.addWidget(instructor_label)
        
        self.instructor_combo = QComboBox()
        self.instructor_combo.setMinimumWidth(250)
        instructor_selection.addWidget(self.instructor_combo)
        
        self.add_instructor_button = QPushButton("Add Instructor")
        self.add_instructor_button.setIcon(QIcon("icons/add.png"))  # Add an icon if available
        self.add_instructor_button.setStyleSheet("""
            QPushButton {
                background-color: #e7f3ff;
                border: 1px solid #4a86e8;
                border-radius: 4px;
                padding: 8px 15px;
                color: #2d6fd2;
            }
            QPushButton:hover {
                background-color: #d0e7ff;
            }
            QPushButton:pressed {
                background-color: #b8d8ff;
            }
        """)
        self.add_instructor_button.clicked.connect(self.add_instructor)
        instructor_selection.addWidget(self.add_instructor_button)
        
        instructor_layout.addLayout(instructor_selection)
        
        # Display assigned instructors with better styling
        assigned_label = QLabel("Assigned Instructors:")
        assigned_label.setFont(QFont("", 9, QFont.Bold))
        instructor_layout.addWidget(assigned_label)
        
        self.assigned_instructors_label = QLabel("None")
        self.assigned_instructors_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 10px;
                min-height: 20px;
            }
        """)
        instructor_layout.addWidget(self.assigned_instructors_label)
        
        self.course_list.itemSelectionChanged.connect(self.update_instructors_for_course)
        self.course_list.itemClicked.connect(self.update_instructors_for_course)
        
        # Store assigned instructors
        self.assigned_instructors = []
        
        instructor_group.setLayout(instructor_layout)
        scroll_layout.addWidget(instructor_group)
        
        # Set the scroll content and add to main layout
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Required fields note
        required_note = QLabel("* Required fields")
        required_note.setStyleSheet("color: gray; font-size: 10pt;")
        main_layout.addWidget(required_note)
        
        # Bottom buttons with improved styling
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Add a spacer to push buttons to the right
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.setMinimumWidth(100)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                border: 1px solid #2d6fd2;
                border-radius: 4px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b77d9;
            }
            QPushButton:pressed {
                background-color: #2d6fd2;
            }
        """)
        self.save_button.clicked.connect(self.save_class)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def update_semester_options(self, year):
        """Update semester options based on the selected year"""
        self.semester_combo.clear()
        
        # Only show relevant semesters for the selected year
        semester_1 = f"{year}.1"
        semester_2 = f"{year}.2"
        
        self.semester_combo.addItem(semester_1, semester_1)
        self.semester_combo.addItem(semester_2, semester_2)
    
    def filter_courses(self):
        """Filter courses based on search text"""
        search_text = self.course_search.text().lower()
        for i in range(self.course_list.count()):
            item = self.course_list.item(i)
            if search_text in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def validate_class_id(self, class_id):
        """Validate class ID format: DEPT followed by 3 digits, with optional space"""
                
        # Pattern: 2-4 letters followed by optional space and 3 digits
        pattern = r'^[A-Za-z]{2,4}\s?[0-9]{3}$'
        
        if not re.match(pattern, class_id):
            return False, "Class ID must be in format: DEPT 123 or DEPT123"
        
        # Extract digits from the class ID
        digits = ''.join(c for c in class_id if c.isdigit())
        
        # Extract year from the first digit of the course number
        year_digit = int(digits[0])
        if year_digit < 1 or year_digit > 6:
            return False, "The first digit of the course number must be 1-6 to represent the year"
        
        return True, ""    
        
    def format_class_id(self):
        """Auto-format class ID as user types"""
        text = self.class_id_input.text()
        
        # If we have at least 4 characters and the 4th isn't a space
        if len(text) >= 4 and text[3] != ' ' and text[3].isdigit():
            # Insert a space between letters and numbers
            dept = ''.join(c for c in text if c.isalpha()).upper()
            nums = ''.join(c for c in text if c.isdigit())
            
            # Only proceed if we have both department and numbers
            if dept and nums:
                formatted = f"{dept} {nums}"
                self.class_id_input.setText(formatted)
                self.class_id_input.setCursorPosition(len(formatted))

    def load_courses(self, list_widget):
        """Load courses for the list widget"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT course_code, course_name 
                FROM courses
                ORDER BY course_name
            """)
            
            courses = cursor.fetchall()
            conn.close()
            
            list_widget.clear()
            for course in courses:
                course_code, course_name = course
                item = QListWidgetItem(f"{course_name} ({course_code})")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                item.setData(Qt.UserRole, course_code)
                list_widget.addItem(item)
                
        except Exception as e:
            print(f"❌ Error loading courses: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load courses: {e}")

    def update_instructors_for_course(self):
        """Update the instructors combo box based on the selected course"""
        try:
            selected_course_codes = []
            for i in range(self.course_list.count()):
                item = self.course_list.item(i)
                if item.checkState() == Qt.Checked and not item.isHidden():
                    selected_course_codes.append(item.data(Qt.UserRole))
            
            if not selected_course_codes:
                self.instructor_combo.clear()
                return
                
            # Use the first selected course to find instructors
            course_code = selected_course_codes[0]
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Query instructors assigned to this course
            cursor.execute("""
                SELECT i.instructor_id, i.instructor_name 
                FROM instructors i
                JOIN instructor_courses ic ON i.instructor_id = ic.instructor_id
                WHERE ic.course_code = ?
                ORDER BY i.instructor_name
            """, (course_code,))
            
            instructors = cursor.fetchall()
            conn.close()
            
            self.instructor_combo.clear()
            for instructor in instructors:
                instructor_id, instructor_name = instructor
                self.instructor_combo.addItem(instructor_name, instructor_id)
                
        except Exception as e:
            print(f"❌ Error loading instructors for course: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load instructors: {e}")
    
    def add_instructor(self):
        """Add selected instructor to the class"""
        if self.instructor_combo.count() == 0:
            QMessageBox.warning(self, "No Instructors", 
                              "No instructors available for this course. Please select a course first.")
            return
            
        instructor_id = self.instructor_combo.currentData()
        instructor_name = self.instructor_combo.currentText()
        
        # Check if instructor already assigned
        if instructor_id in [i[0] for i in self.assigned_instructors]:
            QMessageBox.warning(self, "Duplicate Instructor", 
                               f"Instructor '{instructor_name}' is already assigned to this class")
            return
        
        self.assigned_instructors.append((instructor_id, instructor_name))
        self.update_assigned_instructors_label()
    
    def update_assigned_instructors_label(self):
        """Update the label showing assigned instructors"""
        if not self.assigned_instructors:
            self.assigned_instructors_label.setText("None")
        else:
            instructor_names = ", ".join([i[1] for i in self.assigned_instructors])
            self.assigned_instructors_label.setText(instructor_names)
    
    def load_class_data(self):
        """Load existing class data for editing"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get class details
            cursor.execute("""
                SELECT class_name, course_code, year, semester
                FROM classes 
                WHERE class_id = ?
            """, (self.class_id,))
            
            class_data = cursor.fetchone()
            
            if not class_data:
                QMessageBox.warning(self, "Error", "Class not found")
                self.reject()
                return
            
            class_name, course_code, year, semester = class_data
            
            # Get assigned instructors
            cursor.execute("""
                SELECT ci.instructor_id, i.instructor_name
                FROM class_instructors ci
                JOIN instructors i ON ci.instructor_id = i.instructor_id
                WHERE ci.class_id = ?
            """, (self.class_id,))
            
            instructors = cursor.fetchall()
            
            # Get assigned courses
            cursor.execute("""
                SELECT cc.course_code
                FROM class_courses cc
                WHERE cc.class_id = ?
            """, (self.class_id,))

            assigned_courses = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Set values in the form
            self.class_id_input.setText(str(self.class_id))
            self.class_name_input.setText(class_name)
            
            # Check the appropriate course checkboxes
            for i in range(self.course_list.count()):
                item = self.course_list.item(i)
                if item.data(Qt.UserRole) in assigned_courses:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
            
            # Set year (which will update semester options)
            self.year_spinbox.setValue(year)
            
            # Update semester options based on year
            self.update_semester_options(year)
            
            # Find and select the correct semester
            semester_index = 0
            for i in range(self.semester_combo.count()):
                if self.semester_combo.itemText(i) == semester:
                    semester_index = i
                    break
            self.semester_combo.setCurrentIndex(semester_index)
            
            # Set assigned instructors
            self.assigned_instructors = list(instructors)
            self.update_assigned_instructors_label()
                
        except Exception as e:
            print(f"❌ Error loading class data: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load class data: {e}")
            self.reject()
    
    def save_class(self):
        """Save the class to the database"""
        conn = None
        try:
            custom_id = self.class_id_input.text().strip().upper()
            class_name = self.class_name_input.text().strip()
            year = self.year_spinbox.value()
            semester = self.semester_combo.currentText()
            
            # Validate class ID format
            if custom_id:
                is_valid, error_message = self.validate_class_id(custom_id)
                if not is_valid:
                    QMessageBox.warning(self, "Invalid Class ID", error_message)
                    return
            
            # Validate input
            if not class_name:
                QMessageBox.warning(self, "Input Error", "Class name is required")
                return
            
            # Get selected courses
            selected_courses = []
            for i in range(self.course_list.count()):
                item = self.course_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_courses.append(item.data(Qt.UserRole))
            
            if not selected_courses:
                QMessageBox.warning(self, "Input Error", "Please select at least one course")
                return
            
            # Connect to database
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Start database transaction
            conn.execute("BEGIN TRANSACTION")
            
            try:
                if self.is_edit_mode:
                    # Update existing class
                    cursor.execute("""
                        UPDATE classes SET 
                        class_name = ?,
                        year = ?,
                        semester = ?
                        WHERE class_id = ?
                    """, (class_name, year, semester, self.class_id))
                    
                    # Remove all existing course assignments
                    cursor.execute("""
                        DELETE FROM class_courses
                        WHERE class_id = ?
                    """, (self.class_id,))
                    
                    # Remove all existing instructor assignments
                    cursor.execute("""
                        DELETE FROM class_instructors
                        WHERE class_id = ?
                    """, (self.class_id,))
                    
                    class_id = self.class_id
                    message = "Class updated successfully"
                else:
                    # Handle custom ID if provided
                    if custom_id:
                        # Check if ID already exists
                        cursor.execute("SELECT COUNT(*) FROM classes WHERE class_id = ?", (custom_id,))
                        if cursor.fetchone()[0] > 0:
                            QMessageBox.warning(self, "ID Error", "Class ID already exists")
                            conn.rollback()
                            conn.close()
                            return
                        
                        # Use the first selected course as the primary course
                        primary_course = selected_courses[0]
                        
                        # Insert with specified ID
                        cursor.execute("""
                            INSERT INTO classes 
                            (class_id, class_name, course_code, year, semester) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (custom_id, class_name, primary_course, year, semester))
                        class_id = custom_id
                    else:
                        # Use the first selected course as the primary course
                        primary_course = selected_courses[0]
                        
                        # Insert with auto-generated ID
                        cursor.execute("""
                            INSERT INTO classes 
                            (class_name, course_code, year, semester) 
                            VALUES (?, ?, ?, ?)
                        """, (class_name, primary_course, year, semester))
                        class_id = cursor.lastrowid
                    
                    message = "Class created successfully"

                # Insert class-course associations for all selected courses
                for course_code in selected_courses:
                    cursor.execute("""
                        INSERT INTO class_courses
                        (class_id, course_code)
                        VALUES (?, ?)
                    """, (class_id, course_code))
                
                # Add instructor assignments
                for instructor_id, _ in self.assigned_instructors:
                    cursor.execute("""
                        INSERT INTO class_instructors 
                        (class_id, instructor_id) 
                        VALUES (?, ?)
                    """, (class_id, instructor_id))
                
                # Commit transaction
                conn.commit()
                
                QMessageBox.information(self, "Success", message)
                self.accept()
                
            except Exception as e:
                # Rollback in case of error
                if conn is not None:  # Make sure conn exists before calling rollback
                    conn.rollback()
                raise e
                
        except Exception as e:
            print(f"❌ Error saving class: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not save class: {e}")
            
        finally:
            # Only close connection if it exists and is not None
            if conn is not None:  # Explicit check for None
                conn.close()