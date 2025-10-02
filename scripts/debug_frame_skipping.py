"""
Debug Frame Skipping

This test helps debug why frame skipping isn't working.
"""

import sys
import os
import time
import numpy as np

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector
from src.vision.optimized_face_detector import OptimizedFaceDetector, OptimizationConfig

def debug_frame_skipping():
    """Debug frame skipping logic"""
    print("🐛 Debug Frame Skipping")
    print("=" * 40)
    
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    config = OptimizationConfig(
        frame_skip_enabled=True,
        frame_skip_interval=2,
        face_tracking_enabled=False,
        performance_monitoring=False
    )
    
    optimized = OptimizedFaceDetector(FaceDetector(), config)
    
    print("Manual debugging of frame skipping logic:")
    print()
    
    for i in range(6):
        print(f"Frame {i+1}:")
        
        # Before detection - check state
        print(f"  Before: frame_count={optimized.frame_count}, last_detection={optimized.last_detection_frame}")
        print(f"  Before: cached_faces={len(optimized.cached_faces)}")
        
        # Manual check of should_skip_frame logic
        frames_since_last = optimized.frame_count + 1 - optimized.last_detection_frame  # +1 because frame_count increments in detect_faces
        has_cached_data = len(optimized.cached_faces) > 0 or optimized.last_detection_frame >= 0
        should_skip = optimized.last_detection_frame >= 0 and frames_since_last < config.frame_skip_interval and has_cached_data
        
        print(f"  Should skip calculation:")
        print(f"    frames_since_last={frames_since_last}")
        print(f"    has_cached_data={has_cached_data}")
        print(f"    should_skip={should_skip}")
        
        # Detect faces
        start_time = time.time()
        faces = optimized.detect_faces(frame)
        end_time = time.time()
        
        frame_time = (end_time - start_time) * 1000
        
        # After detection - check state
        print(f"  After: frame_count={optimized.frame_count}, last_detection={optimized.last_detection_frame}")
        print(f"  After: cached_faces={len(optimized.cached_faces)}")
        print(f"  Time: {frame_time:.1f}ms")
        
        stats = optimized.get_optimization_stats()
        print(f"  Stats: full_detections={stats['full_detections']}, cache_hits={stats['cache_hits']}")
        print()

if __name__ == "__main__":
    debug_frame_skipping()