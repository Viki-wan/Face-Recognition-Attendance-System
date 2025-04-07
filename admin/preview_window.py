import cv2
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class PreviewWindow(QWidget):
    def __init__(self, frame, parent_window):
        super().__init__()
        self.frame = frame
        self.parent_window = parent_window
        self.temp_image_path = "temp_preview.jpg"

        self.setWindowTitle("📷 Photo Preview")
        self.setGeometry(300, 200, 420, 460)

        layout = QVBoxLayout()

        # 🔹 **Image Display**
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # 🔹 **Convert OpenCV Frame to Displayable Image**
        cv2.imwrite(self.temp_image_path, self.frame)
        self.update_image_display(self.temp_image_path)

        # 🔹 **Buttons**
        button_layout = QVBoxLayout()
        self.keep_button = QPushButton("✅ Keep", self)
        self.retake_button = QPushButton("🔄 Retake", self)

        button_layout.addWidget(self.keep_button)
        button_layout.addWidget(self.retake_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # ✅ **Button Connections**
        self.keep_button.clicked.connect(self.keep_photo)
        self.retake_button.clicked.connect(self.retake_photo)

    def update_image_display(self, img_path):
        """Loads and scales the captured image for display."""
        pixmap = QPixmap(img_path)
        scaled_pixmap = pixmap.scaled(380, 380, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
    
    def keep_photo(self):
        """Saves the photo and closes the preview."""
        cv2.destroyAllWindows()  # ✅ Close lingering OpenCV windows
        self.parent_window.save_photo(self.frame)
        self.close()


    def retake_photo(self):
        """Reopens the webcam for a new capture."""
        self.cleanup_temp_image()
        self.parent_window.open_webcam()
        self.close()

    def cleanup_temp_image(self):
        """Removes the temporary preview image file."""
        if os.path.exists(self.temp_image_path):
            os.remove(self.temp_image_path)
            print(f"🗑️ Deleted temporary preview image: {self.temp_image_path}")
