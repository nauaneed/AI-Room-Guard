"""
Face recognition module for the AI Guard Agent.
Handles face encoding, matching, and user identification.
"""

import face_recognition
import numpy as np
import cv2
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
import json
import os
from datetime import datetime
from src.utils.smart_logger import SmartLogger

try:
    from src.vision.face_detector import FaceDetector, DetectedFace
    from src.core.trust_manager import TrustManager, TrustLevel
    from src.core.response_system import ResponseSystem
except ImportError:
    try:
        from .face_detector import FaceDetector, DetectedFace
        from ..core.trust_manager import TrustManager, TrustLevel
        from ..core.response_system import ResponseSystem
    except ImportError:
        # For running as main module
        import sys
        from face_detector import FaceDetector, DetectedFace
        from trust_manager import TrustManager, TrustLevel
        from response_system import ResponseSystem
#     sys.path.append(os.path.dirname(os.path.dirname(__file__)))
#     from vision.face_detector import FaceDetector, DetectedFace

@dataclass
class RecognitionResult:
    """Result of face recognition attempt"""
    is_known: bool
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    confidence: float = 0.0
    distance: float = 1.0
    trust_level: Optional[TrustLevel] = None
    trust_score: float = 0.0
    access_granted: bool = False
    match_method: str = "face_recognition"

class FaceRecognizer:
    """Face recognition and matching functionality"""
    
    def __init__(self, tolerance: float = 0.6):
        """
        Initialize face recognizer
        
        Args:
            tolerance: Face matching tolerance (lower = more strict)
        """
        self.logger = SmartLogger(__name__)
        self.tolerance = tolerance
        
        # Initialize user database
        try:
            from src.core.user_database import TrustedUserDatabase
            self.user_database = TrustedUserDatabase()
        except ImportError:
            from core.user_database import TrustedUserDatabase
            self.user_database = TrustedUserDatabase()
        
        # Initialize trust manager
        try:
            from src.core.trust_manager import TrustManager
            self.trust_manager = TrustManager()
        except ImportError:
            from core.trust_manager import TrustManager
            self.trust_manager = TrustManager()
        
        # Initialize response system
        try:
            from src.core.response_system import ResponseSystem
            self.response_system = ResponseSystem()
        except ImportError:
            from core.response_system import ResponseSystem
            self.response_system = ResponseSystem()
        
        # Initialize face detector
        try:
            from src.vision.face_detector import FaceDetector
            self.face_detector = FaceDetector()
        except ImportError:
            from vision.face_detector import FaceDetector
            self.face_detector = FaceDetector()
        
        self.logger.info(f"Face recognizer initialized with tolerance: {tolerance}")
    
    def is_good_quality_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Tuple[bool, Dict]:
        """
        Check if a detected face meets quality requirements for enrollment
        
        Args:
            image: Input image as numpy array
            face_location: Face bounding box (top, right, bottom, left)
            
        Returns:
            Tuple of (is_good_quality, quality_metrics)
        """
        try:
            top, right, bottom, left = face_location
            
            # Calculate face dimensions
            face_width = right - left
            face_height = bottom - top
            image_height, image_width = image.shape[:2]
            
            # Quality metrics
            quality_metrics = {
                'face_width': face_width,
                'face_height': face_height,
                'face_area_ratio': (face_width * face_height) / (image_width * image_height),
                'aspect_ratio': face_width / face_height if face_height > 0 else 0,
                'image_size': (image_width, image_height)
            }
            
            # Quality checks
            checks = {
                'min_face_size': face_width >= 100 and face_height >= 100,
                'max_face_size': face_width <= image_width * 0.8 and face_height <= image_height * 0.8,
                'face_area_ratio': 0.05 <= quality_metrics['face_area_ratio'] <= 0.4,
                'aspect_ratio': 0.7 <= quality_metrics['aspect_ratio'] <= 1.3,
                'not_edge_crop': left > 10 and top > 10 and right < image_width - 10 and bottom < image_height - 10
            }
            
            quality_metrics['checks'] = checks
            is_good_quality = all(checks.values())
            
            return is_good_quality, quality_metrics
            
        except Exception as e:
            self.logger.error(f"Face quality check failed: {e}")
            return False, {}

    def generate_face_encoding(self, image: np.ndarray, face_location: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Generate face encoding for an image
        
        Args:
            image: Input image as numpy array
            face_location: Optional face location as (top, right, bottom, left)
            
        Returns:
            128-dimension face encoding or None if failed
        """
        try:
            # Convert BGR to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if face_location is not None:
                # Use provided face location
                face_locations = [face_location]
            else:
                # Detect face locations automatically
                face_locations = face_recognition.face_locations(rgb_image)
                
                if not face_locations:
                    self.logger.warning("No faces found in image for encoding")
                    return None
                
                if len(face_locations) > 1:
                    self.logger.warning(f"Multiple faces found ({len(face_locations)}), using the first one")
                
                face_location = face_locations[0]
            
            # Generate encoding
            encodings = face_recognition.face_encodings(rgb_image, [face_location])
            
            if encodings:
                encoding = encodings[0]
                self.logger.debug(f"Generated face encoding with shape: {encoding.shape}")
                return encoding
            else:
                self.logger.warning("Failed to generate face encoding")
                return None
                
        except Exception as e:
            self.logger.error(f"Face encoding generation error: {e}")
            return None
    
    def compare_faces(self, known_encodings: List[np.ndarray], face_encoding: np.ndarray) -> Tuple[List[bool], List[float]]:
        """
        Compare a face encoding against known encodings
        
        Args:
            known_encodings: List of known face encodings
            face_encoding: Face encoding to compare
            
        Returns:
            Tuple of (matches, distances) where matches is bool list and distances is float list
        """
        try:
            if not known_encodings:
                return [], []
            
            # Compare faces
            matches = face_recognition.compare_faces(
                known_encodings, 
                face_encoding, 
                tolerance=self.tolerance
            )
            
            # Calculate distances
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            
            self.logger.debug(f"Face comparison completed: {sum(matches)} matches out of {len(known_encodings)}")
            return matches, distances.tolist()
            
        except Exception as e:
            self.logger.error(f"Face comparison error: {e}")
            return [], []
    
    def find_best_match(self, known_encodings: List[np.ndarray], face_encoding: np.ndarray) -> Tuple[int, float]:
        """
        Find the best matching face from known encodings
        
        Args:
            known_encodings: List of known face encodings
            face_encoding: Face encoding to match
            
        Returns:
            Tuple of (best_match_index, confidence) or (-1, 0.0) if no match
        """
        matches, distances = self.compare_faces(known_encodings, face_encoding)
        
        if not matches or not np.any(matches):
            return -1, 0.0
        
        # Find the best match (lowest distance among matches)
        best_match_index = -1
        best_distance = float('inf')
        
        for i, (is_match, distance) in enumerate(zip(matches, distances)):
            if is_match and distance < best_distance:
                best_distance = distance
                best_match_index = i
        
        # Convert distance to confidence (0.0 to 1.0, higher is better)
        confidence = max(0.0, 1.0 - (best_distance / self.tolerance))
        
        return best_match_index, confidence
    
    def recognize_face(self, unknown_encoding: np.ndarray, required_trust_level: TrustLevel = TrustLevel.MEDIUM) -> Tuple[Optional[Dict], float]:
        """
        Recognize a face encoding against the trusted user database with trust evaluation
        
        Args:
            unknown_encoding: Face encoding to identify
            required_trust_level: Minimum trust level required for access
            
        Returns:
            Tuple of (user_info, confidence) where user_info is None if no match
        """
        try:
            # Get all known encodings from database
            all_encodings, all_user_ids = self.user_database.get_all_encodings()
            
            if not all_encodings:
                self.logger.warning("No known encodings in database")
                return None, 0.0
            
            # Compare against all known encodings
            matches = face_recognition.compare_faces(all_encodings, unknown_encoding, tolerance=self.tolerance)
            face_distances = face_recognition.face_distance(all_encodings, unknown_encoding)
            
            # Find the best match (handle numpy array properly)
            # Convert matches to numpy array if it isn't already
            matches = np.array(matches)
            if np.any(matches):
                # Get the index of the best match (lowest distance among matches)
                matched_indices = [i for i, match in enumerate(matches) if match]
                best_match_index = min(matched_indices, key=lambda i: face_distances[i])
                
                best_distance = face_distances[best_match_index]
                confidence = 1.0 - best_distance  # Convert distance to confidence
                
                # Get user info
                matched_user_id = all_user_ids[best_match_index]
                user_info = self.user_database.get_user(matched_user_id)
                
                if user_info:
                    # Update trust level based on recognition confidence
                    current_trust_level = self.trust_manager.record_recognition_event(
                        user_info['user_id'], confidence, f"Face recognition: {confidence:.3f}"
                    )
                    
                    # Get trust summary
                    trust_summary = self.trust_manager.get_trust_summary(user_info['user_id'])
                    trust_score = trust_summary['current_trust_score'] if trust_summary else 0.0
                    
                    # Check if access should be granted
                    access_granted = self.trust_manager.should_grant_access(user_info['user_id'], required_trust_level)
                    
                    # Generate appropriate response
                    response_event = self.response_system.generate_trusted_user_response(
                        user_id=user_info['user_id'],
                        user_name=user_info['name'],
                        confidence=confidence,
                        trust_level=current_trust_level.name,
                        trust_score=trust_score,
                        access_granted=access_granted
                    )
                    self.response_system.process_recognition_event(response_event)
                    
                    # Add trust information to user info
                    user_info['trust_level'] = current_trust_level
                    user_info['trust_score'] = trust_score
                    user_info['access_granted'] = access_granted
                    
                    self.logger.face_recognition_event(user_info['name'], confidence, access_granted)
                else:
                    self.logger.warning(f"User data not found for recognized face (ID: {matched_user_id})")
                
                return user_info, confidence
            else:
                # No matches found - unknown person
                min_distance = np.min(face_distances) if len(face_distances) > 0 else 1.0
                confidence = 1.0 - min_distance
                
                # Generate unknown person response
                response_event = self.response_system.generate_unknown_person_response(confidence)
                self.response_system.process_recognition_event(response_event)
                
                self.logger.face_recognition_event("Unknown Person", confidence, False)
                return None, confidence
                
        except Exception as e:
            self.logger.error(f"Face recognition failed: {e}")
            return None, 0.0

    def recognize_face_in_image(self, image_path: str) -> List[RecognitionResult]:
        """
        Recognize faces in an image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of RecognitionResult objects for each detected face
        """
        results = []
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Could not load image: {image_path}")
                return results
            
            # Detect faces in the image
            detected_faces = self.face_detector.detect_faces(image)
            
            for detected_face in detected_faces:
                # Generate encoding for this face
                face_encoding = self.generate_face_encoding(image, detected_face.location)
                
                if face_encoding is None:
                    # Could not generate encoding
                    results.append(RecognitionResult(
                        is_known=False,
                        confidence=0.0,
                        distance=1.0
                    ))
                    continue
                
                # Recognize the face
                user_info, confidence = self.recognize_face(face_encoding)
                
                if user_info:
                    # Known face found
                    distance = 1.0 - confidence  # Convert confidence back to distance
                    
                    results.append(RecognitionResult(
                        is_known=True,
                        user_id=user_info['user_id'],
                        user_name=user_info.get('name', 'Unknown'),
                        confidence=confidence,
                        distance=distance,
                        trust_level=user_info.get('trust_level'),
                        trust_score=user_info.get('trust_score', 0.0),
                        access_granted=user_info.get('access_granted', False)
                    ))
                else:
                    # Unknown face
                    results.append(RecognitionResult(
                        is_known=False,
                        confidence=confidence,
                        distance=1.0 - confidence,
                        trust_level=TrustLevel.UNKNOWN,
                        trust_score=0.0,
                        access_granted=False
                    ))
            
            self.logger.info(f"Processed {len(detected_faces)} faces in {image_path}")
            return results
            
        except Exception as e:
            self.logger.error(f"Face recognition in image failed: {e}")
            return results
    
    def extract_face_from_image(self, image: np.ndarray, face_location: Tuple[int, int, int, int], padding: int = 20) -> Optional[np.ndarray]:
        """
        Extract face region from image
        
        Args:
            image: Input image as numpy array
            face_location: Face location as (top, right, bottom, left)
            padding: Padding around face in pixels
            
        Returns:
            Cropped face image or None if failed
        """
        try:
            top, right, bottom, left = face_location
            
            # Add padding
            top = max(0, top - padding)
            right = min(image.shape[1], right + padding)
            bottom = min(image.shape[0], bottom + padding)
            left = max(0, left - padding)
            
            # Extract face region
            face_image = image[top:bottom, left:right]
            
            if face_image.size == 0:
                self.logger.warning("Extracted face image is empty")
                return None
            
            return face_image
            
        except Exception as e:
            self.logger.error(f"Face extraction error: {e}")
            return None
    
    def is_good_quality_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Tuple[bool, Dict[str, Any]]:
        """
        Assess the quality of a detected face for enrollment/recognition
        
        Args:
            image: Input image as numpy array
            face_location: Face location as (top, right, bottom, left)
            
        Returns:
            Tuple of (is_good_quality, quality_metrics)
        """
        try:
            top, right, bottom, left = face_location
            
            # Calculate face dimensions
            face_width = right - left
            face_height = bottom - top
            face_area = face_width * face_height
            
            # Quality metrics
            quality_metrics = {
                'face_width': face_width,
                'face_height': face_height,
                'face_area': face_area,
                'aspect_ratio': face_width / face_height if face_height > 0 else 0,
                'is_frontal': True,  # Placeholder - could add pose estimation
                'brightness_ok': True,  # Placeholder - could add brightness check
                'blur_ok': True  # Placeholder - could add blur detection
            }
            
            # Quality thresholds
            min_face_size = 100  # Minimum face width/height
            min_face_area = 10000  # Minimum face area
            aspect_ratio_range = (0.8, 1.2)  # Face should be roughly square
            
            # Check quality criteria
            is_good_quality = (
                face_width >= min_face_size and
                face_height >= min_face_size and
                face_area >= min_face_area and
                aspect_ratio_range[0] <= quality_metrics['aspect_ratio'] <= aspect_ratio_range[1]
            )
            
            quality_metrics['overall_quality'] = is_good_quality
            
            return is_good_quality, quality_metrics
            
        except Exception as e:
            self.logger.error(f"Face quality assessment error: {e}")
            return False, {}
    
    def draw_recognition_results(self, image: np.ndarray, results: List[RecognitionResult], face_locations: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Draw recognition results on image
        
        Args:
            image: Input image as numpy array
            results: List of RecognitionResult objects
            face_locations: List of face locations corresponding to results
            
        Returns:
            Image with recognition results drawn
        """
        result_image = image.copy()
        
        for result, location in zip(results, face_locations):
            top, right, bottom, left = location
            
            # Choose color based on recognition result
            if result.is_known:
                color = (0, 255, 0)  # Green for known faces
                label = f"{result.user_id}: {result.confidence:.2f}"
            else:
                color = (0, 0, 255)  # Red for unknown faces
                label = f"Unknown: {result.confidence:.2f}"
            
            # Draw rectangle
            cv2.rectangle(result_image, (left, top), (right, bottom), color, 2)
            
            # Draw label
            cv2.putText(result_image, label, (left, top - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        
        return result_image

# Test function for this module
def test_face_recognition():
    """Test face recognition with sample encodings"""
    import time
    
    recognizer = FaceRecognizer()
    
    # Create some dummy known encodings for testing
    known_encodings = []
    user_ids = []
    
    print("🎥 Face recognition test started")
    print("This will detect faces and try to recognize them")
    print("Press 'q' to quit")
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera for face recognition test")
        return False
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read from camera")
                break
            
            # Recognize faces
            start_time = time.time()
            results = recognizer.recognize_face_in_image(frame, known_encodings, user_ids)
            recognition_time = time.time() - start_time
            
            # Get face locations for drawing
            detected_faces = recognizer.face_detector.detect_faces(frame)
            face_locations = [face.location for face in detected_faces]
            
            # Draw results
            if results and face_locations:
                result_frame = recognizer.draw_recognition_results(frame, results, face_locations)
            else:
                result_frame = frame
            
            # Add performance info
            info_text = f"Faces: {len(results)}, Time: {recognition_time:.3f}s"
            cv2.putText(result_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show result
            cv2.imshow('Face Recognition Test', result_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
        print(f"✅ Face recognition test completed")
        return True
        
    except Exception as e:
        print(f"❌ Face recognition test error: {e}")
        return False
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Run test when module is executed directly
    logging.basicConfig(level=logging.INFO)
    test_face_recognition()