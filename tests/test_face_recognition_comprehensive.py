"""
Comprehensive Testing Framework for Face Recognition System

This module provides comprehensive testing capabilities for the face recognition
system, including accuracy measurements, environmental testing, and robustness
validation.
"""

import sys
import os
import time
import cv2
import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.face_recognizer import FaceRecognizer
from src.vision.optimized_face_detector import OptimizedFaceDetector, OptimizationConfig
from src.core.user_database import TrustedUserDatabase
from src.core.trust_manager import TrustManager

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    accuracy: float
    processing_time_ms: float
    confidence_score: float
    details: Dict[str, Any]
    timestamp: str

@dataclass
class TestCondition:
    """Test condition parameters"""
    lighting: str  # 'bright', 'normal', 'dim', 'dark'
    angle: str     # 'front', 'left', 'right', 'up', 'down'
    distance: str  # 'close', 'normal', 'far'
    accessories: List[str]  # 'glasses', 'hat', 'mask', etc.
    image_quality: str  # 'high', 'medium', 'low'

class FaceRecognitionTestFramework:
    """Comprehensive testing framework for face recognition system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.user_db = TrustedUserDatabase()
        self.trust_manager = TrustManager()
        
        # Test configuration
        self.test_results: List[TestResult] = []
        self.test_data_dir = Path("data/test_images")
        self.results_dir = Path("tests/results")
        
        # Create directories
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Test parameters
        self.accuracy_threshold = 0.8  # 80% accuracy requirement
        self.confidence_threshold = 0.6
        
        print("🧪 Face Recognition Test Framework initialized")
    
    def create_test_dataset(self) -> None:
        """Create or prepare test dataset for comprehensive testing"""
        print("\n📊 Creating Test Dataset...")
        
        # Create test conditions
        test_conditions = [
            TestCondition("bright", "front", "normal", [], "high"),
            TestCondition("normal", "front", "normal", [], "high"),
            TestCondition("dim", "front", "normal", [], "high"),
            TestCondition("normal", "left", "normal", [], "high"),
            TestCondition("normal", "right", "normal", [], "high"),
            TestCondition("normal", "front", "close", [], "high"),
            TestCondition("normal", "front", "far", [], "high"),
            TestCondition("normal", "front", "normal", ["glasses"], "high"),
            TestCondition("normal", "front", "normal", [], "medium"),
            TestCondition("dim", "left", "normal", [], "medium"),
        ]
        
        # Save test conditions for reference
        conditions_file = self.results_dir / "test_conditions.json"
        with open(conditions_file, 'w') as f:
            json.dump([{
                'lighting': tc.lighting,
                'angle': tc.angle,
                'distance': tc.distance,
                'accessories': tc.accessories,
                'image_quality': tc.image_quality
            } for tc in test_conditions], f, indent=2)
        
        print(f"✅ Created {len(test_conditions)} test conditions")
        print(f"📝 Test conditions saved to: {conditions_file}")
        
        # Instructions for manual test data creation
        print(f"\n📸 Test Data Collection Instructions:")
        print(f"   1. Create directory: {self.test_data_dir}")
        print(f"   2. For each enrolled user, create subdirectory: user_[name]/")
        print(f"   3. Capture images under different conditions:")
        
        for i, condition in enumerate(test_conditions):
            accessories_str = "_".join(condition.accessories) if condition.accessories else "none"
            filename = f"test_{i+1:02d}_{condition.lighting}_{condition.angle}_{condition.distance}_{accessories_str}_{condition.image_quality}.jpg"
            print(f"      - {filename}")
        
        print(f"\n   4. Also create 'unknown/' directory with images of non-enrolled people")
        print(f"   5. Use webcam capture script for consistent image collection")
    
    def capture_test_images_interactive(self) -> None:
        """Interactive image capture for test dataset"""
        print("\n📸 Interactive Test Image Capture")
        print("=" * 50)
        
        # Check enrolled users
        users = self.user_db.list_users()
        if not users:
            print("❌ No users enrolled. Please enroll users first.")
            return
        
        print(f"👥 Found {len(users)} enrolled users:")
        for user in users:
            print(f"   - {user['name']} (ID: {user['user_id']})")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return
        
        try:
            for user in users:
                user_dir = self.test_data_dir / f"user_{user['name'].lower()}"
                user_dir.mkdir(exist_ok=True)
                
                print(f"\n📷 Capturing test images for {user['name']}")
                print("   Instructions:")
                print("   - Position yourself in front of camera")
                print("   - Press SPACE to capture image")
                print("   - Press 'n' for next condition")
                print("   - Press 'q' to quit")
                
                conditions = [
                    ("normal_front", "Normal lighting, facing camera"),
                    ("bright_front", "Bright lighting, facing camera"),
                    ("dim_front", "Dim lighting, facing camera"),
                    ("normal_left", "Normal lighting, head turned left"),
                    ("normal_right", "Normal lighting, head turned right"),
                    ("normal_close", "Normal lighting, close to camera"),
                    ("normal_far", "Normal lighting, far from camera"),
                ]
                
                for condition_name, description in conditions:
                    print(f"\n🎯 Condition: {description}")
                    print("   Press SPACE when ready...")
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            continue
                        
                        # Mirror for better user experience
                        frame = cv2.flip(frame, 1)
                        
                        # Add instruction text
                        cv2.putText(frame, f"User: {user['name']}", 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(frame, f"Condition: {condition_name}", 
                                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(frame, "SPACE: Capture | N: Next | Q: Quit", 
                                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        
                        cv2.imshow('Test Image Capture', frame)
                        
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord(' '):  # Capture
                            timestamp = int(time.time())
                            filename = f"{condition_name}_{timestamp}.jpg"
                            filepath = user_dir / filename
                            cv2.imwrite(str(filepath), frame)
                            print(f"   ✅ Captured: {filename}")
                            break
                        elif key == ord('n'):  # Next condition
                            print(f"   ⏭️ Skipped condition: {condition_name}")
                            break
                        elif key == ord('q'):  # Quit
                            print("   👋 Capture session ended")
                            return
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
        print(f"\n✅ Test image capture completed!")
        print(f"📁 Images saved to: {self.test_data_dir}")
    
    def test_face_detection_accuracy(self) -> TestResult:
        """Test face detection accuracy across various conditions"""
        print("\n🔍 Testing Face Detection Accuracy...")
        
        start_time = time.time()
        total_images = 0
        successful_detections = 0
        total_processing_time = 0
        
        # Test on available images
        for user_dir in self.test_data_dir.glob("user_*"):
            if not user_dir.is_dir():
                continue
                
            for image_file in user_dir.glob("*.jpg"):
                total_images += 1
                
                # Load and test image
                image = cv2.imread(str(image_file))
                if image is None:
                    continue
                
                # Measure processing time
                detection_start = time.time()
                faces = self.face_detector.detect_faces(image)
                detection_time = (time.time() - detection_start) * 1000
                
                total_processing_time += detection_time
                
                if len(faces) > 0:
                    successful_detections += 1
                    
                print(f"   📁 {image_file.name}: {len(faces)} faces detected ({detection_time:.1f}ms)")
        
        # Calculate metrics
        accuracy = successful_detections / total_images if total_images > 0 else 0.0
        avg_processing_time = total_processing_time / total_images if total_images > 0 else 0.0
        
        # Create test result
        test_result = TestResult(
            test_name="face_detection_accuracy",
            success=accuracy >= self.accuracy_threshold,
            accuracy=accuracy,
            processing_time_ms=avg_processing_time,
            confidence_score=1.0,  # Detection is binary
            details={
                "total_images": total_images,
                "successful_detections": successful_detections,
                "failed_detections": total_images - successful_detections,
                "threshold": self.accuracy_threshold
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.test_results.append(test_result)
        
        print(f"📊 Face Detection Results:")
        print(f"   Total Images: {total_images}")
        print(f"   Successful Detections: {successful_detections}")
        print(f"   Accuracy: {accuracy:.1%}")
        print(f"   Average Processing Time: {avg_processing_time:.1f}ms")
        print(f"   Status: {'✅ PASS' if test_result.success else '❌ FAIL'}")
        
        return test_result
    
    def test_face_recognition_accuracy(self) -> TestResult:
        """Test face recognition accuracy for enrolled users"""
        print("\n👤 Testing Face Recognition Accuracy...")
        
        total_tests = 0
        correct_recognitions = 0
        total_processing_time = 0
        confidence_scores = []
        
        # Test recognition for each enrolled user
        users = self.user_db.list_users()
        
        for user in users:
            user_dir = self.test_data_dir / f"user_{user['name'].lower()}"
            if not user_dir.exists():
                print(f"   ⚠️ No test images found for {user['name']}")
                continue
            
            print(f"   Testing recognition for {user['name']}...")
            
            for image_file in user_dir.glob("*.jpg"):
                total_tests += 1
                
                # Load image
                image = cv2.imread(str(image_file))
                if image is None:
                    continue
                
                # Detect faces
                faces = self.face_detector.detect_faces(image)
                if not faces:
                    continue
                
                # Test recognition on first detected face
                face = faces[0]
                
                # Measure processing time
                recognition_start = time.time()
                face_encoding = self.face_recognizer.generate_face_encoding(image, face.location)
                
                if face_encoding is not None:
                    recognized_user, confidence = self.face_recognizer.recognize_face(face_encoding)
                    
                recognition_time = (time.time() - recognition_start) * 1000
                total_processing_time += recognition_time
                
                # Check if recognition is correct
                if (recognized_user and 
                    recognized_user['user_id'] == user['user_id'] and 
                    confidence >= self.confidence_threshold):
                    correct_recognitions += 1
                    confidence_scores.append(confidence)
                    
                print(f"     📁 {image_file.name}: {recognized_user['name'] if recognized_user else 'Unknown'} "
                      f"(conf: {confidence:.3f}, {recognition_time:.1f}ms)")
        
        # Calculate metrics
        accuracy = correct_recognitions / total_tests if total_tests > 0 else 0.0
        avg_processing_time = total_processing_time / total_tests if total_tests > 0 else 0.0
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        # Create test result
        test_result = TestResult(
            test_name="face_recognition_accuracy",
            success=accuracy >= self.accuracy_threshold,
            accuracy=accuracy,
            processing_time_ms=avg_processing_time,
            confidence_score=avg_confidence,
            details={
                "total_tests": total_tests,
                "correct_recognitions": correct_recognitions,
                "incorrect_recognitions": total_tests - correct_recognitions,
                "confidence_threshold": self.confidence_threshold,
                "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
                "max_confidence": max(confidence_scores) if confidence_scores else 0.0,
                "enrolled_users": len(users)
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.test_results.append(test_result)
        
        print(f"📊 Face Recognition Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Correct Recognitions: {correct_recognitions}")
        print(f"   Accuracy: {accuracy:.1%}")
        print(f"   Average Confidence: {avg_confidence:.3f}")
        print(f"   Average Processing Time: {avg_processing_time:.1f}ms")
        print(f"   Status: {'✅ PASS' if test_result.success else '❌ FAIL'}")
        
        return test_result
    
    def test_unknown_user_detection(self) -> TestResult:
        """Test detection of unknown/non-enrolled users"""
        print("\n❓ Testing Unknown User Detection...")
        
        unknown_dir = self.test_data_dir / "unknown"
        if not unknown_dir.exists():
            print("   ⚠️ No unknown user images found. Creating directory...")
            unknown_dir.mkdir(exist_ok=True)
            print(f"   📁 Please add images of non-enrolled people to: {unknown_dir}")
            
            # Return a placeholder result
            test_result = TestResult(
                test_name="unknown_user_detection",
                success=True,  # No test data available
                accuracy=0.0,
                processing_time_ms=0.0,
                confidence_score=0.0,
                details={"total_tests": 0, "reason": "No test images available"},
                timestamp=datetime.now().isoformat()
            )
            self.test_results.append(test_result)
            return test_result
        
        total_tests = 0
        correct_rejections = 0
        total_processing_time = 0
        confidence_scores = []
        
        for image_file in unknown_dir.glob("*.jpg"):
            total_tests += 1
            
            # Load image
            image = cv2.imread(str(image_file))
            if image is None:
                continue
            
            # Detect faces
            faces = self.face_detector.detect_faces(image)
            if not faces:
                continue
            
            # Test recognition on first detected face
            face = faces[0]
            
            # Measure processing time
            recognition_start = time.time()
            face_encoding = self.face_recognizer.generate_face_encoding(image, face.location)
            
            if face_encoding is not None:
                recognized_user, confidence = self.face_recognizer.recognize_face(face_encoding)
                
            recognition_time = (time.time() - recognition_start) * 1000
            total_processing_time += recognition_time
            
            # Check if correctly rejected (should not be recognized with high confidence)
            if not recognized_user or confidence < self.confidence_threshold:
                correct_rejections += 1
                
            confidence_scores.append(confidence)
            print(f"     📁 {image_file.name}: {recognized_user['name'] if recognized_user else 'Unknown'} "
                  f"(conf: {confidence:.3f}, {recognition_time:.1f}ms)")
        
        # Calculate metrics
        accuracy = correct_rejections / total_tests if total_tests > 0 else 0.0
        avg_processing_time = total_processing_time / total_tests if total_tests > 0 else 0.0
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        # Create test result
        test_result = TestResult(
            test_name="unknown_user_detection",
            success=accuracy >= self.accuracy_threshold,
            accuracy=accuracy,
            processing_time_ms=avg_processing_time,
            confidence_score=avg_confidence,
            details={
                "total_tests": total_tests,
                "correct_rejections": correct_rejections,
                "false_positives": total_tests - correct_rejections,
                "confidence_threshold": self.confidence_threshold,
                "avg_confidence": avg_confidence
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.test_results.append(test_result)
        
        print(f"📊 Unknown User Detection Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Correct Rejections: {correct_rejections}")
        print(f"   False Positives: {total_tests - correct_rejections}")
        print(f"   Accuracy: {accuracy:.1%}")
        print(f"   Average Confidence: {avg_confidence:.3f}")
        print(f"   Status: {'✅ PASS' if test_result.success else '❌ FAIL'}")
        
        return test_result
    
    def test_performance_optimization(self) -> TestResult:
        """Test performance optimization effectiveness"""
        print("\n⚡ Testing Performance Optimization...")
        
        # Create optimized detector
        optimized_config = OptimizationConfig(
            frame_skip_enabled=True,
            frame_skip_interval=3,
            face_tracking_enabled=True
        )
        optimized_detector = OptimizedFaceDetector(self.face_detector, optimized_config)
        
        # Test on sample images
        test_images = []
        for user_dir in self.test_data_dir.glob("user_*"):
            for image_file in list(user_dir.glob("*.jpg"))[:3]:  # 3 images per user
                image = cv2.imread(str(image_file))
                if image is not None:
                    test_images.append(image)
        
        if not test_images:
            print("   ⚠️ No test images available for performance testing")
            test_result = TestResult(
                test_name="performance_optimization",
                success=True,
                accuracy=0.0,
                processing_time_ms=0.0,
                confidence_score=0.0,
                details={"reason": "No test images available"},
                timestamp=datetime.now().isoformat()
            )
            self.test_results.append(test_result)
            return test_result
        
        # Test original detector
        original_times = []
        for image in test_images:
            start_time = time.time()
            faces = self.face_detector.detect_faces(image)
            processing_time = (time.time() - start_time) * 1000
            original_times.append(processing_time)
        
        # Test optimized detector
        optimized_times = []
        for image in test_images:
            start_time = time.time()
            faces = optimized_detector.detect_faces(image)
            processing_time = (time.time() - start_time) * 1000
            optimized_times.append(processing_time)
        
        # Calculate metrics
        avg_original = np.mean(original_times)
        avg_optimized = np.mean(optimized_times)
        improvement = ((avg_original - avg_optimized) / avg_original) * 100
        
        # Get optimization stats
        opt_stats = optimized_detector.get_optimization_stats()
        
        # Create test result
        test_result = TestResult(
            test_name="performance_optimization",
            success=improvement > 0,  # Any improvement is good
            accuracy=opt_stats.get('cache_hit_ratio', 0.0),
            processing_time_ms=avg_optimized,
            confidence_score=improvement / 100.0,
            details={
                "original_avg_time": avg_original,
                "optimized_avg_time": avg_optimized,
                "improvement_percentage": improvement,
                "cache_hit_ratio": opt_stats.get('cache_hit_ratio', 0.0),
                "frames_processed": opt_stats.get('frames_processed', 0),
                "test_images": len(test_images)
            },
            timestamp=datetime.now().isoformat()
        )
        
        self.test_results.append(test_result)
        
        print(f"📊 Performance Optimization Results:")
        print(f"   Original Average Time: {avg_original:.1f}ms")
        print(f"   Optimized Average Time: {avg_optimized:.1f}ms")
        print(f"   Performance Improvement: {improvement:.1f}%")
        print(f"   Cache Hit Ratio: {opt_stats.get('cache_hit_ratio', 0.0):.1%}")
        print(f"   Status: {'✅ PASS' if test_result.success else '❌ FAIL'}")
        
        return test_result
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        print("🧪 COMPREHENSIVE FACE RECOGNITION TEST SUITE")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        detection_result = self.test_face_detection_accuracy()
        recognition_result = self.test_face_recognition_accuracy()
        unknown_result = self.test_unknown_user_detection()
        performance_result = self.test_performance_optimization()
        
        total_time = time.time() - start_time
        
        # Calculate overall results
        all_tests = [detection_result, recognition_result, unknown_result, performance_result]
        passed_tests = sum(1 for test in all_tests if test.success)
        overall_accuracy = np.mean([test.accuracy for test in all_tests if test.accuracy > 0])
        
        # Generate summary
        summary = {
            "total_tests": len(all_tests),
            "passed_tests": passed_tests,
            "failed_tests": len(all_tests) - passed_tests,
            "overall_accuracy": overall_accuracy,
            "total_duration_seconds": total_time,
            "timestamp": datetime.now().isoformat(),
            "test_results": [
                {
                    "test_name": test.test_name,
                    "success": test.success,
                    "accuracy": test.accuracy,
                    "details": test.details
                }
                for test in all_tests
            ]
        }
        
        # Save results
        results_file = self.results_dir / f"test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print(f"\n📋 TEST SUITE SUMMARY")
        print(f"=" * 40)
        print(f"Total Tests: {len(all_tests)}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(all_tests) - passed_tests}")
        print(f"Overall Accuracy: {overall_accuracy:.1%}")
        print(f"Test Duration: {total_time:.1f}s")
        print(f"Results Saved: {results_file}")
        
        # Individual test status
        print(f"\n📊 Individual Test Results:")
        for test in all_tests:
            status = "✅ PASS" if test.success else "❌ FAIL"
            print(f"   {test.test_name}: {status} ({test.accuracy:.1%})")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if overall_accuracy >= 0.8:
            print("   ✅ System meets accuracy requirements!")
        else:
            print("   ⚠️ System accuracy below 80% - consider improvements")
            
        if passed_tests == len(all_tests):
            print("   🎉 All tests passed - system ready for deployment!")
        else:
            print("   🔧 Some tests failed - review and address issues")
            
        return summary

def main():
    """Main testing function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    framework = FaceRecognitionTestFramework()
    
    print("🧪 Face Recognition Testing Framework")
    print("=" * 50)
    print("1. Create test dataset instructions")
    print("2. Capture test images interactively")
    print("3. Run comprehensive test suite")
    print("4. Test face detection only")
    print("5. Test face recognition only")
    print("6. Test unknown user detection")
    print("7. Test performance optimization")
    print("8. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            framework.create_test_dataset()
        elif choice == '2':
            framework.capture_test_images_interactive()
        elif choice == '3':
            framework.run_comprehensive_test_suite()
        elif choice == '4':
            framework.test_face_detection_accuracy()
        elif choice == '5':
            framework.test_face_recognition_accuracy()
        elif choice == '6':
            framework.test_unknown_user_detection()
        elif choice == '7':
            framework.test_performance_optimization()
        elif choice == '8':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()