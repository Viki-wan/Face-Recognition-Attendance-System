import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QTableWidgetItem, QPushButton, QApplication, QLabel, QDialog, QMessageBox,
                           QLineEdit, QGroupBox, QComboBox, QHeaderView)
from PyQt5.QtCore import Qt
from config.utils_constants import DATABASE_PATH
from admin.academic_resources.class_dialog import ClassDialog
from config.table_functions import TableFunctions

class ClassManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Class Management")
        
        # Main layout
        layout = QVBoxLayout()

        # Apply the stylesheet to the entire widget
        self.setStyleSheet(QApplication.instance().styleSheet())
        
        # Title and description with object names
        title_label = QLabel("Class Management", self)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        description_label = QLabel("Manage classes and their course assignments", self)
        description_label.setObjectName("description_label")
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        
        # Filter and search section
        filter_group = QGroupBox("Search and Filter")
        filter_group.setObjectName("filter_group")
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("search_edit")
        self.search_edit.setPlaceholderText("Search by class name or course code...")
        filter_layout.addWidget(self.search_edit)
        
        self.course_filter = QComboBox()
        self.course_filter.setObjectName("course_filter")
        self.course_filter.addItem("All Courses", None)
        self.load_courses_for_filter()
        self.course_filter.setPlaceholderText("Filter by course...")
        filter_layout.addWidget(self.course_filter)
        
        self.instructor_filter = QComboBox()
        self.instructor_filter.setObjectName("instructor_filter")
        self.instructor_filter.addItem("All Instructors", None)
        self.load_instructors_for_filter()
        self.instructor_filter.setPlaceholderText("Filter by instructor...")
        filter_layout.addWidget(self.instructor_filter)
        
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("search_button")
        self.search_button.setProperty("class", "primary_button")
        self.search_button.clicked.connect(self.load_classes)
        filter_layout.addWidget(self.search_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("reset_button")
        self.reset_button.setProperty("class", "primary_button")
        self.reset_button.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_button)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Classes table
        self.classes_table = QTableWidget()
        self.classes_table.setObjectName("classes_table")
        self.classes_table.setProperty("class", "classes_table")
        self.classes_table.setColumnCount(6)
        self.classes_table.setHorizontalHeaderLabels([
            "ID", "Class Name", "Course", "Course Code", "Instructors", "Actions"
        ])
        # Set up selection and context menu
        TableFunctions.setup_selection_features(
            self.classes_table,
            delete_callback=self.delete_selected_classes,
            parent=self
        )
        self.classes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.classes_table.horizontalHeader().setStretchLastSection(True)
        self.classes_table.setSortingEnabled(True)
        self.classes_table.horizontalHeader().setSectionsClickable(True)
        layout.addWidget(self.classes_table)
        
        # Set column widths
        self.classes_table.setColumnWidth(0, 30)    # ID
        self.classes_table.setColumnWidth(1, 200)   # Class Name
        self.classes_table.setColumnWidth(2, 200)   # Course
        self.classes_table.setColumnWidth(3, 60)    # Course Code
        self.classes_table.setColumnWidth(4, 300)   # Instructors
        self.classes_table.setColumnWidth(5, 220)   # Actions
        
        self.classes_table.verticalHeader().setDefaultSectionSize(60)
        self.classes_table.setAlternatingRowColors(True)
        self.classes_table.horizontalHeader().setFixedHeight(40)
        self.classes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add New Class")
        self.add_button.setObjectName("add_button")
        self.add_button.setProperty("class", "primary_button")
        self.add_button.clicked.connect(self.create_class)
        buttons_layout.addWidget(self.add_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("refresh_button")
        self.refresh_button.setProperty("class", "primary_button")
        self.refresh_button.clicked.connect(self.load_classes)
        buttons_layout.addWidget(self.refresh_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Load existing classes
        self.load_classes()
            
    
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
    
    def load_instructors_for_filter(self):
        """Load instructors for the filter dropdown"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT instructor_id, instructor_name FROM instructors ORDER BY instructor_name")
            instructors = cursor.fetchall()
            conn.close()
            
            for instructor in instructors:
                instructor_id, instructor_name = instructor
                self.instructor_filter.addItem(instructor_name, instructor_id)
                
        except Exception as e:
            print(f"❌ Error loading instructors for filter: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load instructors: {e}")
    
    def reset_filters(self):
        """Reset all filters to their default values"""
        self.search_edit.clear()
        self.course_filter.setCurrentIndex(0)
        self.instructor_filter.setCurrentIndex(0)
        self.load_classes()
        
    def load_classes(self):
        """Load all classes from the database with filter options"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get search text and filters
            search_text = self.search_edit.text().strip()
            course_code = self.course_filter.currentData()
            instructor_id = self.instructor_filter.currentData()
            
            # Build query based on filters
            params = []
            query_parts = []
            
            base_query = """
                SELECT DISTINCT c.class_id, c.class_name, c.course_code, co.course_name
                FROM classes c
                JOIN courses co ON c.course_code = co.course_code
            """
            
            if instructor_id:
                base_query += " JOIN class_instructors ci ON c.class_id = ci.class_id"
                query_parts.append("ci.instructor_id = ?")
                params.append(instructor_id)
            
            if course_code:
                query_parts.append("c.course_code = ?")
                params.append(course_code)
            
            if search_text:
                query_parts.append("(c.class_name LIKE ? OR c.course_code LIKE ?)")
                params.extend([f"%{search_text}%", f"%{search_text}%"])
            
            if query_parts:
                base_query += " WHERE " + " AND ".join(query_parts)
            
            base_query += " ORDER BY c.class_name"
            
            cursor.execute(base_query, params)
            classes = cursor.fetchall()
            
            # Get instructors for each class
            class_instructors = {}
            for class_data in classes:
                class_id = class_data[0]
                
                cursor.execute("""
                    SELECT i.instructor_name
                    FROM class_instructors ci
                    JOIN instructors i ON ci.instructor_id = i.instructor_id
                    WHERE ci.class_id = ?
                """, (class_id,))
                
                instructors = cursor.fetchall()
                instructor_names = ", ".join([i[0] for i in instructors]) if instructors else "None"
                class_instructors[class_id] = instructor_names
            
            conn.close()
            
            # Display classes in the table
            self.display_classes(classes, class_instructors)
            
            print(f"✅ Loaded {len(classes)} classes")
            
        except Exception as e:
            print(f"❌ Error loading classes: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load classes: {e}")

    def delete_selected_classes(self, class_ids):
        """Delete multiple selected classes"""
        if not class_ids:
            return
        
        # Track results
        success_count = 0
        error_count = 0
        
        # Save scroll position
        scrollbar = self.classes_table.verticalScrollBar()
        current_pos = scrollbar.value()
        
        for class_id in class_ids:
            if self.delete_class_impl(class_id, show_confirmation=False):
                success_count += 1
            else:
                error_count += 1
        
        # Show summary message
        if success_count > 0:
            message = f"Successfully deleted {success_count} classes."
            if error_count > 0:
                message += f"\n{error_count} classes could not be deleted (they may be in use)."
            QMessageBox.information(self, "Batch Deletion Result", message)
            
            # Refresh the table while maintaining position
            def refresh_operation():
                self.load_classes()
                return True
            
            TableFunctions.maintain_scroll_position(self.classes_table, refresh_operation)
        elif error_count > 0:
            QMessageBox.warning(
                self, "Deletion Failed", 
                "No classes could be deleted. They may be in use."
            )
    def delete_class_impl(self, class_id, show_confirmation=True):
        """Implementation of class deletion logic that can be called for batch deletions"""
        # Get the class name
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT class_name FROM classes WHERE class_id = ?", (class_id,))
            result = cursor.fetchone()
            
            if not result:
                if show_confirmation:
                    QMessageBox.warning(self, "Error", "Class not found")
                return False
                
            class_name = result[0]
            
            # Check if class has any sessions
            cursor.execute("SELECT COUNT(*) FROM class_sessions WHERE class_id = ?", (class_id,))
            session_count = cursor.fetchone()[0]
            
            # Check if class has any attendance records (via sessions)
            cursor.execute("""
                SELECT COUNT(*) FROM attendance a
                JOIN class_sessions cs ON a.session_id = cs.session_id
                WHERE cs.class_id = ?
            """, (class_id,))
            attendance_count = cursor.fetchone()[0]
            
            conn.close()
            
            if session_count > 0 or attendance_count > 0:
                if show_confirmation:
                    QMessageBox.warning(
                        self, "Class In Use", 
                        f"Cannot delete '{class_name}' as it has:\n"
                        f"• {session_count} scheduled session(s)\n"
                        f"• {attendance_count} attendance record(s)"
                    )
                return False
                
        except Exception as e:
            print(f"❌ Error checking class references: {e}")
            if show_confirmation:
                QMessageBox.warning(self, "Database Error", f"Could not check class references: {e}")
            return False
        
        # Confirm deletion if requested
        if show_confirmation:
            confirm = QMessageBox.question(
                self, "Confirm Deletion", 
                f"Are you sure you want to delete the class '{class_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return False
        
        # Perform the actual deletion
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # First delete class instructor assignments
            cursor.execute("DELETE FROM class_instructors WHERE class_id = ?", (class_id,))
            
            # Then delete the class
            cursor.execute("DELETE FROM classes WHERE class_id = ?", (class_id,))
            
            # Commit transaction
            cursor.execute("COMMIT")
            conn.close()
            
            if show_confirmation:
                QMessageBox.information(self, "Success", "Class deleted successfully")
            
            return True
                
        except Exception as e:
            print(f"❌ Error deleting class: {e}")
            if show_confirmation:
                QMessageBox.warning(self, "Database Error", f"Could not delete class: {e}")
            
            # Rollback in case of error
            try:
                cursor.execute("ROLLBACK")
            except:
                pass
            
            return False
    def display_classes(self, classes, class_instructors):
        """Display classes in the table with their data"""
        self.classes_table.setRowCount(0)
        
        for row_num, class_data in enumerate(classes):
            class_id, class_name, course_code, course_name = class_data
            instructor_names = class_instructors[class_id]
            
            self.classes_table.insertRow(row_num)
            
            # Add data to table
            self.classes_table.setItem(row_num, 0, QTableWidgetItem(str(class_id)))
            self.classes_table.setItem(row_num, 1, QTableWidgetItem(class_name))
            self.classes_table.setItem(row_num, 2, QTableWidgetItem(course_name))
            self.classes_table.setItem(row_num, 3, QTableWidgetItem(course_code))
            self.classes_table.setItem(row_num, 4, QTableWidgetItem(instructor_names))
            
            # Add action buttons with object names and classes
            action_cell = QWidget()
            action_layout = QHBoxLayout(action_cell)
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_button = QPushButton("Edit")
            edit_button.setObjectName(f"edit_button_{class_id}")
            edit_button.setProperty("class", "action_button")
            edit_button.setProperty("class_id", class_id)
            edit_button.clicked.connect(lambda _, cid=class_id: self.edit_class(cid))
            action_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Delete")
            delete_button.setObjectName(f"delete_button_{class_id}")
            delete_button.setProperty("class", "action_button")
            delete_button.setProperty("class_id", class_id)
            delete_button.clicked.connect(lambda _, cid=class_id: self.delete_class(cid))
            action_layout.addWidget(delete_button)
            
            action_cell.setLayout(action_layout)
            self.classes_table.setCellWidget(row_num, 5, action_cell)
        
        # Resize columns to content
        self.classes_table.resizeColumnsToContents()
        
    def create_class(self):
        """Open dialog to create a new class"""
        dialog = ClassDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_classes()  # Refresh the table
    
    def edit_class(self, class_id):
        """Edit the selected class"""
        dialog = ClassDialog(self, class_id=class_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_classes()  # Refresh the table
    
    def delete_class(self, class_id):
        """Delete the selected class and maintain table position"""
        def operation():
            return self.delete_class_impl(class_id)
        
        result = TableFunctions.maintain_scroll_position(self.classes_table, operation)
        if result:
            # Refresh the table while maintaining position
            def refresh_operation():
                self.load_classes()
                return True
            
            TableFunctions.maintain_scroll_position(self.classes_table, refresh_operation)