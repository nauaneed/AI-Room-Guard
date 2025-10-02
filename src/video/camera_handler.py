"""
Camera handling module for the AI Guard Agent.
Manages webcam access and video capture.
"""

import cv2
import logging
import threading
import time
from typing import Optional, Tuple
import numpy as np
from config.settings import VideoConfig

class CameraHandler:
    """Handles webcam access and video capture"""
    
    def __init__(self, camera_index: int = VideoConfig.CAMERA_INDEX):
        self.logger = logging.getLogger(__name__)
        self.camera_index = camera_index
        self.cap = None
        self.is_active = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        
        # Video configuration
        self.frame_width = VideoConfig.FRAME_WIDTH
        self.frame_height = VideoConfig.FRAME_HEIGHT
        self.fps = VideoConfig.FPS
    
    def initialize(self) -> bool:
        """Initialize camera and test functionality"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                self.logger.error(f"Cannot open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Test frame capture
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error("Cannot read from camera")
                return False
            
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def start_capture(self) -> bool:
        """Start continuous frame capture in a separate thread"""
        if self.is_active:
            self.logger.warning("Camera capture already active")
            return False
        
        if not self.cap or not self.cap.isOpened():
            self.logger.error("Camera not initialized")
            return False
        
        self.is_active = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        self.logger.info("Camera capture started")
        return True
    
    def stop_capture(self):
        """Stop frame capture"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        self.logger.info("Camera capture stopped")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        while self.is_active and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if ret:
                with self.frame_lock:
                    self.current_frame = frame.copy()
            else:
                self.logger.warning("Failed to read frame from camera")
                time.sleep(0.1)  # Prevent tight loop on error
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame (useful for testing)"""
        if not self.cap or not self.cap.isOpened():
            self.logger.error("Camera not initialized")
            return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            self.logger.error("Failed to capture frame")
            return None
    
    def save_frame(self, frame: np.ndarray, filename: str) -> bool:
        """Save a frame to file"""
        try:
            cv2.imwrite(filename, frame)
            self.logger.info(f"Frame saved to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save frame: {e}")
            return False
    
    def get_camera_info(self) -> dict:
        """Get camera information"""
        if not self.cap or not self.cap.isOpened():
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'backend': self.cap.getBackendName()
        }
    
    def is_camera_available(self) -> bool:
        """Check if camera is available and working"""
        return self.cap is not None and self.cap.isOpened() and self.is_active
    
    def cleanup(self):
        """Release camera resources"""
        self.stop_capture()
        
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Test function for this module
def test_camera():
    """Test camera functionality"""
    camera = CameraHandler()
    
    print("Testing camera initialization...")
    if not camera.initialize():
        print("Failed to initialize camera")
        return False
    
    print("Camera info:", camera.get_camera_info())
    
    print("Testing single frame capture...")
    frame = camera.capture_single_frame()
    if frame is not None:
        print(f"Captured frame shape: {frame.shape}")
        camera.save_frame(frame, "test_frame.jpg")
    else:
        print("Failed to capture frame")
        return False
    
    print("Testing continuous capture for 5 seconds...")
    camera.start_capture()
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 5:
        current_frame = camera.get_current_frame()
        if current_frame is not None:
            frame_count += 1
            # Display frame (comment out if running headless)
            # cv2.imshow('Test Feed', current_frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        time.sleep(0.1)
    
    camera.stop_capture()
    camera.cleanup()
    
    print(f"Captured {frame_count} frames in 5 seconds")
    return frame_count > 0

if __name__ == "__main__":
    # Run test when module is executed directly
    logging.basicConfig(level=logging.INFO)
    test_camera()