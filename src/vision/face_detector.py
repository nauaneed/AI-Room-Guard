"""
Face detection module for the AI Guard Agent.
Handles face detection using OpenCV and face_recognition library.
"""

import cv2
import face_recognition
import numpy as np
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from src.utils.smart_logger import SmartLogger

@dataclass
class DetectedFace:
    """Represents a detected face with location and confidence"""
    location: Tuple[int, int, int, int]  # (top, right, bottom, left)
    confidence: float
    landmarks: Optional[dict] = None
    encoding: Optional[np.ndarray] = None

class FaceDetector:
    """Handles face detection using multiple backends for reliability"""
    
    def __init__(self, detection_method: str = "hog"):
        """
        Initialize face detector
        
        Args:
            detection_method: 'hog' for CPU, 'cnn' for GPU (more accurate but slower)
        """
        self.logger = SmartLogger(__name__)
        self.detection_method = detection_method
        
        # OpenCV cascade classifier as backup
        self.cv_face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        self.logger.info(f"Face detector initialized with method: {detection_method}")
    
    def detect_faces_opencv(self, image: np.ndarray) -> List[DetectedFace]:
        """
        Detect faces using OpenCV Haar cascades (fast but less accurate)
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of DetectedFace objects
        """
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.cv_face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            detected_faces = []
            for (x, y, w, h) in faces:
                # Convert to (top, right, bottom, left) format
                location = (y, x + w, y + h, x)
                confidence = 0.8  # OpenCV doesn't provide confidence, use default
                
                detected_faces.append(DetectedFace(
                    location=location,
                    confidence=confidence
                ))
            
            self.logger.debug(f"OpenCV detected {len(detected_faces)} faces")
            return detected_faces
            
        except Exception as e:
            self.logger.error(f"OpenCV face detection error: {e}")
            return []
    
    def detect_faces_dlib(self, image: np.ndarray) -> List[DetectedFace]:
        """
        Detect faces using dlib/face_recognition (more accurate)
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of DetectedFace objects
        """
        try:
            # Convert BGR to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect face locations
            face_locations = face_recognition.face_locations(
                rgb_image, 
                model=self.detection_method
            )
            
            detected_faces = []
            for location in face_locations:
                # face_recognition returns (top, right, bottom, left)
                confidence = 0.9  # dlib is generally more confident
                
                detected_faces.append(DetectedFace(
                    location=location,
                    confidence=confidence
                ))
            
            self.logger.debug(f"Dlib detected {len(detected_faces)} faces")
            return detected_faces
            
        except Exception as e:
            self.logger.error(f"Dlib face detection error: {e}")
            return []
    
    def detect_faces(self, image: np.ndarray, use_dlib: bool = True) -> List[DetectedFace]:
        """
        Detect faces using the preferred method with fallback
        
        Args:
            image: Input image as numpy array
            use_dlib: Whether to use dlib (True) or OpenCV (False) as primary
            
        Returns:
            List of DetectedFace objects
        """
        if image is None or image.size == 0:
            self.logger.warning("Empty or invalid image provided")
            return []
        
        detected_faces = []
        
        # Try primary method
        if use_dlib:
            detected_faces = self.detect_faces_dlib(image)
            
            # Fallback to OpenCV if dlib fails
            if not detected_faces:
                self.logger.debug("Dlib detection failed, falling back to OpenCV")
                detected_faces = self.detect_faces_opencv(image)
        else:
            detected_faces = self.detect_faces_opencv(image)
            
            # Fallback to dlib if OpenCV fails
            if not detected_faces:
                self.logger.debug("OpenCV detection failed, falling back to dlib")
                detected_faces = self.detect_faces_dlib(image)
        
        self.logger.face_detection_change(len(detected_faces), f"Total faces detected: {len(detected_faces)}")
        return detected_faces
    
    def get_face_landmarks(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[dict]:
        """
        Get facial landmarks for a detected face
        
        Args:
            image: Input image as numpy array
            face_location: Face location as (top, right, bottom, left)
            
        Returns:
            Dictionary of facial landmarks or None if failed
        """
        try:
            # Convert BGR to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get landmarks
            landmarks_list = face_recognition.face_landmarks(rgb_image, [face_location])
            
            if landmarks_list:
                return landmarks_list[0]
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Face landmarks detection error: {e}")
            return None
    
    def draw_face_boxes(self, image: np.ndarray, detected_faces: List[DetectedFace]) -> np.ndarray:
        """
        Draw bounding boxes around detected faces
        
        Args:
            image: Input image as numpy array
            detected_faces: List of DetectedFace objects
            
        Returns:
            Image with face boxes drawn
        """
        result_image = image.copy()
        
        for face in detected_faces:
            top, right, bottom, left = face.location
            
            # Draw rectangle
            cv2.rectangle(result_image, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Draw confidence score
            label = f"Face: {face.confidence:.2f}"
            cv2.putText(result_image, label, (left, top - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        return result_image
    
    def is_valid_face(self, detected_face: DetectedFace, min_confidence: float = 0.5) -> bool:
        """
        Check if a detected face meets quality criteria
        
        Args:
            detected_face: DetectedFace object to validate
            min_confidence: Minimum confidence threshold
            
        Returns:
            True if face meets criteria, False otherwise
        """
        # Check confidence
        if detected_face.confidence < min_confidence:
            return False
        
        # Check face size (minimum size requirements)
        top, right, bottom, left = detected_face.location
        width = right - left
        height = bottom - top
        
        if width < 50 or height < 50:  # Minimum 50x50 pixels
            return False
        
        # Check aspect ratio (faces should be roughly rectangular)
        aspect_ratio = width / height
        if aspect_ratio < 0.7 or aspect_ratio > 1.3:
            return False
        
        return True

# Test function for this module
def test_face_detection():
    """Test face detection with camera or sample image"""
    import time
    
    detector = FaceDetector()
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera for face detection test")
        return False
    
    print("🎥 Face detection test started")
    print("Press 'q' to quit, 's' to save current frame")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read from camera")
                break
            
            # Detect faces
            start_time = time.time()
            detected_faces = detector.detect_faces(frame)
            detection_time = time.time() - start_time
            
            # Draw face boxes
            result_frame = detector.draw_face_boxes(frame, detected_faces)
            
            # Add performance info
            info_text = f"Faces: {len(detected_faces)}, Time: {detection_time:.3f}s"
            cv2.putText(result_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show result
            cv2.imshow('Face Detection Test', result_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite('face_detection_test.jpg', result_frame)
                print("📸 Frame saved as 'face_detection_test.jpg'")
            
        print(f"✅ Face detection test completed")
        return True
        
    except Exception as e:
        print(f"❌ Face detection test error: {e}")
        return False
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Run test when module is executed directly
    logging.basicConfig(level=logging.INFO)
    test_face_detection()