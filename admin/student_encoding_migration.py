import os
import sqlite3
import pickle
import face_recognition
import numpy as np
from typing import List, Optional

class StudentEncodingMigrator:
    """
    Helps migrate existing student records to the new encoding storage system
    """
    ENCODING_DIR = "student_encodings"
    
    def __init__(self, db_path="attendance.db"):
        """
        Initialize migration process
        
        Args:
            db_path (str): Path to the SQLite database
        """
        # Ensure encoding directory exists
        if not os.path.exists(self.ENCODING_DIR):
            os.makedirs(self.ENCODING_DIR)
        
        self.db_path = db_path
        self._prepare_database()
    
    def _prepare_database(self):
        """
        Prepare the database by adding necessary columns if they don't exist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Safely add columns if they don't exist
            cursor.execute("PRAGMA table_info(students)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Check and add face_encoding column
            if 'face_encoding' not in columns:
                cursor.execute("""
                    ALTER TABLE students 
                    ADD COLUMN face_encoding BLOB
                """)
            
            # Check and add face_encoding_path column
            if 'face_encoding_path' not in columns:
                cursor.execute("""
                    ALTER TABLE students 
                    ADD COLUMN face_encoding_path TEXT
                """)
            
            conn.commit()
            print("Database columns verified/updated successfully.")
        
        except sqlite3.OperationalError as e:
            print(f"Database preparation warning: {e}")
        
        finally:
            conn.close()
    
    def generate_new_encodings(self, image_path: str) -> Optional[List[List[float]]]:
        """
        Generate augmented face encodings for a given image
        
        Args:
            image_path (str): Path to the student's image
        
        Returns:
            List of face encodings or None if no face detected
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Detect faces
            face_locations = face_recognition.face_locations(image)
            
            # No faces detected
            if not face_locations:
                print(f"❌ No face detected in image: {image_path}")
                return None
            
            # Multiple faces detected
            if len(face_locations) > 1:
                print(f"⚠️ Multiple faces detected in image: {image_path}")
                return None
            
            # Generate encodings with augmentations
            augmented_encodings = []
            
            # Original encoding
            original_encodings = face_recognition.face_encodings(image, face_locations)
            if not original_encodings:
                print(f"❌ Could not generate encoding for: {image_path}")
                return None
            
            augmented_encodings.append(original_encodings[0])
            
            # Simplified augmentation techniques
            augmentations = [
                # Slightly darker
                lambda img: np.clip(img * 0.9, 0, 255).astype(np.uint8),
                # Slightly brighter
                lambda img: np.clip(img * 1.1, 0, 255).astype(np.uint8)
            ]
            
            for augment in augmentations:
                try:
                    # Apply augmentation
                    aug_image = augment(image)
                    
                    # Generate encoding with locations
                    aug_encodings = face_recognition.face_encodings(aug_image, face_locations)
                    
                    if aug_encodings:
                        augmented_encodings.append(aug_encodings[0])
                except Exception as e:
                    print(f"⚠️ Augmentation error: {e}")
            
            return augmented_encodings
        
        except Exception as e:
            print(f"❌ Error processing image {image_path}: {e}")
            return None
    
    def save_student_encodings(self, student_id: str, encodings: List[List[float]]) -> bool:
        
        
        try:
            # Sanitize student ID for filename
            sanitized_id = student_id.replace('/', '_')
            encoding_path = os.path.join(
                self.ENCODING_DIR, 
                f"student_{sanitized_id}_encodings.pkl"
            )
            
            # Save encodings to pickle file
            with open(encoding_path, 'wb') as f:
                pickle.dump(encodings, f)
            
            # Convert to blob for database storage
            encoding_blob = pickle.dumps(encodings)
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE students 
                SET face_encoding = ?, face_encoding_path = ? 
                WHERE student_id = ?
            """, (encoding_blob, encoding_path, student_id))
            conn.commit()
            conn.close()
            
            print(f"✅ Saved {len(encodings)} encodings for student {student_id}")
            return True
        
        except Exception as e:
            print(f"❌ Error saving encodings for student {student_id}: {e}")
            return False
    
    def migrate_all_students(self, dry_run: bool = False) -> dict:
        """
        Migrate all existing students to new encoding system
        
        Args:
            dry_run (bool): If True, only simulate migration without making changes
        
        Returns:
            dict: Migration statistics
        """
        stats = {
            "total_students": 0,
            "migrated_successfully": 0,
            "migration_failed": 0,
            "no_face_detected": 0
        }
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query all students with image paths
            cursor.execute("SELECT student_id, image_path FROM students WHERE image_path IS NOT NULL")
            students = cursor.fetchall()
            
            stats["total_students"] = len(students)
            
            # Process each student
            for student_id, image_path in students:
                # Check image exists
                if not os.path.exists(image_path):
                    print(f"⚠️ Image not found for student {student_id}: {image_path}")
                    stats["migration_failed"] += 1
                    continue
                
                # Dry run - just simulate
                if dry_run:
                    print(f"Would migrate student {student_id} from {image_path}")
                    stats["migrated_successfully"] += 1
                    continue
                
                # Generate new encodings
                encodings = self.generate_new_encodings(image_path)
                
                if not encodings:
                    stats["no_face_detected"] += 1
                    continue
                
                # Save encodings
                if self.save_student_encodings(student_id, encodings):
                    stats["migrated_successfully"] += 1
                else:
                    stats["migration_failed"] += 1
            
            conn.close()
            return stats
        
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return stats
    
    def print_migration_report(self, stats: dict):
        """
        Print a detailed migration report
        
        Args:
            stats (dict): Migration statistics
        """
        print("\n===== MIGRATION REPORT =====")
        print(f"Total Students:           {stats['total_students']}")
        print(f"Successfully Migrated:    {stats['migrated_successfully']}")
        print(f"Migration Failed:         {stats['migration_failed']}")
        print(f"No Face Detected:         {stats['no_face_detected']}")
        print(f"Migration Success Rate:   {stats['migrated_successfully'] / stats['total_students'] * 100:.2f}%")
        print("============================")

# Usage example
def run_migration():
    migrator = StudentEncodingMigrator()
    
    # Perform a dry run first to check potential issues
    print("Performing Dry Run...")
    dry_run_stats = migrator.migrate_all_students(dry_run=True)
    migrator.print_migration_report(dry_run_stats)
    
    # Confirm migration
    confirm = input("\nDo you want to proceed with actual migration? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        print("\nPerforming Actual Migration...")
        migration_stats = migrator.migrate_all_students()
        migrator.print_migration_report(migration_stats)
    else:
        print("Migration cancelled.")

# Run the migration
if __name__ == "__main__":
    run_migration()