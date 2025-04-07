import sqlite3
import pickle
import face_recognition
import cv2

TEST_IMAGE_PATH = "test_images/test_face_1.jpg"  # Change this to an image from your test set

def test_attendance():
    """Checks if a test image matches a registered student"""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute("SELECT student_id, face_encoding FROM students")
    results = cursor.fetchall()

    # Load the test image
    test_image = face_recognition.load_image_file(TEST_IMAGE_PATH)
    test_encodings = face_recognition.face_encodings(test_image)

    if not test_encodings:
        print("❌ No face detected in the test image!")
        return

    test_encoding = test_encodings[0]

    for student_id, encoding_blob in results:
        known_encodings = pickle.loads(encoding_blob)  # Load stored encodings

        matches = face_recognition.compare_faces(known_encodings, test_encoding, tolerance=0.55)
        if True in matches:
            print(f"✅ Match found! Student ID: {student_id} - Attendance Marked!")
            return

    print("❌ No match found in the database.")

if __name__ == "__main__":
    test_attendance()
