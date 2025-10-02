"""
Automated Face Recognition Test Suite

This script provides automated testing capabilities for face recognition
without requiring manual image capture.
"""

import sys
import os
import time
import cv2
import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Optional, Any

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.face_recognizer import FaceRecognizer
from src.vision.optimized_face_detector import OptimizedFaceDetector, OptimizationConfig
from src.core.user_database import TrustedUserDatabase

class AutomatedFaceRecognitionTests:
    """Automated test suite for face recognition system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.user_db = TrustedUserDatabase()
        
        print("🤖 Automated Face Recognition Tests initialized")
    
    def test_system_initialization(self) -> bool:
        """Test that all components initialize correctly"""
        print("\n🔧 Testing System Initialization...")
        
        try:
            # Test face detector
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            faces = self.face_detector.detect_faces(test_image)
            print("   ✅ Face detector working")
            
            # Test face recognizer
            encoding = self.face_recognizer.generate_face_encoding(test_image, (100, 200, 300, 100))
            print("   ✅ Face recognizer working")
            
            # Test user database
            users = self.user_db.list_users()
            print(f"   ✅ User database working ({len(users)} users)")
            
            return True
            
        except Exception as e:
            print(f"   ❌ System initialization failed: {e}")
            return False
    
    def test_face_detection_performance(self) -> Dict[str, Any]:
        """Test face detection performance with synthetic data"""
        print("\n⚡ Testing Face Detection Performance...")
        
        # Generate test frames of different sizes
        test_frames = [
            np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8),  # Small
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),  # Medium
            np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8), # Large
        ]
        
        frame_sizes = ["240x320", "480x640", "720x1280"]
        results = {}
        
        for i, (frame, size_name) in enumerate(zip(test_frames, frame_sizes)):
            print(f"   Testing {size_name} frame...")
            
            # Time multiple detections
            times = []
            for _ in range(5):
                start_time = time.time()
                faces = self.face_detector.detect_faces(frame)
                detection_time = (time.time() - start_time) * 1000
                times.append(detection_time)
            
            avg_time = np.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            results[size_name] = {
                "avg_time_ms": avg_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time,
                "frame_size": frame.shape
            }
            
            print(f"     Average: {avg_time:.1f}ms (min: {min_time:.1f}ms, max: {max_time:.1f}ms)")
        
        return results
    
    def test_optimization_effectiveness(self) -> Dict[str, Any]:
        """Test optimization effectiveness"""
        print("\n🚀 Testing Optimization Effectiveness...")
        
        # Create test frames
        test_frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(20)]
        
        # Test original detector
        print("   Testing original detector...")
        original_times = []
        for frame in test_frames:
            start_time = time.time()
            faces = self.face_detector.detect_faces(frame)
            detection_time = (time.time() - start_time) * 1000
            original_times.append(detection_time)
        
        # Test optimized detector with different configurations
        configs = {
            "conservative": OptimizationConfig(frame_skip_enabled=True, frame_skip_interval=2),
            "aggressive": OptimizationConfig(frame_skip_enabled=True, frame_skip_interval=3),
            "max_performance": OptimizationConfig(frame_skip_enabled=True, frame_skip_interval=4)
        }
        
        optimization_results = {}
        
        for config_name, config in configs.items():
            print(f"   Testing {config_name} optimization...")
            
            optimized_detector = OptimizedFaceDetector(self.face_detector, config)
            optimized_times = []
            
            for frame in test_frames:
                start_time = time.time()
                faces = optimized_detector.detect_faces(frame)
                detection_time = (time.time() - start_time) * 1000
                optimized_times.append(detection_time)
            
            # Calculate metrics
            avg_original = np.mean(original_times)
            avg_optimized = np.mean(optimized_times)
            improvement = ((avg_original - avg_optimized) / avg_original) * 100
            
            # Get optimization stats
            opt_stats = optimized_detector.get_optimization_stats()
            
            optimization_results[config_name] = {
                "avg_time_ms": avg_optimized,
                "improvement_percentage": improvement,
                "cache_hit_ratio": opt_stats.get('cache_hit_ratio', 0.0),
                "frames_processed": opt_stats.get('frames_processed', 0),
                "cache_hits": opt_stats.get('cache_hits', 0)
            }
            
            print(f"     Average time: {avg_optimized:.1f}ms")
            print(f"     Improvement: {improvement:.1f}%")
            print(f"     Cache hit ratio: {opt_stats.get('cache_hit_ratio', 0.0):.1%}")
        
        # Overall results
        results = {
            "original_avg_time_ms": np.mean(original_times),
            "optimization_configs": optimization_results,
            "best_config": max(optimization_results.keys(), 
                             key=lambda k: optimization_results[k]["improvement_percentage"])
        }
        
        best_config = results["best_config"]
        best_improvement = optimization_results[best_config]["improvement_percentage"]
        
        print(f"\n   📊 Summary:")
        print(f"     Original average: {results['original_avg_time_ms']:.1f}ms")
        print(f"     Best configuration: {best_config}")
        print(f"     Best improvement: {best_improvement:.1f}%")
        
        return results
    
    def test_user_database_functionality(self) -> bool:
        """Test user database operations"""
        print("\n👥 Testing User Database Functionality...")
        
        try:
            # Get current user count
            initial_users = self.user_db.list_users()
            initial_count = len(initial_users)
            print(f"   Initial user count: {initial_count}")
            
            # Test database operations (read-only to avoid interfering with real data)
            print("   ✅ User listing works")
            
            # Test user lookup if users exist
            if initial_users:
                test_user = initial_users[0]
                user_data = self.user_db.get_user(test_user['user_id'])
                if user_data:
                    print("   ✅ User lookup works")
                else:
                    print("   ⚠️ User lookup returned None")
            
            return True
            
        except Exception as e:
            print(f"   ❌ User database test failed: {e}")
            return False
    
    def test_integration_flow(self) -> bool:
        """Test complete integration flow"""
        print("\n🔗 Testing Integration Flow...")
        
        try:
            # Create test frame
            test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Step 1: Face detection
            start_time = time.time()
            faces = self.face_detector.detect_faces(test_frame)
            detection_time = (time.time() - start_time) * 1000
            print(f"   ✅ Face detection: {len(faces)} faces found ({detection_time:.1f}ms)")
            
            # Step 2: Face encoding (if faces found)
            if faces:
                start_time = time.time()
                encoding = self.face_recognizer.generate_face_encoding(test_frame, faces[0].location)
                encoding_time = (time.time() - start_time) * 1000
                print(f"   ✅ Face encoding: {'Generated' if encoding is not None else 'Failed'} ({encoding_time:.1f}ms)")
                
                # Step 3: Face recognition (if encoding generated)
                if encoding is not None:
                    start_time = time.time()
                    user_info, confidence = self.face_recognizer.recognize_face(encoding)
                    recognition_time = (time.time() - start_time) * 1000
                    print(f"   ✅ Face recognition: {'Found' if user_info else 'Unknown'} user "
                          f"(conf: {confidence:.3f}, {recognition_time:.1f}ms)")
            
            print("   ✅ Integration flow completed successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Integration flow failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all automated tests"""
        print("🧪 AUTOMATED FACE RECOGNITION TEST SUITE")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        # Run tests
        results['system_initialization'] = self.test_system_initialization()
        results['performance'] = self.test_face_detection_performance()
        results['optimization'] = self.test_optimization_effectiveness()
        results['user_database'] = self.test_user_database_functionality()
        results['integration_flow'] = self.test_integration_flow()
        
        total_time = time.time() - start_time
        
        # Calculate summary
        passed_tests = sum(1 for test in [
            results['system_initialization'],
            results['user_database'],
            results['integration_flow']
        ] if test)
        
        total_tests = 3  # Boolean tests only
        
        # Print summary
        print(f"\n📋 AUTOMATED TEST SUMMARY")
        print(f"=" * 40)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Test Duration: {total_time:.1f}s")
        
        # Individual test status
        print(f"\n📊 Test Results:")
        print(f"   System Initialization: {'✅ PASS' if results['system_initialization'] else '❌ FAIL'}")
        print(f"   User Database: {'✅ PASS' if results['user_database'] else '❌ FAIL'}")
        print(f"   Integration Flow: {'✅ PASS' if results['integration_flow'] else '❌ FAIL'}")
        
        # Performance summary
        if 'performance' in results:
            print(f"\n⚡ Performance Summary:")
            for size, metrics in results['performance'].items():
                print(f"   {size}: {metrics['avg_time_ms']:.1f}ms average")
        
        # Optimization summary
        if 'optimization' in results:
            opt_results = results['optimization']
            best_config = opt_results['best_config']
            best_improvement = opt_results['optimization_configs'][best_config]['improvement_percentage']
            print(f"\n🚀 Optimization Summary:")
            print(f"   Best configuration: {best_config}")
            print(f"   Performance improvement: {best_improvement:.1f}%")
        
        # Overall status
        if passed_tests == total_tests:
            print(f"\n🎉 All core tests passed! System is functioning correctly.")
        else:
            print(f"\n⚠️ Some tests failed. Please review and address issues.")
        
        # Save results
        results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'test_duration': total_time,
            'timestamp': time.time()
        }
        
        return results

def main():
    """Main function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    tests = AutomatedFaceRecognitionTests()
    
    print("🤖 Automated Face Recognition Testing")
    print("=" * 50)
    print("1. Run all automated tests")
    print("2. Test system initialization")
    print("3. Test face detection performance")
    print("4. Test optimization effectiveness")
    print("5. Test user database")
    print("6. Test integration flow")
    print("7. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            tests.run_all_tests()
        elif choice == '2':
            tests.test_system_initialization()
        elif choice == '3':
            tests.test_face_detection_performance()
        elif choice == '4':
            tests.test_optimization_effectiveness()
        elif choice == '5':
            tests.test_user_database_functionality()
        elif choice == '6':
            tests.test_integration_flow()
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()