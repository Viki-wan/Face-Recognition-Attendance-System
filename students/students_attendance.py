from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sqlite3
from config.utils_constants import DATABASE_PATH

class StudentAttendancePage(QWidget):
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("✅ My Attendance Records")
        title.setFont(QFont('Arial', 16))
        layout.addWidget(title)
        
        # Summary Statistics
        self.summary_layout = QHBoxLayout()
        self.total_attendance_label = QLabel("Total Attendance Records: 0")
        self.present_count_label = QLabel("Present: 0")
        self.absent_count_label = QLabel("Absent: 0")
        
        self.summary_layout.addWidget(self.total_attendance_label)
        self.summary_layout.addWidget(self.present_count_label)
        self.summary_layout.addWidget(self.absent_count_label)
        
        layout.addLayout(self.summary_layout)
        
        # Attendance Table
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(2)
        self.attendance_table.setHorizontalHeaderLabels(["Date", "Status"])
        self.attendance_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.attendance_table)
        
        # Refresh Button
        self.refresh_button = QPushButton("🔄 Refresh Attendance")
        self.refresh_button.clicked.connect(self.load_attendance_data)
        layout.addWidget(self.refresh_button)
        
        self.setLayout(layout)
        
        # Load initial data
        self.load_attendance_data()
    
    def load_attendance_data(self):
        """Fetch and display student's attendance records."""
        # Clear existing table data
        self.attendance_table.setRowCount(0)
        
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Fetch individual attendance records
            cursor.execute("""
                SELECT date, status
                FROM attendance 
                WHERE student_id = ? 
                ORDER BY date DESC
            """, (self.student_id,))
            records = cursor.fetchall()
            
            # Calculate attendance statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                    SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count
                FROM attendance 
                WHERE student_id = ?
            """, (self.student_id,))
            stats = cursor.fetchone()
            
            conn.close()
            
            # Update summary statistics
            total_records = stats[0] if stats[0] is not None else 0
            present_count = stats[1] if stats[1] is not None else 0
            absent_count = stats[2] if stats[2] is not None else 0
            
            self.total_attendance_label.setText(f"Total Attendance Records: {total_records}")
            self.present_count_label.setText(f"Present: {present_count}")
            self.absent_count_label.setText(f"Absent: {absent_count}")
            
            # Populate attendance table
            self.attendance_table.setRowCount(len(records))
            for row, (date, status) in enumerate(records):
                # Date column
                date_item = QTableWidgetItem(str(date))
                date_item.setTextAlignment(Qt.AlignCenter)
                self.attendance_table.setItem(row, 0, date_item)
                
                # Status column with color coding
                status_item = QTableWidgetItem(str(status))
                status_item.setTextAlignment(Qt.AlignCenter)
                if status == 'Present':
                    status_item.setForeground(Qt.green)
                else:
                    status_item.setForeground(Qt.red)
                self.attendance_table.setItem(row, 1, status_item)
            
            self.attendance_table.resizeColumnsToContents()
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Attendance Error", f"Could not load attendance records: {e}")