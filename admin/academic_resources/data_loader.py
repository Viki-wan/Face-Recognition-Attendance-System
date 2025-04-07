from PyQt5.QtCore import pyqtSignal, QObject
from config.utils_constants import DATABASE_PATH

class DataLoader(QObject):
    """Worker class for loading data in background thread"""
    courses_loaded = pyqtSignal(tuple)  
    classes_loaded = pyqtSignal(tuple)  
    instructor_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    done = pyqtSignal()  # Add this signal

    def __init__(self, db_manager, instructor_id=None):
        super().__init__()
        self.db_manager = db_manager
        self.instructor_id = instructor_id
        self.selected_courses = []
    
    def load_courses(self):
        try:
            # Get all courses
            courses = self.db_manager.execute_query(
                "SELECT course_code, course_name FROM courses ORDER BY course_code",
                fetchall=True
            )

            # Get instructor's courses if in edit mode
            instructor_courses = []
            if self.instructor_id:
                instructor_courses_data = self.db_manager.execute_query(
                    "SELECT course_code FROM instructor_courses WHERE instructor_id = ?",
                    (self.instructor_id,),
                    fetchall=True
                )
                instructor_courses = [course[0] for course in instructor_courses_data]
                self.selected_courses = instructor_courses.copy()

            self.courses_loaded.emit((courses, instructor_courses))
        except Exception as e:
            self.error_occurred.emit(f"Error loading courses: {e}")
    
    def load_classes(self, filter_by_courses=True):
        try:
            query = """
                SELECT c.class_id, c.class_name, c.course_code, co.course_name
                FROM classes c
                JOIN courses co ON c.course_code = co.course_code
            """

            params = []
            
            if filter_by_courses and self.selected_courses:
                placeholders = ', '.join(['?' for _ in self.selected_courses])
                query += f" WHERE c.course_code IN ({placeholders})"
                params.extend(self.selected_courses)
            
            query += " ORDER BY c.class_name"
            
            classes = self.db_manager.execute_query(query, params, fetchall=True)
            
            # Get instructor's classes if in edit mode
            instructor_classes = []
            if self.instructor_id:
                instructor_classes_data = self.db_manager.execute_query(
                    "SELECT class_id FROM class_instructors WHERE instructor_id = ?",
                    (self.instructor_id,),
                    fetchall=True
                )
                instructor_classes = [class_id[0] for class_id in instructor_classes_data]
            
            self.classes_loaded.emit((classes, instructor_classes))
        except Exception as e:
            self.error_occurred.emit(f"Error loading classes: {e}")
            
        self.done.emit()

    def load_instructor_data(self):
        try:
            if not self.instructor_id:
                self.error_occurred.emit("No instructor ID provided")
                return

            instructor = self.db_manager.execute_query(
                "SELECT instructor_name, email, phone FROM instructors WHERE instructor_id = ?",
                (self.instructor_id,),
                fetchone=True
            )

            if not instructor:
                self.error_occurred.emit(f"Instructor not found with ID {self.instructor_id}")
                return

            # Get academic period from the first instructor course
            academic_period = ""  # Default empty since it's not in the database

            instructor_data = {
                'name': instructor[0],
                'email': instructor[1] or "",
                'phone': instructor[2] or "",
                'academic_period': academic_period
            }

            self.instructor_loaded.emit(instructor_data)
        except Exception as e:
            self.error_occurred.emit(f"Error loading instructor data: {e}")

    def load_all_data(self):
        """Load all necessary data and emit done signal"""
        if self.instructor_id:
            self.load_instructor_data()
        self.load_courses()
        self.load_classes(True)
        self.done.emit() 