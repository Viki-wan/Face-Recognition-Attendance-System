from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem, QWidget,
    QLabel, QLineEdit, QPushButton, QApplication, QHBoxLayout, QComboBox, QFileDialog, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
import sqlite3
import csv
from config.utils_constants import DATABASE_PATH

class ViewAttendanceWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Attendance Records")
        self.setGeometry(300, 200, 800, 550)  # ✅ Slightly wider window

        self.setObjectName("ViewAttendanceWindow")
        self.setStyleSheet(QApplication.instance().styleSheet())  # ✅ Inherit global QSS

        self.records = []  # ✅ Ensure `self.records` is always defined

        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        self.table_widget = QTableWidget()
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setAlternatingRowColors(True)
        
        # 🔍 **Search Input**
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("🔍 Search by Student ID or Name...")
        self.search_input.textChanged.connect(self.apply_filters)

        # 📅 **Date Filter**
        self.date_filter = QDateEdit(self)
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.dateChanged.connect(self.apply_filters)

        # ✅ **Status Filter**
        self.status_filter = QComboBox(self)
        self.status_filter.addItems(["All", "Present", "Absent"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        
        # 📊 **Course Filter**
        self.course_filter = QComboBox(self)
        self.course_filter.addItem("All Courses")
        self.load_courses()
        self.course_filter.currentTextChanged.connect(self.apply_filters)

        # 📂 **Export Button**
        self.export_button = QPushButton("📂 Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)

        # 🔄 **Refresh Button**
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_attendance_data)

        # 🔹 **Layout Adjustments**
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(QLabel("📅 Date:"))
        top_layout.addWidget(self.date_filter)
        top_layout.addWidget(QLabel("✅ Status:"))
        top_layout.addWidget(self.status_filter)
        
        second_row_layout = QHBoxLayout()
        second_row_layout.addWidget(QLabel("📊 Course:"))
        second_row_layout.addWidget(self.course_filter)
        second_row_layout.addWidget(self.refresh_button)
        second_row_layout.addWidget(self.export_button)
        second_row_layout.addStretch()

        main_layout = QVBoxLayout()
        self.title_label = QLabel("📋 Attendance Records")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(self.title_label)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(second_row_layout)
        main_layout.addWidget(self.table_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_attendance_data()

    def load_courses(self):
        """Load course names into the course filter dropdown."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT course_name FROM courses ORDER BY course_name")
            courses = cursor.fetchall()
            conn.close()
            
            for course in courses:
                self.course_filter.addItem(course[0])
        except Exception as e:
            print(f"Error loading courses: {e}")

    def refresh_attendance_data(self):
        """Reload attendance data."""
        self.load_attendance_data()
        self.apply_filters()

    def load_attendance_data(self):
        """Fetch and display attendance records from the database using the correct schema."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Using the correct database schema with joins to relevant tables
            cursor.execute("""
                SELECT 
                    s.student_id, 
                    s.name, 
                    c.course_name,
                    cs.date, 
                    cs.start_time,
                    cs.end_time,
                    a.status,
                    (SELECT COUNT(*) FROM attendance 
                    WHERE attendance.student_id = s.student_id 
                    AND attendance.status = 'Present') AS total_present
                FROM 
                    students s
                JOIN 
                    attendance a ON s.student_id = a.student_id
                JOIN 
                    class_sessions cs ON a.session_id = cs.session_id
                JOIN 
                    classes cl ON cs.class_id = cl.class_id
                JOIN 
                    courses c ON cl.course_code = c.course_code
                ORDER BY 
                    cs.date DESC, 
                    cs.start_time DESC,
                    s.name
            """)
            
            self.records = cursor.fetchall()
            conn.close()
            
            self.populate_table(self.records)
        except Exception as e:
            print(f"Error loading attendance data: {e}")
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            
    def populate_table(self, records):
        """Populates the table with the given records."""
        self.table_widget.setRowCount(len(records))
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels([
            "Student ID", 
            "Name", 
            "Course", 
            "Date", 
            "Start Time", 
            "End Time", 
            "Status", 
            "Total Present"
        ])

        for row_idx, row_data in enumerate(records):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data) if col_data is not None else "")
                item.setTextAlignment(Qt.AlignCenter)
                # Make status column bold with color
                if col_idx == 6:  # Status column
                    if col_data == "Present":
                        item.setForeground(Qt.darkGreen)
                    elif col_data == "Absent":
                        item.setForeground(Qt.red)
                self.table_widget.setItem(row_idx, col_idx, item)

        self.table_widget.resizeColumnsToContents()

    def apply_filters(self):
        """Applies filtering based on search, date, status, and course."""
        search_text = self.search_input.text().strip().lower()
        selected_date = self.date_filter.date().toString("yyyy-MM-dd")
        selected_status = self.status_filter.currentText()
        selected_course = self.course_filter.currentText()

        for row in range(self.table_widget.rowCount()):
            student_id = self.table_widget.item(row, 0).text().lower()
            name = self.table_widget.item(row, 1).text().lower()
            course = self.table_widget.item(row, 2).text()
            date = self.table_widget.item(row, 3).text()
            status = self.table_widget.item(row, 6).text()

            matches_search = search_text in student_id or search_text in name
            matches_date = selected_date in date or not selected_date
            matches_status = selected_status == "All" or status == selected_status
            matches_course = selected_course == "All Courses" or course == selected_course

            if matches_search and matches_date and matches_status and matches_course:
                self.table_widget.setRowHidden(row, False)
            else:
                self.table_widget.setRowHidden(row, True)

    def export_to_csv(self):
        """Exports the attendance data to a CSV file with a user-selected name."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)", options=options
        )

        if not file_path:
            return  # ✅ Exit if the user cancels

        try:
            with open(file_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Student ID", 
                    "Name", 
                    "Course", 
                    "Date", 
                    "Start Time", 
                    "End Time", 
                    "Status", 
                    "Total Present"
                ])

                for row in range(self.table_widget.rowCount()):
                    if not self.table_widget.isRowHidden(row):  # ✅ Export only visible rows
                        row_data = []
                        for col in range(self.table_widget.columnCount()):
                            item = self.table_widget.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)

            print(f"✅ Attendance exported to {file_path}")
        except Exception as e:
            print(f"Error exporting to CSV: {e}")