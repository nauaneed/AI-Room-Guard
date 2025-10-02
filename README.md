# AI Guard Agent - EE782 Assignment 2
_This assignment was done individually by me and not as a team of two as I could not find a partner with
matching timings along with complementary skills._

An AI-powered room guard system that uses webcam, microphone, and speakers to monitor spaces and interact with visitors.

## Milestones
- [x] **Milestone 1: Activation and Basic Input** ✅ COMPLETE
- [x] **Milestone 2: Face Recognition and Trusted User Enrollment** ✅ COMPLETE  
- [x] **Milestone 3: Escalation Dialogue and Full Integration** ✅ COMPLETE
- [x] Milestone 4: Polish and Stretch Goals (Optional) ✅ COMPLETE


## How to

### Install deps
```bash
pip install -r reqs.txt
```

# Set env vars

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH # Since all imports are relative to project root
export GEMINI_PROJECT_ID="yourprojectid"
export GOOGLE_GEMINI_API_KEY='yourprojectkey"

```

# Add face
```bash
python enrollment/enroll_user.py
```
and follow instructions. Note userid and username for next step.

# Set trust level

```python
from src.core.trust_manager import TrustManager, TrustLevel
tm = TrustManager()
profile = tm.create_trust_profile('userid', 'username', TrustLevel.MEDIUM)
print(f'Trust Level: {profile.base_trust_level.name}')
print(f'Trust Score: {profile.current_trust_score}')
```


### Running the System
```bash
python main.py
```

## Features

- **LLM Integration**: Intelligent dialogue generation with Google Gemini (rate limit applicable)
- **Text-to-Speech**: Real-time audio output with natural voice
- **4-Level Escalation**: Progressive conversation escalation system
- **Complete Integration**: All AI modalities working seamlessly together
- **Performance**: <3s end-to-end response time suitable for real-time use

Following implemented

- [x] Voice activation system with dual backends
- [x] Real-time audio processing
- [x] State management
- [x] Face recognition for trusted users
- [x] Escalating conversation with intruders
- [x] Text-to-speech responses
- [x] Logging and monitoring


## Speech Recognition Backends

The system supports two speech recognition backends:

### Google Speech Recognition (Default Backend)
- **Pros**: Fast processing, cloud-based
- **Cons**: Requires internet, API rate limits

### Whisper (Non Default Backend)
- **Pros**: Works offline, 
- **Cons**: Slower processing, requires more CPU/memory


### Configuration
Edit `config/settings.py` to change backend:
```python
class AudioConfig:
    SPEECH_BACKEND = "whisper"  # or "google"
    WHISPER_MODEL = "base"      # tiny, base, small, medium, large
```


## TTS Backends

The system supports two speech recognition backends:

### Gemini Flash TTS Preview (Default Backend)
- **Pros**: Very natural sounding, high quality
- **Cons**: Very stingy API rate limits, default output is .pcm, needs extra ffmpeg step for to convert to playable format

### gTTS
- **Pros**: Generous rate limits
- **Cons**: Voice not so natural

## Face Detection and Recognition

The system uses OpenCV and `face_recognition` libraries for robust face detection and recognition:

### Face Detection
- Utilizes OpenCV's to locate faces in video frames.
- Real-time detection from webcam feed.
- Crops and aligns detected faces for further processing.

### Face Recognition
- Employs the `face_recognition` library (built on dlib) for encoding and matching faces.
- Each enrolled user has a unique face encoding stored securely.
- On detection, the system compares the face encoding with known users to identify trusted individuals.
- Recognition is threshold-based to minimize false positives.


### Security
- Face data is stored locally and not uploaded to any cloud service.
- Recognition is performed in real-time for seamless user experience.
- Only trusted users can bypass escalation protocols.
- Unrecognized faces trigger the escalation dialogue.


## Project Structure


## Project Directory Structure

```
EE782/a2_submit/
├── main.py                          # Main application entry point
├── README.md                        # Readme
├── reqs.txt                         # Python dependencies (latest)
├── requirements.txt                 # Python dependencies (old)
│
├── config/                          # Configuration
│   ├── __init__.py
│   ├── settings.py                  # actual configuration
│
├── src/                             # Main Source Code
│   ├── __init__.py
│   │
│   ├── audio/                       # Audio Processing Modules
│   │   ├── __init__.py
│   │   ├── audio_player.py          # Audio playback functionality
│   │   ├── audio_recorder.py        # Microphone recording functionality
│   │   ├── speech_recognizer.py     # Speech-to-text processing (Google/Whisper)
│   │   └── tts_manager.py           # Text-to-speech management (Gemini/gTTS)
│   │
│   ├── core/                        # Core System Logic
│   │   ├── __init__.py
│   │   ├── guard_agent.py           # Main guard agent orchestrator
│   │   ├── performance_profiler.py  # System performance monitoring
│   │   ├── response_system.py       # Response coordination system
│   │   ├── state_manager.py         # Application state management
│   │   ├── trust_manager.py         # User trust level management
│   │   └── user_database.py         # User data storage and retrieval
│   │
│   ├── dialogue/                    # Conversation Management
│   │   ├── __init__.py
│   │   ├── conversation_controller.py # Conversation flow control
│   │   ├── escalation_manager.py    # 4-level escalation system
│   │   └── response_generator.py    # Dynamic response generation
│   │
│   ├── llm/                         # Large Language Model Integration
│   │   ├── __init__.py
│   │   ├── dialogue_generator.py    # AI dialogue generation with Gemini
│   │   └── llm_config.py           # LLM configuration and settings
│   │
│   ├── utils/                       # Utility Functions
│   │   ├── __init__.py
│   │   ├── logger.py                # Basic logging functionality
│   │   └── smart_logger.py          # Advanced logging with context
│   │
│   ├── video/                       # Video Processing
│   │   ├── __init__.py
│   │   └── camera_handler.py        # Webcam capture and management
│   │
│   └── vision/                      # Computer Vision
│       ├── __init__.py
│       ├── face_detector.py         # Face detection using OpenCV
│       ├── face_recognizer.py       # Face recognition and matching
│       └── optimized_face_detector.py # Performance-optimized face detection
│
├── data/                            # Data Storage
│
├── enrollment/                      # User Enrollment System
│   └── enroll_user.py               # Face enrollment script for new users
│
├── milestone_demos/                 # Milestone Demonstration Scripts
│   ├── integration_demo.py          # Full system integration demo
│   ├── milestone_1_demo.py          # Milestone 1: Activation and basic input
│   ├── milestone_2_realtime_demo.py # Milestone 2: Real-time face recognition
│   ├── milestone3_demo.py           # Milestone 3: Complete system demo
│   ├── response_system_demo.py      # Response system demonstration
│   └── trust_management_demo.py     # Trust management system demo
│
├── scripts/                         # Utility Scripts
│   ├── debug_frame_skipping.py      # Frame processing debugging
│   ├── frame_skipping_test.py       # Frame skipping performance test
│   ├── initialize_trust.py          # Trust system initialization
│   ├── performance_baseline.py      # Performance baseline measurement
│   ├── performance_comparison.py    # Performance comparison tools
│   └── quick_performance_test.py    # Quick performance validation
│
├── tests/                           # Tests
│
└── docs/                            # Documentation and interim notes

```