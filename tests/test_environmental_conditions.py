"""
Lighting and Environment Testing

This script provides testing capabilities for various environmental conditions
including lighting variations, angles, and real-world scenarios.
"""

import sys
import os
import time
import cv2
import numpy as np
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.face_recognizer import FaceRecognizer
from src.core.user_database import TrustedUserDatabase

class EnvironmentalTestingFramework:
    """Framework for testing face recognition under various environmental conditions"""
    
    def __init__(self):
        # Initialize components
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.user_db = TrustedUserDatabase()
        
        # Results storage
        self.test_results = []
        self.results_dir = Path("tests/environmental_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("🌍 Environmental Testing Framework initialized")
    
    def capture_lighting_variations(self) -> None:
        """Interactive capture of images under different lighting conditions"""
        print("\n💡 Lighting Variation Capture")
        print("=" * 50)
        
        # Check for enrolled users
        users = self.user_db.list_users()
        if not users:
            print("❌ No users enrolled. Please enroll users first.")
            return
        
        lighting_conditions = [
            ("bright", "Position yourself near a bright light source"),
            ("normal", "Normal indoor lighting"),
            ("dim", "Dim lighting (turn off some lights)"),
            ("backlit", "Position yourself with light source behind you"),
            ("side_lit", "Light source from the side"),
            ("harsh_shadows", "Direct overhead lighting creating shadows"),
        ]
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return
        
        try:
            for user in users:
                user_name = user['name'].lower()
                lighting_dir = Path("data/lighting_tests") / f"user_{user_name}"
                lighting_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"\n👤 Testing lighting conditions for {user['name']}")
                
                for condition_name, instruction in lighting_conditions:
                    print(f"\n💡 {condition_name.upper()} LIGHTING")
                    print(f"   {instruction}")
                    print("   Press SPACE when ready, N to skip, Q to quit")
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            continue
                        
                        frame = cv2.flip(frame, 1)
                        
                        # Add overlay text
                        cv2.putText(frame, f"User: {user['name']}", 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Lighting: {condition_name}", 
                                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        cv2.putText(frame, instruction, 
                                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        cv2.putText(frame, "SPACE: Capture | N: Skip | Q: Quit", 
                                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        
                        # Show brightness indicators
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        brightness = np.mean(gray)
                        cv2.putText(frame, f"Brightness: {brightness:.1f}", 
                                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        cv2.imshow('Lighting Test Capture', frame)
                        
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord(' '):  # Capture
                            timestamp = int(time.time())
                            filename = f"{condition_name}_{timestamp}.jpg"
                            filepath = lighting_dir / filename
                            cv2.imwrite(str(filepath), frame)
                            print(f"   ✅ Captured: {filename} (brightness: {brightness:.1f})")
                            break
                        elif key == ord('n'):  # Skip
                            print(f"   ⏭️ Skipped: {condition_name}")
                            break
                        elif key == ord('q'):  # Quit
                            print("   👋 Capture session ended")
                            return
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
        print(f"\n✅ Lighting variation capture completed!")
    
    def test_lighting_robustness(self) -> Dict[str, Any]:
        """Test recognition accuracy under different lighting conditions"""
        print("\n💡 Testing Lighting Robustness...")
        
        lighting_dir = Path("data/lighting_tests")
        if not lighting_dir.exists():
            print(f"   ⚠️ Lighting test directory not found: {lighting_dir}")
            print("   Please run lighting variation capture first")
            return {"error": "No test data available"}
        
        results = {}
        overall_stats = {
            "total_tests": 0,
            "successful_detections": 0,
            "successful_recognitions": 0,
            "lighting_conditions": []
        }
        
        # Test each user's lighting variations
        for user_dir in lighting_dir.glob("user_*"):
            if not user_dir.is_dir():
                continue
            
            user_name = user_dir.name.replace("user_", "")
            print(f"   Testing lighting conditions for {user_name}...")
            
            user_results = {}
            
            for image_file in user_dir.glob("*.jpg"):
                condition_name = image_file.stem.split('_')[0]
                
                if condition_name not in user_results:
                    user_results[condition_name] = {
                        "tests": 0,
                        "detections": 0,
                        "recognitions": 0,
                        "avg_confidence": 0.0,
                        "confidences": []
                    }
                
                # Load and test image
                image = cv2.imread(str(image_file))
                if image is None:
                    continue
                
                overall_stats["total_tests"] += 1
                user_results[condition_name]["tests"] += 1
                
                # Test face detection
                faces = self.face_detector.detect_faces(image)
                if faces:
                    overall_stats["successful_detections"] += 1
                    user_results[condition_name]["detections"] += 1
                    
                    # Test recognition
                    face_encoding = self.face_recognizer.generate_face_encoding(image, faces[0].location)
                    if face_encoding is not None:
                        recognized_user, confidence = self.face_recognizer.recognize_face(face_encoding)
                        
                        if recognized_user and confidence >= 0.6:
                            overall_stats["successful_recognitions"] += 1
                            user_results[condition_name]["recognitions"] += 1
                            user_results[condition_name]["confidences"].append(confidence)
                
                print(f"     {image_file.name}: {'✅' if faces else '❌'} detection, "
                      f"{'✅' if faces and face_encoding is not None else '❌'} recognition")
            
            # Calculate averages for this user
            for condition, stats in user_results.items():
                if stats["confidences"]:
                    stats["avg_confidence"] = np.mean(stats["confidences"])
                stats["detection_rate"] = stats["detections"] / stats["tests"] if stats["tests"] > 0 else 0.0
                stats["recognition_rate"] = stats["recognitions"] / stats["tests"] if stats["tests"] > 0 else 0.0
            
            results[user_name] = user_results
        
        # Calculate overall statistics
        detection_rate = overall_stats["successful_detections"] / overall_stats["total_tests"] if overall_stats["total_tests"] > 0 else 0.0
        recognition_rate = overall_stats["successful_recognitions"] / overall_stats["total_tests"] if overall_stats["total_tests"] > 0 else 0.0
        
        # Print summary
        print(f"\n📊 Lighting Robustness Results:")
        print(f"   Total Tests: {overall_stats['total_tests']}")
        print(f"   Detection Rate: {detection_rate:.1%}")
        print(f"   Recognition Rate: {recognition_rate:.1%}")
        
        # Save results
        results_data = {
            "overall_stats": overall_stats,
            "detection_rate": detection_rate,
            "recognition_rate": recognition_rate,
            "user_results": results,
            "timestamp": time.time()
        }
        
        results_file = self.results_dir / f"lighting_robustness_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"   Results saved: {results_file}")
        
        return results_data
    
    def capture_angle_variations(self) -> None:
        """Capture images from different camera angles"""
        print("\n📐 Angle Variation Capture")
        print("=" * 40)
        
        users = self.user_db.list_users()
        if not users:
            print("❌ No users enrolled. Please enroll users first.")
            return
        
        angle_conditions = [
            ("front", "Look directly at camera"),
            ("left_15", "Turn head 15° to your left"),
            ("right_15", "Turn head 15° to your right"),
            ("left_30", "Turn head 30° to your left"),
            ("right_30", "Turn head 30° to your right"),
            ("up_15", "Tilt head up 15°"),
            ("down_15", "Tilt head down 15°"),
        ]
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return
        
        try:
            for user in users:
                user_name = user['name'].lower()
                angle_dir = Path("data/angle_tests") / f"user_{user_name}"
                angle_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"\n👤 Testing angle variations for {user['name']}")
                
                for condition_name, instruction in angle_conditions:
                    print(f"\n📐 {condition_name.upper()}")
                    print(f"   {instruction}")
                    print("   Press SPACE when ready, N to skip, Q to quit")
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            continue
                        
                        frame = cv2.flip(frame, 1)
                        
                        # Add overlay
                        cv2.putText(frame, f"User: {user['name']}", 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Angle: {condition_name}", 
                                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        cv2.putText(frame, instruction, 
                                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        cv2.imshow('Angle Test Capture', frame)
                        
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord(' '):
                            timestamp = int(time.time())
                            filename = f"{condition_name}_{timestamp}.jpg"
                            filepath = angle_dir / filename
                            cv2.imwrite(str(filepath), frame)
                            print(f"   ✅ Captured: {filename}")
                            break
                        elif key == ord('n'):
                            print(f"   ⏭️ Skipped: {condition_name}")
                            break
                        elif key == ord('q'):
                            return
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def test_distance_sensitivity(self) -> Dict[str, Any]:
        """Test recognition at different distances"""
        print("\n📏 Testing Distance Sensitivity...")
        
        print("   This test requires manual positioning at different distances")
        print("   Distances: Very Close (1 foot), Close (2 feet), Normal (3-4 feet), Far (6+ feet)")
        
        distance_conditions = [
            ("very_close", "Position very close to camera (~1 foot)"),
            ("close", "Position close to camera (~2 feet)"),
            ("normal", "Normal distance (~3-4 feet)"),
            ("far", "Position far from camera (6+ feet)"),
        ]
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return {"error": "Camera not available"}
        
        distance_results = {}
        
        try:
            for condition_name, instruction in distance_conditions:
                print(f"\n📏 Testing {condition_name} distance")
                print(f"   {instruction}")
                input("   Press Enter when positioned correctly...")
                
                # Capture multiple frames for testing
                test_frames = []
                print("   Capturing test frames...")
                
                for i in range(5):
                    ret, frame = cap.read()
                    if ret:
                        frame = cv2.flip(frame, 1)
                        test_frames.append(frame)
                        time.sleep(0.5)
                
                # Test each frame
                detections = 0
                recognitions = 0
                confidences = []
                
                for i, frame in enumerate(test_frames):
                    faces = self.face_detector.detect_faces(frame)
                    if faces:
                        detections += 1
                        
                        face_encoding = self.face_recognizer.generate_face_encoding(frame, faces[0].location)
                        if face_encoding is not None:
                            recognized_user, confidence = self.face_recognizer.recognize_face(face_encoding)
                            if recognized_user and confidence >= 0.6:
                                recognitions += 1
                                confidences.append(confidence)
                    
                    print(f"     Frame {i+1}: {'✅' if faces else '❌'} detection")
                
                distance_results[condition_name] = {
                    "detection_rate": detections / len(test_frames),
                    "recognition_rate": recognitions / len(test_frames),
                    "avg_confidence": np.mean(confidences) if confidences else 0.0,
                    "total_frames": len(test_frames)
                }
                
                print(f"   Results: {detections}/{len(test_frames)} detections, "
                      f"{recognitions}/{len(test_frames)} recognitions")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        # Save results
        results_file = self.results_dir / f"distance_sensitivity_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(distance_results, f, indent=2)
        
        print(f"\n📊 Distance Sensitivity Results saved: {results_file}")
        return distance_results
    
    def generate_environmental_report(self) -> None:
        """Generate comprehensive environmental testing report"""
        print("\n📋 Generating Environmental Testing Report...")
        
        report_data = {
            "test_timestamp": time.time(),
            "system_info": {
                "face_detector": "HOG-based detector",
                "face_recognizer": "dlib face_recognition",
                "enrolled_users": len(self.user_db.list_users())
            },
            "test_summary": {},
            "recommendations": []
        }
        
        # Load recent test results
        result_files = list(self.results_dir.glob("*.json"))
        
        if result_files:
            print("   Found test result files:")
            for file in result_files:
                print(f"     - {file.name}")
        else:
            print("   No test result files found")
        
        # Generate recommendations
        recommendations = [
            "🔍 Ensure adequate lighting for reliable face detection",
            "📐 Train users to face camera directly for best recognition",
            "📏 Maintain 3-4 feet distance from camera for optimal results",
            "⚡ Use performance optimization for real-time applications",
            "🔄 Regularly test system under various environmental conditions",
            "📊 Monitor recognition confidence scores for quality assessment"
        ]
        
        report_data["recommendations"] = recommendations
        
        # Save comprehensive report
        report_file = self.results_dir / f"environmental_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Environmental Testing Report:")
        print(f"   Report saved: {report_file}")
        print(f"\n💡 Key Recommendations:")
        for rec in recommendations:
            print(f"     {rec}")

def main():
    """Main function"""
    framework = EnvironmentalTestingFramework()
    
    print("🌍 Environmental Testing Framework")
    print("=" * 50)
    print("1. Capture lighting variations")
    print("2. Test lighting robustness")
    print("3. Capture angle variations")
    print("4. Test distance sensitivity")
    print("5. Generate environmental report")
    print("6. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            framework.capture_lighting_variations()
        elif choice == '2':
            framework.test_lighting_robustness()
        elif choice == '3':
            framework.capture_angle_variations()
        elif choice == '4':
            framework.test_distance_sensitivity()
        elif choice == '5':
            framework.generate_environmental_report()
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()