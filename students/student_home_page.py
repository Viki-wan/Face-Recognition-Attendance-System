import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QGridLayout, QPushButton, QSizePolicy, QSpacerItem)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt
from datetime import datetime
from config.utils_constants import DATABASE_PATH

class StudentHomePage(QWidget):
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        
        # Set object name for styling
        self.setObjectName("studentDashboard")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Top section with welcome and quick stats
        top_section = QHBoxLayout()
        top_section.addWidget(self.create_welcome_section())
        top_section.addWidget(self.create_quick_stats_section())
        
        main_layout.addLayout(top_section)
        
        # Recent activities section
        main_layout.addWidget(self.create_recent_activities_section())
        
        # Add vertical spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def create_welcome_section(self):
        """Create personalized welcome section"""
        welcome_frame = QFrame()
        welcome_frame.setObjectName("dashboardTile")
        welcome_layout = QVBoxLayout(welcome_frame)
        
        try:
            conn = sqlite3.connect('attendance.db')  
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (self.student_id,))
            name_result = cursor.fetchone()
            student_name = name_result[0] if name_result else "Student"
            conn.close()
        except sqlite3.Error:
            student_name = "Student"
        
        # Welcome title
        welcome_title = QLabel("Dashboard")
        welcome_title.setObjectName("tileTitle")
        
        # Personalized greeting
        greeting_label = QLabel(f"Welcome, {student_name}")
        greeting_label.setObjectName("heading")
        
        # Motivational message
        motivation_label = QLabel("Keep up the great work!")
        motivation_label.setObjectName("subheading")
        
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(greeting_label)
        welcome_layout.addWidget(motivation_label)
        welcome_layout.addStretch(1)
        
        return welcome_frame
    
    def create_quick_stats_section(self):
        """Create a grid of quick stats"""
        stats_frame = QFrame()
        stats_frame.setObjectName("dashboardTile")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(10)
        
        # Define stats
        stats = [
            {
                "icon": ":/icons/attendance.png",  # Use resource icon or path
                "title": "Attendance",
                "value": self.fetch_attendance_stats(),
                "object_name": "attendance"
            },
            {
                "icon": ":/icons/calendar.png",
                "title": "Total Classes",
                "value": self.fetch_total_classes(),
                "object_name": "classes"
            },
            {
                "icon": ":/icons/performance.png",
                "title": "Performance",
                "value": self.fetch_performance_stats(),
                "object_name": "performance"
            }
        ]
        
        # Create stat cards
        for i, stat in enumerate(stats):
            card = self.create_stat_card(stat)
            stats_layout.addWidget(card, i // 3, i % 3)
        
        return stats_frame
    
    def create_stat_card(self, stat):
        """Create an individual stat card"""
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(stat['icon']).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setObjectName(f"{stat['object_name']}Icon")
        
        # Title
        title_label = QLabel(stat['title'])
        title_label.setObjectName("tileTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Value
        value_label = QLabel(str(stat['value']))
        value_label.setObjectName("tileValue")
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
    
    def create_recent_activities_section(self):
        """Create recent activities section with dynamic data from activity_log"""
        activities_frame = QFrame()
        activities_frame.setObjectName("dashboardTile")
        activities_layout = QVBoxLayout(activities_frame)
        
        # Title
        title_label = QLabel("Recent Activities")
        title_label.setObjectName("tileTitle")
        activities_layout.addWidget(title_label)
        
        # Fetch recent activities from database
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Fetch last 5 activities for this student
            cursor.execute("""
                SELECT timestamp, activity_type 
                FROM activity_log 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 5
            """, (self.student_id,))
            
            activities = cursor.fetchall()
            conn.close()
            
            # Display activities
            if not activities:
                no_activities_label = QLabel("No recent activities")
                no_activities_label.setObjectName("activityItem")
                activities_layout.addWidget(no_activities_label)
            else:
                for timestamp, activity_type in activities:
                    try:
                        # Convert timestamp to a more readable format
                        formatted_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                    except (ValueError, TypeError):
                        formatted_date = timestamp
                    # Format activity description
                    activity_description = self._format_activity_description(activity_type)
                    
                    activity_label = QLabel(f"{formatted_date} - {activity_description}")
                    activity_label.setObjectName("activityItem")
                    activities_layout.addWidget(activity_label)
        
        except sqlite3.Error as e:
            error_label = QLabel(f"Error fetching activities: {str(e)}")
            error_label.setObjectName("activityItem")
            activities_layout.addWidget(error_label)
        
        activities_layout.addStretch(1)
        
        return activities_frame
    
    def _format_activity_description(self, activity_type):
        
        activity_map = {
            'student_login': 'Logged into dashboard',
            'student_logout': 'Logged out of dashboard',
            'profile_update': 'Updated profile information',
            'password_change': 'Changed account password',
            'attendance_view': 'Viewed attendance records',
            'settings_update': 'Updated dashboard settings',
            'default': 'Performed an action'
        }
        
        return activity_map.get(activity_type, activity_map['default'])
    
    def fetch_attendance_stats(self):
        """Fetch attendance percentage"""
        try:
            conn = sqlite3.connect('attendance.db')  
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    ROUND(
                        (SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0)), 
                    2
                    ) as attendance_percentage
                FROM attendance 
                WHERE student_id = ?
            """, (self.student_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return f"{result[0] or 0}%"
        except Exception:
            return "N/A"
    
    def fetch_total_classes(self):
        """Fetch total number of classes"""
        try:
            conn = sqlite3.connect('attendance.db')  
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(DISTINCT date) as total_classes 
                FROM attendance 
                WHERE student_id = ?
            """, (self.student_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] or 0
        except Exception:
            return "N/A"
    
    def fetch_performance_stats(self):
        """Fetch a performance indicator"""
        try:
            conn = sqlite3.connect('attendance.db') 
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    ROUND(
                        (SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) * 100.0 / 
                        NULLIF(COUNT(*), 0)), 
                    2
                    ) as performance_score
                FROM attendance 
                WHERE student_id = ?
            """, (self.student_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return "Good" if result[0] and result[0] > 80 else "Needs Improvement"
        except Exception:
            return "N/A"