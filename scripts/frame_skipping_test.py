"""
Simple Frame Skipping Test

This test demonstrates frame skipping optimization clearly.
"""

import sys
import os
import time
import numpy as np

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.optimized_face_detector import OptimizedFaceDetector, OptimizationConfig

def test_frame_skipping():
    """Test frame skipping logic specifically"""
    print("🎯 Frame Skipping Test")
    print("=" * 40)
    
    # Create a single frame for consistent testing
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Create optimized detector with aggressive skipping
    config = OptimizationConfig(
        frame_skip_enabled=True,
        frame_skip_interval=2,  # Skip every other frame
        face_tracking_enabled=False,  # Disable tracking for this test
        performance_monitoring=False  # Disable profiling for cleaner output
    )
    
    optimized = OptimizedFaceDetector(FaceDetector(), config)
    
    print("Processing 10 frames with skip_interval=2:")
    print("Expected pattern: Full, Skip, Full, Skip, Full, Skip...")
    print()
    
    total_time = 0
    full_detection_times = []
    cache_times = []
    
    for i in range(10):
        start_time = time.time()
        faces = optimized.detect_faces(frame)
        end_time = time.time()
        
        frame_time = (end_time - start_time) * 1000  # ms
        total_time += frame_time
        
        # Check if this was a cache hit or full detection
        stats = optimized.get_optimization_stats()
        
        if i == 0 or stats['cache_hits'] == 0 or (stats['cache_hits'] + stats['full_detections']) == stats['full_detections']:
            detection_type = "FULL"
            full_detection_times.append(frame_time)
        else:
            detection_type = "SKIP"
            cache_times.append(frame_time)
        
        print(f"Frame {i+1:2d}: {frame_time:6.1f}ms [{detection_type}] - {len(faces)} faces")
    
    # Print statistics
    stats = optimized.get_optimization_stats()
    print(f"\n📊 Results:")
    print(f"   Total Frames: {stats['frames_processed']}")
    print(f"   Full Detections: {stats['full_detections']}")
    print(f"   Cache Hits: {stats['cache_hits']}")
    print(f"   Cache Hit Ratio: {stats['cache_hit_ratio']:.1%}")
    print(f"   Total Time: {total_time:.1f}ms")
    print(f"   Average Time: {total_time/10:.1f}ms")
    
    if full_detection_times and cache_times:
        avg_full = np.mean(full_detection_times)
        avg_cache = np.mean(cache_times)
        speedup = (avg_full - avg_cache) / avg_full * 100
        
        print(f"\n⚡ Performance Analysis:")
        print(f"   Full Detection Avg: {avg_full:.1f}ms")
        print(f"   Cache Hit Avg: {avg_cache:.1f}ms")
        print(f"   Speedup on cached frames: {speedup:.1f}%")
    elif stats['cache_hit_ratio'] > 0:
        print(f"\n✅ Frame skipping is working!")
        print(f"   {stats['cache_hits']} frames were skipped")
    else:
        print(f"\n⚠️ Frame skipping not working as expected")

def test_without_optimization():
    """Test baseline without optimization"""
    print("\n🔍 Baseline Test (No Optimization)")
    print("=" * 40)
    
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    original = FaceDetector()
    
    times = []
    for i in range(10):
        start_time = time.time()
        faces = original.detect_faces(frame)
        end_time = time.time()
        
        frame_time = (end_time - start_time) * 1000
        times.append(frame_time)
        print(f"Frame {i+1:2d}: {frame_time:6.1f}ms [FULL] - {len(faces)} faces")
    
    avg_time = np.mean(times)
    print(f"\n📊 Baseline Results:")
    print(f"   Average Time: {avg_time:.1f}ms")
    print(f"   All frames: Full detection")
    
    return avg_time

if __name__ == "__main__":
    baseline_avg = test_without_optimization()
    test_frame_skipping()
    
    print(f"\n🎯 Summary:")
    print(f"   This test demonstrates frame skipping optimization")
    print(f"   Cache hits should be much faster than full detections")
    print(f"   Overall performance depends on cache hit ratio")