"""
Optimized Face Recognition System - Phase 1: Frame Skipping

This module implements frame skipping optimization for face detection
to improve performance while maintaining accuracy.
"""

import cv2
import numpy as np
import time
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

# Import base components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_detector import FaceDetector, DetectedFace
from src.core.performance_profiler import PerformanceProfiler

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """Configuration for performance optimizations"""
    # Frame skipping
    frame_skip_enabled: bool = True
    frame_skip_interval: int = 2  # Process every Nth frame
    
    # Face tracking  
    face_tracking_enabled: bool = True
    tracking_timeout_ms: float = 1000  # 1 second
    tracking_distance_threshold: float = 50.0  # pixels
    
    # Performance monitoring
    performance_monitoring: bool = True
    log_slow_operations: bool = True
    slow_operation_threshold_ms: float = 200

class OptimizedFaceDetector:
    """
    Face detector with performance optimizations
    
    Optimizations:
    - Frame skipping: Process every Nth frame
    - Face tracking: Track detected faces across frames
    - Intelligent fallback: Use full detection when tracking fails
    """
    
    def __init__(self, base_detector: FaceDetector = None, config: OptimizationConfig = None):
        self.base_detector = base_detector or FaceDetector()
        self.config = config or OptimizationConfig()
        self.profiler = PerformanceProfiler() if self.config.performance_monitoring else None
        
        # Frame skipping state
        self.frame_count = 0
        self.last_detection_frame = -1
        self.cached_faces: List[DetectedFace] = []
        
        # Face tracking state
        self.tracked_faces: List[Dict[str, Any]] = []
        self.next_face_id = 0
        
        # Statistics tracking
        self.stats = {
            'frames_processed': 0,
            'full_detections': 0,
            'cache_hits': 0,
            'skipped_frames': 0
        }
        
        logger.info(f"Optimized Face Detector initialized with config: {self.config}")
    
    def detect_faces(self, frame: np.ndarray) -> List[DetectedFace]:
        """
        Optimized face detection with frame skipping and tracking
        """
        self.frame_count += 1
        current_time = time.time() * 1000  # milliseconds
        
        # Start performance measurement
        op_id = None
        if self.profiler:
            op_id = self.profiler.start_operation('optimized_face_detection', {
                'frame_count': self.frame_count,
                'frame_shape': frame.shape
            })
        
        try:
            detected_faces = []
            self.stats['frames_processed'] += 1
            
            # Decide whether to skip this frame
            should_skip_frame = self._should_skip_frame()
            
            if should_skip_frame:
                # Use cached results with position prediction (even if empty)
                detected_faces = self._predict_face_positions(frame, current_time)
                self.stats['cache_hits'] += 1
                self.stats['skipped_frames'] += 1
                logger.debug(f"Frame {self.frame_count}: Using cached faces ({len(detected_faces)} faces)")
            else:
                # Perform full face detection
                detected_faces = self._full_face_detection(frame, current_time)
                self.last_detection_frame = self.frame_count
                self.cached_faces = detected_faces.copy()
                self.stats['full_detections'] += 1
                logger.debug(f"Frame {self.frame_count}: Full detection ({len(detected_faces)} faces)")
            
            # Update tracking information
            if self.config.face_tracking_enabled:
                self._update_face_tracking(detected_faces, current_time)
            
            return detected_faces
            
        finally:
            # End performance measurement
            if self.profiler and op_id:
                context = {
                    'faces_detected': len(detected_faces) if 'detected_faces' in locals() else 0,
                    'used_cache': should_skip_frame if 'should_skip_frame' in locals() else False,
                    'tracking_enabled': self.config.face_tracking_enabled
                }
                self.profiler.end_operation(op_id, context)
    
    def _should_skip_frame(self) -> bool:
        """Determine if current frame should be skipped"""
        if not self.config.frame_skip_enabled:
            return False
        
        # Always do detection on first frame
        if self.last_detection_frame < 0:
            return False
        
        # Skip if we haven't reached the interval
        frames_since_last = self.frame_count - self.last_detection_frame
        return frames_since_last < self.config.frame_skip_interval
    
    def _full_face_detection(self, frame: np.ndarray, current_time: float) -> List[DetectedFace]:
        """Perform full face detection using base detector"""
        return self.base_detector.detect_faces(frame)
    
    def _predict_face_positions(self, frame: np.ndarray, current_time: float) -> List[DetectedFace]:
        """Predict face positions based on cached results and tracking"""
        if not self.config.face_tracking_enabled or not self.tracked_faces:
            return self.cached_faces
        
        predicted_faces = []
        
        for cached_face in self.cached_faces:
            # Find corresponding tracked face
            tracked_face = self._find_tracked_face(cached_face, current_time)
            
            if tracked_face:
                # Use tracked position with some prediction
                predicted_location = self._predict_face_location(tracked_face, current_time)
                
                # Create new DetectedFace with predicted location
                predicted_face = DetectedFace(
                    location=predicted_location,
                    confidence=cached_face.confidence * 0.9,  # Slightly reduce confidence
                    landmarks=cached_face.landmarks  # Keep original landmarks
                )
                predicted_faces.append(predicted_face)
            else:
                # No tracking info, use cached face as-is but reduce confidence
                cached_face.confidence *= 0.8
                predicted_faces.append(cached_face)
        
        return predicted_faces
    
    def _update_face_tracking(self, detected_faces: List[DetectedFace], current_time: float):
        """Update face tracking information"""
        # Remove expired tracks
        self.tracked_faces = [
            track for track in self.tracked_faces
            if current_time - track['last_seen'] < self.config.tracking_timeout_ms
        ]
        
        # Update existing tracks and create new ones
        for face in detected_faces:
            existing_track = self._find_matching_track(face, current_time)
            
            if existing_track:
                # Update existing track
                existing_track['locations'].append(face.location)
                existing_track['timestamps'].append(current_time)
                existing_track['last_seen'] = current_time
                existing_track['confidence'] = face.confidence
                
                # Keep only recent history
                max_history = 5
                if len(existing_track['locations']) > max_history:
                    existing_track['locations'] = existing_track['locations'][-max_history:]
                    existing_track['timestamps'] = existing_track['timestamps'][-max_history:]
            else:
                # Create new track
                new_track = {
                    'id': self.next_face_id,
                    'locations': [face.location],
                    'timestamps': [current_time],
                    'last_seen': current_time,
                    'confidence': face.confidence,
                    'created': current_time
                }
                self.tracked_faces.append(new_track)
                self.next_face_id += 1
    
    def _find_tracked_face(self, face: DetectedFace, current_time: float) -> Optional[Dict[str, Any]]:
        """Find tracked face that matches given detected face"""
        return self._find_matching_track(face, current_time)
    
    def _find_matching_track(self, face: DetectedFace, current_time: float) -> Optional[Dict[str, Any]]:
        """Find existing track that matches the given face"""
        top, right, bottom, left = face.location
        face_center = ((left + right) // 2, (top + bottom) // 2)
        
        best_track = None
        min_distance = float('inf')
        
        for track in self.tracked_faces:
            if not track['locations']:
                continue
            
            # Get last known position
            last_location = track['locations'][-1]
            last_top, last_right, last_bottom, last_left = last_location
            last_center = ((last_left + last_right) // 2, (last_top + last_bottom) // 2)
            
            # Calculate distance
            distance = np.sqrt((face_center[0] - last_center[0])**2 + (face_center[1] - last_center[1])**2)
            
            if distance < self.config.tracking_distance_threshold and distance < min_distance:
                min_distance = distance
                best_track = track
        
        return best_track
    
    def _predict_face_location(self, track: Dict[str, Any], current_time: float) -> Tuple[int, int, int, int]:
        """Predict face location based on tracking history"""
        if len(track['locations']) < 2:
            return track['locations'][-1]
        
        # Simple linear prediction based on last two positions
        last_location = track['locations'][-1]
        prev_location = track['locations'][-2]
        last_time = track['timestamps'][-1]
        prev_time = track['timestamps'][-2]
        
        time_delta = current_time - last_time
        time_interval = last_time - prev_time
        
        if time_interval <= 0:
            return last_location
        
        # Calculate velocity
        velocity_factor = time_delta / time_interval
        
        top_delta = (last_location[0] - prev_location[0]) * velocity_factor
        right_delta = (last_location[1] - prev_location[1]) * velocity_factor
        bottom_delta = (last_location[2] - prev_location[2]) * velocity_factor
        left_delta = (last_location[3] - prev_location[3]) * velocity_factor
        
        # Predict new location
        predicted_location = (
            int(last_location[0] + top_delta),
            int(last_location[1] + right_delta),
            int(last_location[2] + bottom_delta),
            int(last_location[3] + left_delta)
        )
        
        return predicted_location
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            'frames_processed': self.stats['frames_processed'],
            'full_detections': self.stats['full_detections'],
            'cache_hits': self.stats['cache_hits'],
            'skipped_frames': self.stats['skipped_frames'],
            'active_tracks': len(self.tracked_faces),
            'cache_hit_ratio': self.stats['cache_hits'] / max(self.stats['frames_processed'], 1)
        }
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        if self.frame_count == 0:
            return 0.0
        
        full_detections = self.frame_count // max(self.config.frame_skip_interval, 1)
        cache_hits = self.frame_count - full_detections
        
        return cache_hits / self.frame_count if self.frame_count > 0 else 0.0

# Test function
if __name__ == "__main__":
    print("🧪 Testing Optimized Face Detection...")
    
    # Create optimized detector
    config = OptimizationConfig(
        frame_skip_enabled=True,
        frame_skip_interval=3,
        face_tracking_enabled=True
    )
    
    optimized_detector = OptimizedFaceDetector(config=config)
    
    # Simulate frame processing
    for i in range(20):
        # Create synthetic frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Detect faces
        faces = optimized_detector.detect_faces(frame)
        print(f"Frame {i+1}: {len(faces)} faces detected")
        
        time.sleep(0.01)  # Simulate frame rate
    
    # Print optimization stats
    stats = optimized_detector.get_optimization_stats()
    print(f"\n📊 Optimization Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Print performance report
    if optimized_detector.profiler:
        optimized_detector.profiler.print_performance_report()