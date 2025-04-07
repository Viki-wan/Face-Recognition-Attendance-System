import os
import cv2
import sqlite3
import pickle
import face_recognition
import numpy as np
from PIL import Image

# Directories for test and student images
TEST_IMAGE_DIR = "test_images"
STUDENT_IMAGE_DIR = "student_images"

# Ensure directories exist
os.makedirs(TEST_IMAGE_DIR, exist_ok=True)
os.makedirs(STUDENT_IMAGE_DIR, exist_ok=True)

def resize_image(image_path, output_size=(400, 400)):
    """Resize image while keeping aspect ratio, adding padding if necessary."""
    try:
        image = Image.open(image_path)
        image.thumbnail(output_size, Image.Resampling.LANCZOS)  # Maintain aspect ratio

        # Create a blank white square
        new_image = Image.new("RGB", output_size, (255, 255, 255))
        new_image.paste(image, ((output_size[0] - image.size[0]) // 2, (output_size[1] - image.size[1]) // 2))

        resized_path = image_path.replace(".jpg", "_resized.jpg")
        new_image.save(resized_path, "JPEG")

        return resized_path
    except Exception as e:
        print(f"❌ Error resizing image {image_path}: {e}")
        return image_path  # Return original if resizing fails

def create_test_students(num_students=5):
    """Create artificial student records for testing using real images and face encodings."""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # Clear existing test students
    cursor.execute("DELETE FROM students WHERE student_id LIKE 'TEST%'")
    conn.commit()

    created_count = 0  # Track how many students were successfully created

    for i in range(num_students):
        student_id = f"TEST{i+1:03d}"
        name = f"Test Student {i+1}"
        test_image_path = os.path.join(TEST_IMAGE_DIR, f"test_face_{i+1}.jpg")

        # Check if test image exists
        if not os.path.exists(test_image_path):
            print(f"❌ Missing test image: {test_image_path} (Skipping this student)")
            continue  # Skip this student if no image is available

        # Resize image before processing
        resized_image_path = resize_image(test_image_path)

        # Load the resized image
        image = face_recognition.load_image_file(resized_image_path)

        # Extract face encodings
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            print(f"⚠️ No face detected in {resized_image_path} (Skipping this student)")
            continue  # Skip if no face found

        # Save multiple encodings for robustness
        augmented_encodings = [
            encodings[0],
            encodings[0] + np.random.normal(0, 0.05, size=(128,))  # Slight variation
        ]
        augmented_encodings[1] = augmented_encodings[1] / np.linalg.norm(augmented_encodings[1])

        # Serialize encodings
        encoding_blob = pickle.dumps(augmented_encodings)

        # Save the image in student_images/
        student_image_path = os.path.join(STUDENT_IMAGE_DIR, f"{student_id}.jpg")
        cv2.imwrite(student_image_path, cv2.imread(resized_image_path))

        # Insert student into database
        cursor.execute("""
            INSERT INTO students (name, student_id, image_path, image_hash, face_encoding)
            VALUES (?, ?, ?, ?, ?)
        """, (name, student_id, student_image_path, "testimagehash", pickle.dumps(augmented_encodings)))

        created_count += 1

    conn.commit()
    conn.close()

    print(f"✅ Created {created_count} test students")

if __name__ == "__main__":
    create_test_students()
