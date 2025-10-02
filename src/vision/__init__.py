"""
Vision processing modules for the AI Guard Agent.
Includes face detection, recognition, and related computer vision functionality.
"""

from .face_detector import FaceDetector, DetectedFace
# from .face_recognizer import FaceRecognizer  # Will be added next

__all__ = ['FaceDetector', 'DetectedFace']