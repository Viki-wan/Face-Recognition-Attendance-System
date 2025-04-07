import sys
import cv2
import numpy as np
from admin.preview_window import PreviewWindow
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer

class WebcamWindow(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("📸 Capture Photo")
        self.setGeometry(400, 200, 500, 500)
        self.setStyleSheet(QApplication.instance().styleSheet())

        # Initialize camera with error handling
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Failed to open camera. Please check your webcam.")
            self.close()
            return
            
        self.captured_frame = None

        # Layout
        layout = QVBoxLayout()

        # Live camera feed
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(450, 350)
        layout.addWidget(self.image_label)

        # Face Alignment Indicator
        self.status_label = QLabel("🔍 Align your face within the box")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Capture Button
        self.capture_button = QPushButton("📸 Capture")
        self.capture_button.clicked.connect(self.capture_photo)
        layout.addWidget(self.capture_button)

        self.setLayout(layout)

        # Timer for real-time webcam updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)  # Update every 50ms

    def update_frame(self):
        """Continuously updates the webcam feed with real-time face detection."""
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.setText("⚠️ Camera error! Check connection.")
            return

        # Make a copy to avoid modifying the original
        display_frame = frame.copy()
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        if len(faces) == 0:
            self.status_label.setText("⚠️ No face detected! Adjust your position.")
        elif len(faces) > 1:
            self.status_label.setText("⚠️ Multiple faces detected! Only one person should be in frame.")
        else:
            self.status_label.setText("✅ Face detected. Stay still and capture.")
            
            # Draw face guide rectangle
            x, y, w, h = faces[0]
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green rectangle

        # Convert OpenCV frame to Qt format for display
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.image_label.setPixmap(QPixmap.fromImage(q_img))

    def capture_photo(self):
        """Capture a photo with validation checks."""
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.warning(self, "Error", "Failed to capture image.")
            return

        # Make a copy of the frame to avoid modification issues
        captured = frame.copy()
        gray = cv2.cvtColor(captured, cv2.COLOR_BGR2GRAY)

        # Image quality checks
        avg_brightness = gray.mean()
        if avg_brightness < 40:
            QMessageBox.warning(self, "⚠️ Low Light", "Photo is too dark. Try again in better lighting.")
            return

        std_dev = gray.std()
        if std_dev < 20:
            QMessageBox.warning(self, "⚠️ Invalid Photo", "Image lacks detail. Please retake.")
            return

        # Face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        if len(faces) == 0:
            QMessageBox.warning(self, "⚠️ No Face Detected", "Please ensure your face is inside the frame.")
            return

        if len(faces) > 1:
            QMessageBox.warning(self, "⚠️ Multiple Faces", "Please ensure only one person is in the frame.")
            return

        # Store captured frame and show preview
        self.captured_frame = captured.copy()  # Important: make a copy!
        self.preview_window = PreviewWindow(self.captured_frame, self.parent_window)
        self.preview_window.show()

        # Close the webcam and open preview
        self.timer.stop()
        self.cap.release()
        self.close()

    def closeEvent(self, event):
        """Ensure the camera is released properly when window is closed."""
        self.timer.stop()
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        event.accept()