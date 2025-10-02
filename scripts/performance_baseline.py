"""
Face Recognition Performance Baseline

This script establishes performance baselines for our face recognition system
before applying optimizations.
"""

import sys
import os
import time
import cv2
import numpy as np
from typing import List

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.performance_profiler import PerformanceProfiler
from src.vision.face_recognizer import FaceRecognizer
from src.vision.face_detector import FaceDetector
from src.video.camera_handler import CameraHandler
from src.core.trust_manager import TrustLevel

class PerformanceBaseline:
    """Create performance baseline for face recognition system"""
    
    def __init__(self):
        print("🔧 Initializing Performance Baseline System...")
        
        self.profiler = PerformanceProfiler()
        self.face_recognizer = FaceRecognizer()
        self.face_detector = FaceDetector()
        self.camera_handler = CameraHandler()
        
        print("✅ Performance Baseline System initialized!")
    
    def measure_face_detection_performance(self, num_samples: int = 20) -> None:
        """Measure face detection performance"""
        print(f"\n📸 Measuring Face Detection Performance ({num_samples} samples)")
        
        # Start camera
        if not self.camera_handler.start_capture():
            print("❌ Failed to start camera, using synthetic frames")
            self._measure_synthetic_face_detection(num_samples)
            return
        
        try:
            for i in range(num_samples):
                frame = self.camera_handler.get_current_frame()
                if frame is not None:
                    # Measure face detection
                    op_id = self.profiler.start_operation('face_detection', {
                        'frame_shape': frame.shape,
                        'sample': i + 1
                    })
                    
                    detected_faces = self.face_detector.detect_faces(frame)
                    
                    self.profiler.end_operation(op_id, {
                        'faces_detected': len(detected_faces)
                    })
                    
                    print(f"  Sample {i+1}/{num_samples}: {len(detected_faces)} faces detected")
                    time.sleep(0.1)  # Small delay between samples
                else:
                    print(f"  Sample {i+1}/{num_samples}: No frame available")
        
        finally:
            self.camera_handler.stop_capture()
    
    def _measure_synthetic_face_detection(self, num_samples: int) -> None:
        """Measure face detection with synthetic frames"""
        print("  Using synthetic frames for testing...")
        
        for i in range(num_samples):
            # Create synthetic frame
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            op_id = self.profiler.start_operation('face_detection', {
                'frame_shape': frame.shape,
                'sample': i + 1,
                'synthetic': True
            })
            
            detected_faces = self.face_detector.detect_faces(frame)
            
            self.profiler.end_operation(op_id, {
                'faces_detected': len(detected_faces),
                'synthetic': True
            })
            
            print(f"  Sample {i+1}/{num_samples}: {len(detected_faces)} faces detected (synthetic)")
    
    def measure_face_encoding_performance(self, num_samples: int = 20) -> None:
        """Measure face encoding generation performance"""
        print(f"\n🔢 Measuring Face Encoding Performance ({num_samples} samples)")
        
        # Create test frames with face-like regions
        for i in range(num_samples):
            # Create synthetic frame with face-like region
            frame = np.random.randint(100, 200, (480, 640, 3), dtype=np.uint8)
            face_location = (100, 300, 300, 100)  # (top, right, bottom, left)
            
            op_id = self.profiler.start_operation('face_encoding', {
                'frame_shape': frame.shape,
                'face_location': face_location,
                'sample': i + 1
            })
            
            encoding = self.face_recognizer.generate_face_encoding(frame, face_location)
            
            self.profiler.end_operation(op_id, {
                'encoding_generated': encoding is not None,
                'encoding_shape': encoding.shape if encoding is not None else None
            })
            
            status = "✅" if encoding is not None else "❌"
            print(f"  Sample {i+1}/{num_samples}: {status} Encoding generated")
    
    def measure_face_recognition_performance(self, num_samples: int = 15) -> None:
        """Measure face recognition performance"""
        print(f"\n🔍 Measuring Face Recognition Performance ({num_samples} samples)")
        
        # Get a known encoding for testing
        test_encodings = []
        frame = np.random.randint(100, 200, (480, 640, 3), dtype=np.uint8)
        face_location = (100, 300, 300, 100)
        
        # Generate test encoding
        test_encoding = self.face_recognizer.generate_face_encoding(frame, face_location)
        if test_encoding is not None:
            test_encodings.append(test_encoding)
        
        # Use random encodings if we can't generate real ones
        if not test_encodings:
            for _ in range(3):
                test_encodings.append(np.random.random(128))
        
        for i in range(num_samples):
            encoding = test_encodings[i % len(test_encodings)]
            
            op_id = self.profiler.start_operation('face_recognition', {
                'encoding_shape': encoding.shape,
                'sample': i + 1
            })
            
            try:
                user_info, confidence = self.face_recognizer.recognize_face(
                    encoding, TrustLevel.MEDIUM
                )
                
                self.profiler.end_operation(op_id, {
                    'user_recognized': user_info is not None,
                    'confidence': confidence,
                    'user_id': user_info.get('user_id') if user_info else None
                })
                
                status = f"✅ User: {user_info.get('name', 'Unknown')}" if user_info else "❌ Unknown"
                print(f"  Sample {i+1}/{num_samples}: {status} (confidence: {confidence:.3f})")
                
            except Exception as e:
                self.profiler.end_operation(op_id, {'error': str(e)})
                print(f"  Sample {i+1}/{num_samples}: ❌ Error: {e}")
    
    def measure_trust_evaluation_performance(self, num_samples: int = 25) -> None:
        """Measure trust evaluation performance"""
        print(f"\n🛡️ Measuring Trust Evaluation Performance ({num_samples} samples)")
        
        user_ids = ['user_ddded5e2', 'test_user_001']  # Known users
        
        for i in range(num_samples):
            user_id = user_ids[i % len(user_ids)]
            confidence = 0.5 + (i % 10) * 0.05  # Vary confidence
            
            op_id = self.profiler.start_operation('trust_evaluation', {
                'user_id': user_id,
                'confidence': confidence,
                'sample': i + 1
            })
            
            try:
                trust_level = self.face_recognizer.trust_manager.record_recognition_event(
                    user_id, confidence, f"Performance test {i+1}"
                )
                
                access_granted = self.face_recognizer.trust_manager.should_grant_access(
                    user_id, TrustLevel.MEDIUM
                )
                
                self.profiler.end_operation(op_id, {
                    'trust_level': trust_level.name,
                    'access_granted': access_granted
                })
                
                print(f"  Sample {i+1}/{num_samples}: Trust: {trust_level.name}, Access: {access_granted}")
                
            except Exception as e:
                self.profiler.end_operation(op_id, {'error': str(e)})
                print(f"  Sample {i+1}/{num_samples}: ❌ Error: {e}")
    
    def measure_response_generation_performance(self, num_samples: int = 15) -> None:
        """Measure response generation performance"""
        print(f"\n📢 Measuring Response Generation Performance ({num_samples} samples)")
        
        for i in range(num_samples):
            op_id = self.profiler.start_operation('response_generation', {
                'sample': i + 1
            })
            
            try:
                if i % 3 == 0:
                    # Trusted user response
                    response_event = self.face_recognizer.response_system.generate_trusted_user_response(
                        user_id="test_user",
                        user_name="Test User",
                        confidence=0.85,
                        trust_level="HIGH",
                        trust_score=0.82,
                        access_granted=True
                    )
                else:
                    # Unknown person response
                    response_event = self.face_recognizer.response_system.generate_unknown_person_response(
                        confidence=0.3
                    )
                
                self.profiler.end_operation(op_id, {
                    'response_type': response_event.event_type.value,
                    'alert_level': response_event.alert_level.value
                })
                
                print(f"  Sample {i+1}/{num_samples}: {response_event.event_type.value} response generated")
                
            except Exception as e:
                self.profiler.end_operation(op_id, {'error': str(e)})
                print(f"  Sample {i+1}/{num_samples}: ❌ Error: {e}")
    
    def run_comprehensive_baseline(self) -> None:
        """Run comprehensive performance baseline measurement"""
        print("\n🚀 Running Comprehensive Performance Baseline")
        print("=" * 70)
        
        try:
            # Measure all components
            self.measure_face_detection_performance(20)
            self.measure_face_encoding_performance(15)
            self.measure_face_recognition_performance(10)
            self.measure_trust_evaluation_performance(20)
            self.measure_response_generation_performance(15)
            
            # Save baseline
            self.profiler.save_baseline("pre_optimization")
            
            # Generate comprehensive report
            print("\n📊 BASELINE PERFORMANCE REPORT")
            print("=" * 70)
            self.profiler.print_performance_report(detailed=True)
            
            # Performance suggestions
            suggestions = self.profiler.get_performance_suggestions()
            print("\n🎯 OPTIMIZATION TARGETS:")
            print("-" * 40)
            for suggestion in suggestions:
                print(f"   {suggestion}")
            
        except Exception as e:
            print(f"❌ Error during baseline measurement: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main baseline measurement function"""
    baseline = PerformanceBaseline()
    
    print("\n🎯 Face Recognition System - Performance Baseline")
    print("=" * 60)
    print("This will measure the current performance of all system components")
    print("to establish a baseline before optimization.")
    
    try:
        baseline.run_comprehensive_baseline()
        print("\n✅ Baseline measurement completed successfully!")
        print("📁 Results saved to data/performance_metrics_baseline_pre_optimization.json")
        
    except KeyboardInterrupt:
        print("\n👋 Baseline measurement interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()