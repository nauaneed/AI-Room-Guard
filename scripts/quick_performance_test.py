"""
Quick Performance Test

This script runs a quick test to verify optimizations are working correctly.
"""

import sys
import os
import time
import cv2
import numpy as np

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.optimized_face_detector import OptimizedFaceDetector, OptimizationConfig

def quick_performance_test():
    """Quick test to verify optimizations work"""
    print("🧪 Quick Performance Test")
    print("=" * 50)
    
    # Create test frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Create detectors
    original = FaceDetector()
    optimized = OptimizedFaceDetector(original, OptimizationConfig(
        frame_skip_enabled=True,
        frame_skip_interval=3,
        face_tracking_enabled=True,
        tracking_timeout_ms=1000
    ))
    
    print("\n📊 Testing Original Detector (10 frames):")
    times_original = []
    for i in range(10):
        start = time.time()
        faces = original.detect_faces(frame)
        end = time.time()
        frame_time = (end - start) * 1000
        times_original.append(frame_time)
        print(f"  Frame {i+1}: {frame_time:.1f}ms ({len(faces)} faces)")
    
    print(f"\n⚡ Original Average: {np.mean(times_original):.1f}ms")
    
    print("\n📊 Testing Optimized Detector (10 frames):")
    times_optimized = []
    for i in range(10):
        start = time.time()
        faces = optimized.detect_faces(frame)
        end = time.time()
        frame_time = (end - start) * 1000
        times_optimized.append(frame_time)
        print(f"  Frame {i+1}: {frame_time:.1f}ms ({len(faces)} faces)")
    
    print(f"\n⚡ Optimized Average: {np.mean(times_optimized):.1f}ms")
    
    # Calculate improvement
    avg_original = np.mean(times_original)
    avg_optimized = np.mean(times_optimized)
    improvement = ((avg_original - avg_optimized) / avg_original) * 100
    
    print(f"\n📈 Performance Result:")
    print(f"   Original: {avg_original:.1f}ms")
    print(f"   Optimized: {avg_optimized:.1f}ms")
    print(f"   Improvement: {improvement:.1f}%")
    
    # Get optimization stats
    stats = optimized.get_optimization_stats()
    print(f"\n📊 Optimization Stats:")
    print(f"   Frames Processed: {stats.get('frames_processed', 0)}")
    print(f"   Cache Hits: {stats.get('cache_hits', 0)}")
    print(f"   Cache Hit Ratio: {stats.get('cache_hit_ratio', 0):.1%}")
    print(f"   Full Detections: {stats.get('full_detections', 0)}")
    
    if improvement > 0:
        print("\n✅ Optimization Working!")
    else:
        print("\n⚠️ Optimization needs tuning")

if __name__ == "__main__":
    quick_performance_test()