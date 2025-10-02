#!/usr/bin/env python3
"""
User enrollment script for the AI Guard Agent.
Allows enrolling trusted users by capturing photos and generating face encodings.
"""

import os
import cv2
import time
import logging
from typing import List, Optional

from src.vision.face_detector import FaceDetector
from src.vision.face_recognizer import FaceRecognizer
from src.core.user_database import TrustedUserDatabase

class UserEnrollment:
    """Handles the enrollment process for trusted users"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.user_db = TrustedUserDatabase()
        
        # Enrollment settings
        self.min_photos = 3
        self.max_photos = 8
        self.min_face_quality = 0.7
        
    def capture_enrollment_photos(self, user_name: str) -> List[str]:
        """
        Capture multiple photos for user enrollment
        
        Args:
            user_name: Name of the user being enrolled
            
        Returns:
            List of captured photo filenames
        """
        print(f"\n👤 Enrolling user: {user_name}")
        print(f"📸 We need to capture {self.min_photos}-{self.max_photos} good quality photos")
        print("Instructions:")
        print("- Look directly at the camera")
        print("- Ensure good lighting")
        print("- Try different angles (slightly left, center, slightly right)")
        print("- Press SPACE to capture photo, 'q' to quit, 'r' to retake last photo")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not open camera")
        
        captured_photos = []
        photo_count = 0
        
        # Create photos directory if it doesn't exist
        photos_dir = os.path.join("data", "enrollment_photos", user_name.replace(" ", "_"))
        os.makedirs(photos_dir, exist_ok=True)
        
        try:
            while photo_count < self.max_photos:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detect faces in current frame
                detected_faces = self.face_detector.detect_faces(frame)
                
                # Draw face detection overlay
                display_frame = frame.copy()
                
                if detected_faces:
                    # Check face quality
                    for face in detected_faces:
                        is_good_quality, quality_metrics = self.face_recognizer.is_good_quality_face(
                            frame, face.location
                        )
                        
                        # Draw face box with quality indicator
                        top, right, bottom, left = face.location
                        color = (0, 255, 0) if is_good_quality else (0, 165, 255)  # Green if good, orange if poor
                        cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                        
                        # Quality indicator
                        quality_text = "Good Quality" if is_good_quality else "Poor Quality"
                        cv2.putText(display_frame, quality_text, (left, top - 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
                        # Face size info
                        size_text = f"Size: {quality_metrics.get('face_width', 0)}x{quality_metrics.get('face_height', 0)}"
                        cv2.putText(display_frame, size_text, (left, top - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                else:
                    cv2.putText(display_frame, "No face detected", (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Add instructions
                progress_text = f"Photos captured: {photo_count}/{self.max_photos} (min: {self.min_photos})"
                cv2.putText(display_frame, progress_text, (10, display_frame.shape[0] - 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                instruction_text = "SPACE: Capture | Q: Quit | R: Retake last"
                cv2.putText(display_frame, instruction_text, (10, display_frame.shape[0] - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if photo_count >= self.min_photos:
                    done_text = "Press ENTER when done (minimum photos captured)"
                    cv2.putText(display_frame, done_text, (10, display_frame.shape[0] - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow('User Enrollment - Photo Capture', display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):  # Space - capture photo
                    if detected_faces:
                        # Check if any face has good quality
                        good_faces = []
                        for face in detected_faces:
                            is_good, _ = self.face_recognizer.is_good_quality_face(frame, face.location)
                            if is_good:
                                good_faces.append(face)
                        
                        if good_faces:
                            # Save photo
                            timestamp = int(time.time())
                            photo_filename = f"{user_name.replace(' ', '_')}_{timestamp}_{photo_count + 1}.jpg"
                            photo_path = os.path.join(photos_dir, photo_filename)
                            
                            cv2.imwrite(photo_path, frame)
                            captured_photos.append(photo_path)
                            photo_count += 1
                            
                            print(f"📸 Captured photo {photo_count}: {photo_filename}")
                            
                            # Brief visual feedback
                            flash_frame = frame.copy()
                            cv2.rectangle(flash_frame, (0, 0), (frame.shape[1], frame.shape[0]), (255, 255, 255), 20)
                            cv2.imshow('User Enrollment - Photo Capture', flash_frame)
                            cv2.waitKey(200)
                        else:
                            print("⚠️  Poor quality face detected. Please improve lighting and try again.")
                    else:
                        print("⚠️  No face detected. Please position yourself in front of the camera.")
                
                elif key == ord('r') and captured_photos:  # R - retake last photo
                    last_photo = captured_photos.pop()
                    photo_count -= 1
                    try:
                        os.remove(last_photo)
                        print(f"🗑️  Removed last photo. Count: {photo_count}")
                    except OSError:
                        pass
                
                elif key == ord('q'):  # Q - quit
                    print("❌ Enrollment cancelled by user")
                    break
                
                elif key == 13 and photo_count >= self.min_photos:  # Enter - done (if minimum met)
                    print(f"✅ Photo capture completed with {photo_count} photos")
                    break
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        return captured_photos
    
    def process_enrollment_photos(self, photo_paths: List[str]) -> List:
        """
        Process captured photos to generate face encodings
        
        Args:
            photo_paths: List of photo file paths
            
        Returns:
            List of successfully generated face encodings
        """
        print(f"\n🔍 Processing {len(photo_paths)} photos...")
        
        face_encodings = []
        successful_photos = []
        
        for i, photo_path in enumerate(photo_paths):
            print(f"Processing photo {i + 1}/{len(photo_paths)}: {os.path.basename(photo_path)}")
            
            try:
                # Load image
                image = cv2.imread(photo_path)
                if image is None:
                    print(f"   ❌ Could not load photo")
                    continue
                
                # Generate face encoding
                encoding = self.face_recognizer.generate_face_encoding(image)
                
                if encoding is not None:
                    face_encodings.append(encoding)
                    successful_photos.append(photo_path)
                    print(f"   ✅ Face encoding generated successfully")
                else:
                    print(f"   ❌ Could not generate face encoding")
                    
            except Exception as e:
                print(f"   ❌ Error processing photo: {e}")
        
        print(f"\n📊 Successfully processed {len(face_encodings)} out of {len(photo_paths)} photos")
        return face_encodings
    
    def enroll_user(self, user_name: str, custom_user_id: str = None) -> bool:
        """
        Complete user enrollment process
        
        Args:
            user_name: Name of the user to enroll
            custom_user_id: Optional custom user ID
            
        Returns:
            True if enrollment successful, False otherwise
        """
        try:
            print(f"\n🎯 Starting enrollment for: {user_name}")
            
            # Check if user already exists
            existing_user = self.user_db.get_user_by_name(user_name)
            if existing_user:
                print(f"⚠️  User '{user_name}' already exists with ID: {existing_user['user_id']}")
                response = input("Do you want to add more photos to existing user? (y/n): ")
                if response.lower() != 'y':
                    return False
                
                # Add photos to existing user
                photo_paths = self.capture_enrollment_photos(user_name)
                if len(photo_paths) < 1:
                    print("❌ No photos captured")
                    return False
                
                face_encodings = self.process_enrollment_photos(photo_paths)
                if not face_encodings:
                    print("❌ No valid face encodings generated")
                    return False
                
                # Add encodings to existing user
                for encoding in face_encodings:
                    self.user_db.add_face_encoding(existing_user['user_id'], encoding)
                
                print(f"✅ Added {len(face_encodings)} new encodings to existing user")
                return True
            
            else:
                # New user enrollment
                photo_paths = self.capture_enrollment_photos(user_name)
                
                if len(photo_paths) < self.min_photos:
                    print(f"❌ Insufficient photos captured. Need at least {self.min_photos}, got {len(photo_paths)}")
                    return False
                
                face_encodings = self.process_enrollment_photos(photo_paths)
                
                if not face_encodings:
                    print("❌ No valid face encodings generated")
                    return False
                
                if len(face_encodings) < self.min_photos:
                    print(f"❌ Insufficient valid encodings. Need at least {self.min_photos}, got {len(face_encodings)}")
                    return False
                
                # Add user to database
                photo_filenames = [os.path.basename(path) for path in photo_paths]
                user_id = self.user_db.add_user(
                    name=user_name,
                    face_encodings=face_encodings,
                    photos_used=photo_filenames,
                    user_id=custom_user_id
                )
                
                print(f"✅ User enrolled successfully!")
                print(f"   User ID: {user_id}")
                print(f"   Name: {user_name}")
                print(f"   Photos: {len(photo_paths)}")
                print(f"   Valid encodings: {len(face_encodings)}")
                
                return True
                
        except Exception as e:
            print(f"❌ Enrollment failed: {e}")
            self.logger.error(f"Enrollment error for {user_name}: {e}")
            return False
    
    def list_enrolled_users(self):
        """Display list of enrolled users"""
        users = self.user_db.list_users()
        
        if not users:
            print("📝 No users enrolled yet")
            return
        
        print(f"\n📝 Enrolled Users ({len(users)}):")
        print("-" * 60)
        
        for user in users:
            print(f"ID: {user['user_id']}")
            print(f"Name: {user['name']}")
            print(f"Enrolled: {user['enrollment_date'][:10]}")  # Just the date part
            print(f"Trust Level: {user['trust_level']:.2f}")
            print(f"Encodings: {user['metadata'].get('num_encodings', 0)}")
            print(f"Last Seen: {user.get('last_seen', 'Never')[:10] if user.get('last_seen') else 'Never'}")
            print("-" * 60)

def main():
    """Main enrollment interface"""
    print("🔐 AI Guard Agent - User Enrollment System")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    enrollment = UserEnrollment()
    
    while True:
        print("\nOptions:")
        print("1. Enroll new user")
        print("2. List enrolled users")
        print("3. Show database statistics")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            user_name = input("Enter user name: ").strip()
            if user_name:
                success = enrollment.enroll_user(user_name)
                if success:
                    print("🎉 Enrollment completed successfully!")
                else:
                    print("💔 Enrollment failed!")
            else:
                print("❌ Invalid user name")
        
        elif choice == '2':
            enrollment.list_enrolled_users()
        
        elif choice == '3':
            stats = enrollment.user_db.get_database_stats()
            print("\n📊 Database Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()