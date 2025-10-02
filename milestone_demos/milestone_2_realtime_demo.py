#!/usr/bin/env python3
"""
Real-time face recognition demo for the AI Guard Agent.
Tests the complete face recognition pipeline with live camera feed.
"""

import sys
import os
import cv2
import time
import logging
from typing import Dict, List, Optional

# # Add src directory to path
# root_dir = os.path.dirname(os.path.dirname(__file__))
# src_dir = os.path.join(root_dir, 'src')
# sys.path.insert(0, src_dir)

from src.vision.face_detector import FaceDetector
from src.vision.face_recognizer import FaceRecognizer
from src.core.user_database import TrustedUserDatabase

class RealTimeFaceRecognition:
    """Real-time face recognition system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.user_db = TrustedUserDatabase()
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Recognition settings
        self.recognition_threshold = 0.6
        self.min_confidence = 0.7
        self.frame_skip = 2  # Process every nth frame for better performance
        self.frame_count = 0
        
        # UI colors
        self.colors = {
            'trusted': (0, 255, 0),      # Green for trusted users
            'unknown': (0, 0, 255),      # Red for unknown faces
            'processing': (0, 165, 255), # Orange for processing
            'text': (255, 255, 255),     # White for text
            'background': (0, 0, 0)      # Black for backgrounds
        }
    
    def update_fps(self):
        """Update FPS calculation"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def draw_face_info(self, frame, face_location, user_info: Optional[Dict], confidence: float = 0.0):
        """
        Draw face detection and recognition information on frame
        
        Args:
            frame: Video frame
            face_location: Face bounding box (top, right, bottom, left)
            user_info: User information if recognized, None if unknown
            confidence: Recognition confidence score
        """
        top, right, bottom, left = face_location
        
        # Determine color and status based on recognition
        if user_info:
            color = self.colors['trusted']
            status = f"✓ {user_info['name']}"
            # Handle trust_level which is now a TrustLevel enum
            trust_level = user_info.get('trust_level', 'UNKNOWN')
            if hasattr(trust_level, 'name'):
                trust_str = trust_level.name
            else:
                trust_str = str(trust_level)
            detail = f"Trust: {trust_str}"
        else:
            color = self.colors['unknown']
            status = "⚠ Unknown Person"
            detail = f"Conf: {confidence:.2f}"
        
        # Draw face rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        
        # Draw status background
        status_bg_height = 60
        cv2.rectangle(frame, (left, top - status_bg_height), (right, top), color, -1)
        
        # Draw status text
        cv2.putText(frame, status, (left + 5, top - 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(frame, detail, (left + 5, top - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Draw confidence bar for unknown faces
        if not user_info and confidence > 0:
            bar_width = right - left
            bar_height = 5
            bar_fill = int((confidence / 1.0) * bar_width)
            
            # Background bar
            cv2.rectangle(frame, (left, bottom + 5), (right, bottom + 5 + bar_height), 
                         (50, 50, 50), -1)
            # Confidence bar
            cv2.rectangle(frame, (left, bottom + 5), (left + bar_fill, bottom + 5 + bar_height), 
                         color, -1)
    
    def draw_system_info(self, frame):
        """Draw system information overlay"""
        height, width = frame.shape[:2]
        
        # System info background
        info_height = 120
        cv2.rectangle(frame, (10, 10), (300, info_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (300, info_height), (100, 100, 100), 2)
        
        # System info text
        info_lines = [
            f"🎯 AI Guard Face Recognition",
            f"📊 FPS: {self.current_fps}",
            f"👥 Enrolled Users: {len(self.user_db.list_users())}",
            f"🔧 Recognition Threshold: {self.recognition_threshold:.2f}"
        ]
        
        for i, line in enumerate(info_lines):
            y_pos = 30 + (i * 20)
            cv2.putText(frame, line, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, self.colors['text'], 1)
        
        # Controls info
        controls_y = height - 80
        cv2.rectangle(frame, (10, controls_y), (400, height - 10), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, controls_y), (400, height - 10), (100, 100, 100), 2)
        
        control_lines = [
            "Controls: Q=Quit | SPACE=Pause | R=Reset Stats",
            "S=Screenshot | T=Adjust Threshold | F=Toggle Info"
        ]
        
        for i, line in enumerate(control_lines):
            y_pos = controls_y + 20 + (i * 15)
            cv2.putText(frame, line, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, self.colors['text'], 1)
    
    def recognize_faces_in_frame(self, frame):
        """
        Perform face recognition on a frame
        
        Args:
            frame: Input video frame
            
        Returns:
            List of tuples (face_location, user_info, confidence)
        """
        # Detect faces
        detected_faces = self.face_detector.detect_faces(frame)
        
        if not detected_faces:
            return []
        
        results = []
        
        for face in detected_faces:
            # Generate face encoding
            face_encoding = self.face_recognizer.generate_face_encoding(frame, face.location)
            
            if face_encoding is not None:
                # Try to recognize the face
                user_info, confidence = self.face_recognizer.recognize_face(face_encoding)
                
                # Check if recognition meets threshold
                if confidence >= self.recognition_threshold:
                    # Update last seen for trusted user
                    if user_info:
                        self.user_db.update_last_seen(user_info['user_id'])
                    
                    results.append((face.location, user_info, confidence))
                else:
                    # Unknown face
                    results.append((face.location, None, confidence))
            else:
                # Could not generate encoding
                results.append((face.location, None, 0.0))
        
        return results
    
    def run(self):
        """Run the real-time face recognition system"""
        print("🎯 Starting Real-time Face Recognition System")
        print("=" * 60)
        
        # Check if users are enrolled
        users = self.user_db.list_users()
        if not users:
            print("⚠️  No users enrolled yet!")
            print("📝 Please run enrollment/enroll_user.py first")
            return
        
        print(f"👥 Found {len(users)} enrolled users:")
        for user in users:
            print(f"   - {user['name']} (ID: {user['user_id']})")
        
        print(f"\n🎮 Starting camera... (Recognition threshold: {self.recognition_threshold:.2f})")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return
        
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        paused = False
        show_info = True
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        print("❌ Failed to read from camera")
                        break
                    
                    # Mirror the frame horizontally for more natural interaction
                    frame = cv2.flip(frame, 1)
                    
                    # Update FPS
                    self.update_fps()
                    
                    # Process frame (skip frames for performance)
                    if self.frame_count % self.frame_skip == 0:
                        recognition_results = self.recognize_faces_in_frame(frame)
                        
                        # Draw recognition results
                        for face_location, user_info, confidence in recognition_results:
                            self.draw_face_info(frame, face_location, user_info, confidence)
                    
                    self.frame_count += 1
                    
                    # Draw system info overlay
                    if show_info:
                        self.draw_system_info(frame)
                    
                    # Add pause indicator
                    if paused:
                        cv2.putText(frame, "PAUSED - Press SPACE to resume", 
                                   (frame.shape[1]//2 - 150, frame.shape[0]//2), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Display frame
                cv2.imshow('AI Guard - Real-time Face Recognition', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):  # Quit
                    print("👋 Shutting down...")
                    break
                
                elif key == ord(' '):  # Pause/Resume
                    paused = not paused
                    status = "paused" if paused else "resumed"
                    print(f"⏸️  System {status}")
                
                elif key == ord('r'):  # Reset stats
                    self.fps_counter = 0
                    self.fps_start_time = time.time()
                    self.frame_count = 0
                    print("📊 Statistics reset")
                
                elif key == ord('s'):  # Screenshot
                    timestamp = int(time.time())
                    screenshot_path = f"data/screenshots/recognition_{timestamp}.jpg"
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    cv2.imwrite(screenshot_path, frame)
                    print(f"📸 Screenshot saved: {screenshot_path}")
                
                elif key == ord('t'):  # Adjust threshold
                    print(f"\n🎚️  Current threshold: {self.recognition_threshold:.2f}")
                    try:
                        new_threshold = float(input("Enter new recognition threshold (0.0-1.0): "))
                        if 0.0 <= new_threshold <= 1.0:
                            self.recognition_threshold = new_threshold
                            print(f"✅ Threshold updated to {new_threshold:.2f}")
                        else:
                            print("❌ Invalid threshold. Must be between 0.0 and 1.0")
                    except ValueError:
                        print("❌ Invalid input. Please enter a number.")
                
                elif key == ord('f'):  # Toggle info display
                    show_info = not show_info
                    status = "shown" if show_info else "hidden"
                    print(f"🔧 Info overlay {status}")
        
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("🏁 Camera released and windows closed")
    
    def test_recognition_accuracy(self, test_duration: int = 30):
        """
        Test recognition accuracy over a specified duration
        
        Args:
            test_duration: Test duration in seconds
        """
        print(f"\n🧪 Starting {test_duration}s recognition accuracy test...")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera for testing")
            return
        
        start_time = time.time()
        total_detections = 0
        trusted_recognitions = 0
        unknown_detections = 0
        
        try:
            while time.time() - start_time < test_duration:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                frame = cv2.flip(frame, 1)
                
                # Process frame
                recognition_results = self.recognize_faces_in_frame(frame)
                
                for face_location, user_info, confidence in recognition_results:
                    total_detections += 1
                    
                    if user_info:
                        trusted_recognitions += 1
                    else:
                        unknown_detections += 1
                    
                    # Draw results
                    self.draw_face_info(frame, face_location, user_info, confidence)
                
                # Show test progress
                elapsed = time.time() - start_time
                remaining = test_duration - elapsed
                cv2.putText(frame, f"Testing... {remaining:.1f}s remaining", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                cv2.imshow('Recognition Accuracy Test', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        # Report results
        print(f"\n📊 Recognition Accuracy Test Results:")
        print(f"   Duration: {test_duration}s")
        print(f"   Total Detections: {total_detections}")
        print(f"   Trusted Recognitions: {trusted_recognitions}")
        print(f"   Unknown Detections: {unknown_detections}")
        
        if total_detections > 0:
            trusted_rate = (trusted_recognitions / total_detections) * 100
            unknown_rate = (unknown_detections / total_detections) * 100
            print(f"   Trusted Recognition Rate: {trusted_rate:.1f}%")
            print(f"   Unknown Detection Rate: {unknown_rate:.1f}%")

def main():
    """Main function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    recognition_system = RealTimeFaceRecognition()
    
    print("🤖 AI Guard Agent - Real-time Face Recognition")
    print("=" * 50)
    print("1. Start real-time recognition")
    print("2. Test recognition accuracy")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        recognition_system.run()
    elif choice == '2':
        duration = input("Enter test duration in seconds (default 30): ").strip()
        try:
            duration = int(duration) if duration else 30
            recognition_system.test_recognition_accuracy(duration)
        except ValueError:
            print("❌ Invalid duration, using default 30 seconds")
            recognition_system.test_recognition_accuracy(30)
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()