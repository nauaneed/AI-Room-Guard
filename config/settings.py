# Configuration settings for the AI Guard Agent

import os
from enum import Enum

class GuardState(Enum):
    """System states for the guard agent"""
    IDLE = "idle"
    LISTENING = "listening"
    GUARD_ACTIVE = "guard_active"
    PROCESSING = "processing"
    FACE_RECOGNITION = "face_recognition"

class AudioConfig:
    """Audio processing configuration"""
    CHUNK_SIZE = 1024
    FORMAT = "paInt16"  # Will be converted to pyaudio constant
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5  # Duration of each audio chunk
    
    # Speech recognition settings
    RECOGNITION_TIMEOUT = 5  # seconds
    PHRASE_TIMEOUT = 0.3  # seconds
    
    # Speech recognition backend
    SPEECH_BACKEND = "google"  # Options: "google", "whisper"
    WHISPER_MODEL = "medium"  # Options: "tiny", "base", "small", "medium", "large"
    
    # Activation commands
    ACTIVATION_COMMANDS = [
        "guard my room",
        "start guard mode", 
        "begin guarding",
        "activate guard",
        "activate surveillance"
    ]
    
    # Command matching threshold (for fuzzy matching)
    COMMAND_SIMILARITY_THRESHOLD = 0.8
    
    # Performance settings
    AUDIO_BUFFER_SIZE = 15  # number of audio chunks to keep in memory

class VideoConfig:
    """Camera configuration"""
    CAMERA_INDEX = 0  # Default camera
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    FPS = 5

class FaceRecognitionConfig:
    """Face recognition configuration"""
    # Recognition settings
    RECOGNITION_THRESHOLD = 0.6  # Confidence threshold for face recognition
    MIN_FACE_SIZE = 100  # Minimum face size in pixels
    FACE_DETECTION_METHOD = "hog"  # Options: "hog", "cnn"
    
    # Performance settings
    FACE_DETECTION_FRAME_SKIP = 2  # Process every nth frame for performance
    MAX_RECOGNITION_DISTANCE = 0.6  # Maximum face distance for recognition
    
    # Trusted user detection timing
    TRUSTED_USER_CHECK_INTERVAL = 10.0  # seconds to wait before checking for trusted user again
    TRUSTED_USER_IDLE_DURATION = 10.0  # seconds to completely stop face recognition after trusted user detected
    ESCALATION_FACE_CHECK_INTERVAL = 5.0  # seconds between face checks during escalation conversations
    
    # Database settings
    USER_DATABASE_DIR = "data/trusted_users"
    ENROLLMENT_PHOTOS_DIR = "data/enrollment_photos"
    
    # Security settings
    MIN_TRUST_LEVEL = 0.5  # Minimum trust level for access
    UNKNOWN_PERSON_ALERT = True  # Alert on unknown person detection
    
    # Logging
    LOG_RECOGNITION_EVENTS = True

class SystemConfig:
    """General system configuration"""
    LOG_LEVEL = "INFO"
    LOG_FILE = "data/logs/guard_agent.log"
    
    # Smart logging configuration
    ENABLE_PERIODIC_LOGGING = False  # Disable repetitive status messages
    ENABLE_EVENT_LOGGING = True     # Enable logging only for actual events
    PERIODIC_LOG_INTERVAL = 30.0    # If periodic logging enabled, log every N seconds
    
    # Event-based logging (only log when these things happen)
    LOG_EVENTS = {
        'state_changes': True,          # State transitions
        'face_detection': True,         # Face detected/lost
        'face_recognition': True,       # User recognized/unknown
        'audio_commands': True,         # Voice commands detected
        'escalation_events': True,      # Escalation start/stop
        'trust_changes': True,          # Trust score updates
        'system_events': True,          # Start/stop/errors
        'periodic_status': False,       # Regular "Guard mode is ACTIVE" messages
        'waiting_messages': False,      # "Waiting for next check" messages
    }
    
    # Directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    
    # Ensure directories exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Performance settings
    MAX_PROCESSING_TIME = 10  # seconds