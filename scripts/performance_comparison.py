"""
Performance Comparison Test

This script compares the performance of the original face recognition system
vs the optimized version to validate improvements without breaking functionality.
"""

import sys
import os
import time
import cv2
import numpy as np
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.optimized_face_detector import OptimizedFaceDetector, OptimizationConfig
from src.core.performance_profiler import PerformanceProfiler

class PerformanceComparison:
    """Compare performance between original and optimized systems"""
    
    def __init__(self):
        print("🔧 Initializing Performance Comparison...")
        
        # Create components
        self.original_detector = FaceDetector()
        
        # Create optimized detector with different configurations
        self.optimized_configs = {
            'conservative': OptimizationConfig(
                frame_skip_enabled=True,
                frame_skip_interval=2,
                face_tracking_enabled=True,
                tracking_timeout_ms=1000
            ),
            'aggressive': OptimizationConfig(
                frame_skip_enabled=True,
                frame_skip_interval=3,
                face_tracking_enabled=True,
                tracking_timeout_ms=1500
            ),
            'max_performance': OptimizationConfig(
                frame_skip_enabled=True,
                frame_skip_interval=4,
                face_tracking_enabled=True,
                tracking_timeout_ms=2000
            )
        }
        
        self.optimized_detectors = {
            name: OptimizedFaceDetector(self.original_detector, config)
            for name, config in self.optimized_configs.items()
        }
        
        # Performance profiler
        self.profiler = PerformanceProfiler()
        
        print("✅ Performance Comparison initialized!")
    
    def generate_test_frames(self, num_frames: int = 30) -> List[np.ndarray]:
        """Generate test frames for consistent testing"""
        print(f"📸 Generating {num_frames} test frames...")
        
        frames = []
        for i in range(num_frames):
            # Create more realistic test frames
            frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
            
            # Add some structure to make detection more realistic
            # Add some face-like regions
            if i % 5 == 0:  # Every 5th frame has a face-like region
                # Add rectangular regions that might look like faces
                cv2.rectangle(frame, (200, 150), (350, 300), (120, 150, 180), -1)
                cv2.rectangle(frame, (220, 170), (330, 220), (100, 130, 160), -1)  # forehead
                cv2.rectangle(frame, (240, 240), (310, 270), (90, 120, 150), -1)   # mouth area
            
            frames.append(frame)
        
        return frames
    
    def test_original_detector(self, frames: List[np.ndarray]) -> Dict[str, Any]:
        """Test original face detector performance"""
        print(f"\n🔍 Testing Original Face Detector ({len(frames)} frames)")
        
        results = []
        total_faces = 0
        
        start_time = time.time()
        
        for i, frame in enumerate(frames):
            frame_start = time.time()
            
            # Detect faces
            faces = self.original_detector.detect_faces(frame)
            
            frame_end = time.time()
            frame_time = (frame_end - frame_start) * 1000  # ms
            
            results.append({
                'frame': i + 1,
                'faces_detected': len(faces),
                'processing_time_ms': frame_time
            })
            
            total_faces += len(faces)
            print(f"  Frame {i+1}/{len(frames)}: {len(faces)} faces, {frame_time:.1f}ms")
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # ms
        
        # Calculate statistics
        processing_times = [r['processing_time_ms'] for r in results]
        
        return {
            'name': 'Original',
            'total_time_ms': total_time,
            'avg_time_per_frame_ms': total_time / len(frames),
            'min_time_ms': min(processing_times),
            'max_time_ms': max(processing_times),
            'total_faces_detected': total_faces,
            'frames_per_second': len(frames) / (total_time / 1000),
            'results': results
        }
    
    def test_optimized_detector(self, name: str, detector: OptimizedFaceDetector, frames: List[np.ndarray]) -> Dict[str, Any]:
        """Test optimized face detector performance"""
        print(f"\n⚡ Testing Optimized Face Detector - {name.upper()} ({len(frames)} frames)")
        
        results = []
        total_faces = 0
        
        start_time = time.time()
        
        for i, frame in enumerate(frames):
            frame_start = time.time()
            
            # Detect faces
            faces = detector.detect_faces(frame)
            
            frame_end = time.time()
            frame_time = (frame_end - frame_start) * 1000  # ms
            
            results.append({
                'frame': i + 1,
                'faces_detected': len(faces),
                'processing_time_ms': frame_time
            })
            
            total_faces += len(faces)
            print(f"  Frame {i+1}/{len(frames)}: {len(faces)} faces, {frame_time:.1f}ms")
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # ms
        
        # Calculate statistics
        processing_times = [r['processing_time_ms'] for r in results]
        
        # Get optimization stats
        opt_stats = detector.get_optimization_stats()
        
        return {
            'name': f'Optimized-{name}',
            'total_time_ms': total_time,
            'avg_time_per_frame_ms': total_time / len(frames),
            'min_time_ms': min(processing_times),
            'max_time_ms': max(processing_times),
            'total_faces_detected': total_faces,
            'frames_per_second': len(frames) / (total_time / 1000),
            'optimization_stats': opt_stats,
            'results': results
        }
    
    def compare_accuracy(self, original_results: Dict, optimized_results: Dict) -> Dict[str, Any]:
        """Compare detection accuracy between original and optimized"""
        original_faces = [r['faces_detected'] for r in original_results['results']]
        optimized_faces = [r['faces_detected'] for r in optimized_results['results']]
        
        # Calculate accuracy metrics
        exact_matches = sum(1 for o, opt in zip(original_faces, optimized_faces) if o == opt)
        accuracy_percentage = (exact_matches / len(original_faces)) * 100
        
        face_difference = sum(abs(o - opt) for o, opt in zip(original_faces, optimized_faces))
        avg_face_difference = face_difference / len(original_faces)
        
        return {
            'exact_matches': exact_matches,
            'total_frames': len(original_faces),
            'accuracy_percentage': accuracy_percentage,
            'avg_face_difference': avg_face_difference,
            'original_total_faces': sum(original_faces),
            'optimized_total_faces': sum(optimized_faces)
        }
    
    def print_comparison_report(self, results: List[Dict[str, Any]]) -> None:
        """Print comprehensive comparison report"""
        print("\n📊 PERFORMANCE COMPARISON REPORT")
        print("=" * 80)
        
        # Performance summary
        print("\n📈 Performance Summary:")
        print("-" * 60)
        
        baseline = None
        for result in results:
            if result['name'] == 'Original':
                baseline = result
                break
        
        for result in results:
            name = result['name']
            fps = result['frames_per_second']
            avg_time = result['avg_time_per_frame_ms']
            total_faces = result['total_faces_detected']
            
            if baseline and result != baseline:
                # Calculate improvements
                speed_improvement = ((baseline['avg_time_per_frame_ms'] - avg_time) / baseline['avg_time_per_frame_ms']) * 100
                fps_improvement = ((fps - baseline['frames_per_second']) / baseline['frames_per_second']) * 100
                
                print(f"🔄 {name}:")
                print(f"   Avg Time/Frame: {avg_time:.1f}ms ({speed_improvement:+.1f}%)")
                print(f"   Frames/Second: {fps:.1f} FPS ({fps_improvement:+.1f}%)")
                print(f"   Total Faces: {total_faces}")
                
                if 'optimization_stats' in result:
                    opt_stats = result['optimization_stats']
                    print(f"   Cache Hit Ratio: {opt_stats.get('cache_hit_ratio', 0):.1%}")
                    print(f"   Active Tracks: {opt_stats.get('active_tracks', 0)}")
                print()
            else:
                print(f"📊 {name} (Baseline):")
                print(f"   Avg Time/Frame: {avg_time:.1f}ms")
                print(f"   Frames/Second: {fps:.1f} FPS")
                print(f"   Total Faces: {total_faces}")
                print()
        
        # Accuracy comparison
        if len(results) > 1 and baseline:
            print("\n🎯 Accuracy Comparison:")
            print("-" * 40)
            
            for result in results:
                if result != baseline:
                    accuracy = self.compare_accuracy(baseline, result)
                    print(f"📋 {result['name']} vs Original:")
                    print(f"   Exact Matches: {accuracy['exact_matches']}/{accuracy['total_frames']} ({accuracy['accuracy_percentage']:.1f}%)")
                    print(f"   Avg Face Difference: {accuracy['avg_face_difference']:.2f}")
                    print(f"   Face Count: {accuracy['optimized_total_faces']} vs {accuracy['original_total_faces']} (original)")
                    print()
        
        # Recommendations
        print("\n💡 Optimization Recommendations:")
        print("-" * 50)
        
        if baseline:
            best_performer = min(results[1:], key=lambda x: x['avg_time_per_frame_ms']) if len(results) > 1 else None
            
            if best_performer:
                improvement = ((baseline['avg_time_per_frame_ms'] - best_performer['avg_time_per_frame_ms']) / baseline['avg_time_per_frame_ms']) * 100
                
                print(f"✅ Best performer: {best_performer['name']}")
                print(f"   Performance gain: {improvement:.1f}% faster")
                print(f"   Recommended for: {'Real-time applications' if improvement > 20 else 'Balanced performance'}")
                
                # Check if accuracy is maintained
                if len(results) > 1:
                    accuracy = self.compare_accuracy(baseline, best_performer)
                    if accuracy['accuracy_percentage'] >= 90:
                        print(f"   ✅ Maintains high accuracy: {accuracy['accuracy_percentage']:.1f}%")
                    else:
                        print(f"   ⚠️ Accuracy impact: {accuracy['accuracy_percentage']:.1f}% - consider tuning")
            else:
                print("   No significant improvement found")
        
        print("\n🔧 Next Steps:")
        print("   1. Deploy best-performing configuration")
        print("   2. Monitor production performance")
        print("   3. Fine-tune parameters based on real usage")
    
    def run_comprehensive_comparison(self) -> None:
        """Run comprehensive performance comparison"""
        print("\n🚀 Running Comprehensive Performance Comparison")
        print("=" * 70)
        
        # Generate test frames
        test_frames = self.generate_test_frames(30)
        
        # Test original detector
        original_results = self.test_original_detector(test_frames)
        
        # Test optimized detectors
        optimized_results = []
        for name, detector in self.optimized_detectors.items():
            result = self.test_optimized_detector(name, detector, test_frames)
            optimized_results.append(result)
        
        # Combine all results
        all_results = [original_results] + optimized_results
        
        # Print comparison report
        self.print_comparison_report(all_results)
        
        # Test safety - ensure optimization doesn't break core functionality
        print("\n🛡️ Safety Check:")
        print("-" * 30)
        
        safety_passed = True
        for opt_result in optimized_results:
            accuracy = self.compare_accuracy(original_results, opt_result)
            if accuracy['accuracy_percentage'] < 70:  # Allow some variation for optimization
                print(f"❌ {opt_result['name']}: Accuracy too low ({accuracy['accuracy_percentage']:.1f}%)")
                safety_passed = False
            else:
                print(f"✅ {opt_result['name']}: Accuracy acceptable ({accuracy['accuracy_percentage']:.1f}%)")
        
        if safety_passed:
            print("\n✅ All optimizations passed safety checks!")
        else:
            print("\n⚠️ Some optimizations may need tuning")

def main():
    """Main comparison function"""
    comparison = PerformanceComparison()
    
    try:
        comparison.run_comprehensive_comparison()
        print("\n🏁 Performance comparison completed successfully!")
        
    except KeyboardInterrupt:
        print("\n👋 Comparison interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()