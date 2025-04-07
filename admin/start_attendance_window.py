import sys
import cv2
import sqlite3
import numpy as np
import face_recognition
import hashlib
import imagehash
from PIL import Image
import pickle
import uuid
import time as system_time
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDialog, QApplication, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from config.utils_constants import *
from admin.class_session_dialog import ClassSessionDialog
from admin.settings_window import SettingsWindow
from config.utils import enhance_image


def compute_phash(image_path):
        image = Image.open(image_path).convert("L").resize((64, 64))  # Convert to grayscale & resize
        return str(imagehash.phash(image))  # Returns a perceptual hash


class StartAttendanceWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📡 Start Attendance")
        self.setGeometry(300, 200, 750, 550)

        self.setObjectName("StartAttendanceWindow")

        self.last_unknown_save_time = 0
    
        self.setStyleSheet(QApplication.instance().styleSheet())  # ✅ Inherit global QSS

        self.current_session = None
        self.session_id = None

         # ✅ Load settings before applying them
        self.settings = self.load_settings()  
        self.apply_saved_settings()
        # ✅ Layout
        layout = QVBoxLayout()

        # ✅ Status Label
        self.status_label = QLabel("🔄 System Ready...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # ✅ Session Info Label
        self.session_info_label = QLabel("No active session", self)
        self.session_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.session_info_label)

        # ✅ Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # ✅ Attendance Table
        self.attendance_table = QTableWidget(self)
        self.attendance_table.setColumnCount(3)
        self.attendance_table.setHorizontalHeaderLabels(["Student ID", "Name", "Status"])
        layout.addWidget(self.attendance_table)

        # ✅ Start & Stop Buttons
        self.start_button = QPushButton("▶ Start Attendance")
        self.start_button.clicked.connect(self.initiate_attendance_session)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹ Stop Attendance")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_attendance)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

        # ✅ Timer for Processing
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

        # ✅ Load Known Faces
        self.known_faces, self.student_ids = self.load_known_faces()

        # ✅ Tracking Variables
        self.recognized_students = {}
        self.progress = 0
        self.match_counter = {}
        self.unknown_counter = 0
        self.cap = None
        self.attendance_running = False

    def refresh_known_faces(self):
        """Reload known faces and update cache."""
        self.known_faces, self.student_ids = self.load_known_faces()


    def get_name(self, student_id):
        """Fetch student name from the database using student_id."""
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else "Unknown"
    
    def load_application_data(self):
        """Load application settings and known faces."""
        self.settings = self.load_settings()
        self.known_faces, self.student_ids = self.load_known_faces()
        self.apply_saved_settings()

    def initiate_attendance_session(self):
        """Begin attendance process with session selection."""
        # Launch class session dialog
        session_dialog = ClassSessionDialog(self)
        if session_dialog.exec_() == QDialog.Accepted:
            # Retrieve selected session details
            self.current_session = session_dialog.get_selected_session()
            
            # Validate session details
            if not self.validate_session():
                return
            
            # Create session record
            self.session_id = self.create_session_record()
            if not self.session_id:
                QMessageBox.warning(self, "Session Error", "Failed to create session record")
                return
            
            # Update session info display
            self.update_session_display()
            
            # Start actual attendance process
            self.start_attendance()

    def update_session_display(self):
        """Update the session information on the UI."""
        if self.current_session:
            session_info = (f"Session: {self.current_session['course_name']} - "
                        f"{self.current_session['class_name']} with "
                        f"{self.current_session['instructor_name']}")
            self.session_info_label.setText(session_info)
        else:
            self.session_info_label.setText("No active session")

    def validate_session(self):
        """Validate the selected session details."""
        if not self.current_session:
            QMessageBox.warning(self, "Session Error", "No session selected")
            return False
        if not self.current_session['class_name']:
            QMessageBox.warning(self, "Session Error", "No class selected. There may not be any classes scheduled for today with the selected course and instructor.")
            return False
        # Additional validation checks can be added here
        return True

    def create_session_record(self):
        """Create a record of the current attendance session."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Insert session details into class_sessions table
            cursor.execute("""
                INSERT INTO class_sessions 
                (class_id, date, start_time, end_time, status) 
                VALUES (?, ?, ?, NULL, ?)
            """, (
                self.current_session['class_id'],
                self.current_session['date'],
                self.current_session['start_time'],
                'active'  # Status is set to active when starting a session
            ))

            session_id = cursor.lastrowid
            
            # Log activity
            cursor.execute("""
                INSERT INTO activity_log
                (user_id, activity_type, timestamp)
                VALUES (?, ?, datetime('now'))
            """, (
                "admin",  # Assuming the user is an admin; modify as needed
                f"Started attendance session for {self.current_session['class_name']}"
            ))
            
            conn.commit()
            conn.close()
            
            return session_id  # Return the session ID
            
        except Exception as e:
            print(f"Error creating session record: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not create session record: {e}")
            return None  # Return None to indicate failure
        
    def start_attendance(self): 
        """Start the attendance process with a loading indicator."""

        if not self.current_session or not self.session_id:
            QMessageBox.warning(self, "Session Error", "Please select a class session before starting attendance")
            return
        # Show loading status
        self.status_label.setText("🔄 Initializing camera...")
        self.progress_bar.setValue(10)
        QApplication.processEvents()  # Force UI update
        
        # Check if there are registered faces
        known_faces, student_ids = self.load_known_faces()
        if not known_faces:
            QMessageBox.warning(self, "No Registered Faces", "No students are registered")
            self.status_label.setText("🔄 System Ready...")
            self.progress_bar.setValue(0)
            return
        
        # Initialize camera with loading feedback
        self.status_label.setText("🔄 Opening camera...")
        self.progress_bar.setValue(30)
        QApplication.processEvents()  # Force UI update
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Could not open webcam")
            self.status_label.setText("❌ Camera error")
            self.progress_bar.setValue(0)
            return
        
        # Update UI to show loading progress
        self.status_label.setText("🔄 Preparing face recognition...")
        self.progress_bar.setValue(70)
        QApplication.processEvents()  # Force UI update
        
        # Disable start button, enable stop button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Update final status
        self.status_label.setText("✅ Attendance system active")
        self.progress_bar.setValue(100)
        QApplication.processEvents()  # Force UI update
        
        # Initialize counters
        match_counter = {}  # Track repeated matches for known faces
        unknown_counter = 0  # Track repeated unknown face appearances
        required_matches = int(self.settings.get("required_matches", "3"))  # Minimum times a face must be seen
        self.attendance_running = True  # Track if attendance is running
        
        # Main attendance loop
        while self.attendance_running:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            avg_brightness = gray.mean()

            if avg_brightness < 20:
                cv2.putText(frame, "Low light detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("Attendance System", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")

            if not face_locations:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                unknown_counter = 0  # Reset unknown counter if no face is found
                cv2.imshow("Attendance System", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):

                tolerance = int(self.settings.get("face_recognition_sensitivity", "50")) / 100
                matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=tolerance)
                face_distances = face_recognition.face_distance(known_faces, face_encoding)

                student_id = "Unknown"
                name = "Unknown"

                required_matches = int(self.settings.get("required_matches", "3"))

                save_unknown_faces = self.settings.get("save_unknown_faces", "1") == "1"

                # Check if we have any matches and face distances
                if len(known_faces) > 0 and len(matches) > 0 and np.any(matches):
                    best_match_index = int(np.argmin(face_distances))
                    
                    # Verify the index is valid
                    if best_match_index < len(matches) and best_match_index < len(student_ids):
                        if matches[best_match_index]:
                            student_id = student_ids[best_match_index]
                            name = self.get_name(student_id)

                        # Confidence Score
                        confidence = 1.0 - face_distances[best_match_index]
                        confidence_text = f"Confidence: {confidence:.2f}"

                        # ✅ Count the number of times a face is recognized
                        match_counter[student_id] = match_counter.get(student_id, 0) + 1

                        # ✅ Mark attendance only when seen required times
                        if match_counter[student_id] == required_matches:
                            self.mark_attendance(student_id)
                            # Add to the attendance table
                            self.update_table(student_id, name, "Present")
                else:
                    unknown_counter += 1

                    # ✅ Only save unknown faces if the setting is enabled
                    if save_unknown_faces and unknown_counter >= required_matches:
                        self.save_unknown_face(frame, face_location)
                        print(f"⚠️ Unknown face saved after {required_matches} detections.")
                        unknown_counter = 0  # Reset counter after saving
                    elif not save_unknown_faces:
                        print("⚠️ Unknown face ignored due to settings.")

                    # ✅ Save unknown face only if it appears multiple times
                    if unknown_counter == required_matches:
                        self.save_unknown_face(frame, face_location)
                        unknown_counter = 0  # Reset counter after saving
                        

                # ✅ Draw a box around the face
                top, right, bottom, left = face_location
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # ✅ Display the student's name and ID or "Unknown"
                label = f"{name} ({student_id})" if name != "Unknown" else "⚠️ Unknown"
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("Attendance System", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Process any pending UI events to keep the interface responsive
            QApplication.processEvents()

        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Reset UI when finished
        self.attendance_running = False
        self.status_label.setText("✅ Attendance Stopped.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.update_session_end_time()

    def update_session_end_time(self):
        """Update the session record with the end time when attendance is stopped."""
        if self.session_id:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                end_time = datetime.now().strftime("%H:%M:%S")
                
                # Update the class_sessions table with end time and change status to 'completed'
                cursor.execute("""
                    UPDATE class_sessions 
                    SET end_time = ?, status = 'completed' 
                    WHERE session_id = ?
                """, (end_time, self.session_id))
                
                # Log activity
                cursor.execute("""
                    INSERT INTO activity_log
                    (user_id, activity_type, timestamp)
                    VALUES (?, ?, datetime('now'))
                """, (
                    "admin",  # Assuming the user is an admin; modify as needed
                    f"Ended attendance session {self.session_id}"
                ))
                
                conn.commit()
                conn.close()
                
                print(f"✅ Session {self.session_id} ended at {end_time}")
            except Exception as e:
                print(f"Error updating session end time: {e}")

    def stop_attendance(self):
        """Stops attendance and ensures webcam is released instantly."""
        self.attendance_running = False  # ✅ Stops the loop immediately
        self.status_label.setText("✅ Attendance Stopped.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.timer.stop()

         # Release webcam
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

        self.update_session_end_time()

    def save_unknown_face(self, frame, face_location):
        """Save detected unknown faces with robust duplicate detection."""
        try:
            if not os.path.exists(UNKNOWN_DIR):
                os.makedirs(UNKNOWN_DIR)

            # Extract and pad face region
            top, right, bottom, left = face_location
            padding = 20
            top, bottom = max(0, top - padding), min(frame.shape[0], bottom + padding)
            left, right = max(0, left - padding), min(frame.shape[1], right + padding)
            face_img = frame[top:bottom, left:right]

            # Ensure face is large enough for recognition
            if face_img.shape[0] < MIN_FACE_SIZE or face_img.shape[1] < MIN_FACE_SIZE:
                print("⚠️ Face too small, skipping save.")
                return

            # Convert image and generate multiple hash types for better comparison
            pil_image = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
            standardized_image = pil_image.convert("L").resize((128, 128))
            
            # Generate multiple hash types for more robust comparison
            phash_value = imagehash.phash(standardized_image)
            dhash_value = imagehash.dhash(standardized_image)
            avg_hash_value = imagehash.average_hash(standardized_image)
            
            # Get face encoding for face recognition comparison (more accurate)
            rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_face)
            if not face_encodings:
                print("⚠️ Could not generate face encoding, skipping save.")
                return
            face_encoding = face_encodings[0]

            # Store current timestamp to prevent rapid duplicate saves
            current_time = system_time.time()
            
            # Check for duplicates using multiple methods
            is_duplicate = False
            closest_match = float('inf')
            closest_file = None
            
            for file in os.listdir(UNKNOWN_DIR):
                file_path = os.path.join(UNKNOWN_DIR, file)
                
                # Skip non-image files
                if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                try:
                    # Method 1: Multi-hash comparison
                    existing_img = Image.open(file_path).convert("L").resize((128, 128))
                    existing_phash = imagehash.phash(existing_img)
                    existing_dhash = imagehash.dhash(existing_img)
                    existing_avg_hash = imagehash.average_hash(existing_img)
                    
                    # Calculate combined hash difference (weighted average)
                    phash_diff = abs(phash_value - existing_phash)
                    dhash_diff = abs(dhash_value - existing_dhash)
                    avg_hash_diff = abs(avg_hash_value - existing_avg_hash)
                    
                    combined_diff = (phash_diff * 0.5) + (dhash_diff * 0.3) + (avg_hash_diff * 0.2)
                    
                    if combined_diff < closest_match:
                        closest_match = combined_diff
                        closest_file = file
                    
                    if combined_diff < HASH_SIMILARITY_THRESHOLD:
                        print(f"⚠️ Duplicate detected via hash (similarity: {combined_diff})")
                        is_duplicate = True
                        break
                    
                    
                    if HASH_SIMILARITY_THRESHOLD <= combined_diff <= HASH_SIMILARITY_THRESHOLD * 2:
                        try:
                            existing_face_img = cv2.imread(file_path)
                            existing_rgb = cv2.cvtColor(existing_face_img, cv2.COLOR_BGR2RGB)
                            existing_encodings = face_recognition.face_encodings(existing_rgb)
                            
                            if existing_encodings:
                                # Compare face encodings
                                face_distance = face_recognition.face_distance([existing_encodings[0]], face_encoding)[0]
                                
                                if face_distance < FACE_SIMILARITY_THRESHOLD:
                                    print(f"⚠️ Duplicate detected via face recognition (distance: {face_distance})")
                                    is_duplicate = True
                                    break
                        except Exception as e:
                            print(f"Error comparing face encodings: {e}")
                    
                except Exception as e:
                    print(f"Error processing existing image {file}: {e}")
                    continue

            # Check cooldown period for saving unknown faces
            last_save_time = getattr(self, 'last_unknown_save_time', 0)
            cooldown_period = self.settings.get("unknown_face_cooldown", "5")  # 5 seconds default
            
            if current_time - last_save_time < float(cooldown_period):
                print(f"⚠️ Cooldown period active, skipping save. ({current_time - last_save_time:.1f}s < {cooldown_period}s)")
                return

            # Save file if no duplicates found
            if not is_duplicate:
                file_path = os.path.join(UNKNOWN_DIR, f"unknown_{uuid.uuid4().hex[:8]}.jpg")
                pil_image.save(file_path)
                self.last_unknown_save_time = current_time
                
                print(f"✅ New unknown face saved: {file_path}")
                if closest_match != float('inf'):
                    print(f"   Closest match was {closest_file} with difference {closest_match}")
                
                # Check brightness & contrast before enhancement
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                avg_brightness = np.mean(gray)
                contrast = np.std(gray)

                if BRIGHTNESS_MIN < avg_brightness < BRIGHTNESS_MAX and contrast > CONTRAST_THRESHOLD:
                    print("📸 Image quality is good, skipping enhancement.")
                    final_path = file_path
                else:
                    enhanced_path = enhance_image(file_path)
                    if enhanced_path:
                        final_path = enhanced_path
                        print(f"📸 Enhanced & saved unknown face at {final_path}")
                    else:
                        final_path = file_path  # Fallback to original

                return final_path
            else:
                print("⚠️ Duplicate face not saved.")
                return None

        except Exception as e:
            print(f"❌ Error saving unknown face: {e}")
            return None
        
    def update_progress(self):
        """Simulates progress update while attendance is running."""
        current_value = self.progress_bar.value()
        if current_value < 100:
            self.progress_bar.setValue(current_value + 5)

    
    def load_known_faces(self):
        
        self.known_faces = []  # Clear previous encodings
        self.student_ids = []  

        # Ensure encoding directory exists
        encoding_dir = "student_encodings"
        if not os.path.exists(encoding_dir):
            print("❌ Student encodings directory not found.")
            return [], []

        try:
            # Find all encoding files
            encoding_files = [f for f in os.listdir(encoding_dir) if f.endswith('_encodings.pkl')]
            
            for encoding_file in encoding_files:
                try:
                    file_path = os.path.join(encoding_dir, encoding_file)
                    
                    # Extract student ID from filename
                    student_id = encoding_file.replace('student_', '').replace('_encodings.pkl', '')
                    
                    # Load encodings from pickle file
                    with open(file_path, 'rb') as f:
                        encodings = pickle.load(f)
                    
                    # Add each encoding and corresponding student ID
                    for encoding in encodings:
                        self.known_faces.append(encoding)
                        self.student_ids.append(student_id)
                    
                    print(f"✅ Loaded {len(encodings)} encodings for student {student_id}")
                
                except Exception as e:
                    print(f"❌ Error loading encoding file {encoding_file}: {e}")

            print(f"✅ Total loaded faces: {len(self.known_faces)}")
            return self.known_faces, self.student_ids

        except Exception as e:
            print(f"❌ Error in loading known faces: {e}")
            return [], []
    def update_table(self, student_id, name, status):
        """Updates the attendance table dynamically."""
        row = self.attendance_table.rowCount()
        self.attendance_table.insertRow(row)
        self.attendance_table.setItem(row, 0, QTableWidgetItem(student_id))
        self.attendance_table.setItem(row, 1, QTableWidgetItem(name))
        self.attendance_table.setItem(row, 2, QTableWidgetItem(status))

    def mark_attendance(self, student_id):
        """Marks attendance in the database with session information."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            today_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")

            # Check if already marked for this session
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE student_id = ? AND date = ? AND session_id = ?
            """, (student_id, today_date, self.session_id))
            
            if not cursor.fetchone():
                # Insert with session ID
                cursor.execute("""
                    INSERT INTO attendance 
                    (student_id, date, time, status, session_id) 
                    VALUES (?, ?, ?, 'Present', ?)
                """, (student_id, today_date, current_time, self.session_id))
                
                conn.commit()
                print(f"✅ Marked attendance for student {student_id} in session {self.session_id}")
            
            conn.close()
        except Exception as e:
            print(f"❌ Error marking attendance: {e}")


    def load_settings(self):
        """Loads settings from the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM settings")
        settings = dict(cursor.fetchall())
        conn.close()

        return settings if settings else {} 

    def apply_saved_settings(self):
        """Load and apply settings when the dashboard starts."""
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM settings")
        settings = dict(cursor.fetchall())
        conn.close()
        
        if self.settings.get("auto_start", "0") == "1":
            self.start_attendance()  # Function to begin attendance automatically


    def get_saved_dark_mode_setting(self):
        """Retrieve the saved dark mode setting from the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'dark_mode'")
        result = cursor.fetchone()
        conn.close()

        return result is not None and result[0] == "1"  # Convert result to Boolean


    
