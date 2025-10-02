# Milestone 1: Activation and Basic Input - Detailed Plan

## Overview
**Goal**: Agent activates via speech command (e.g., "Guard my room") and establishes basic system infrastructure.

**Success Criteria**: 
- Command recognition accuracy (90%+ on clear audio)
- Basic state management (guard mode on/off)
- Webcam/microphone access working

## File Structure for the Project

```
EE782_A2_AI_Guard/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── speech_recognizer.py
│   │   └── audio_recorder.py
│   ├── video/
│   │   ├── __init__.py
│   │   └── camera_handler.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── guard_agent.py
│   │   └── state_manager.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_audio.py
│   ├── test_camera.py
│   └── test_integration.py
├── data/
│   ├── audio_samples/
│   └── logs/
├── main.py
└── milestone_demos/
    └── milestone_1_demo.py
```

## Milestone 1 Breakdown - Small Testable Steps

### Step 1: Environment Setup and Dependencies (Day 1)
**Objective**: Set up the development environment with all required libraries.

**Tasks**:
1. Create virtual environment
2. Install core dependencies
3. Test basic imports
4. Create project structure

**Dependencies needed**:
- `speechrecognition` - for speech-to-text
- `pyaudio` - for microphone access
- `opencv-python` - for camera access
- `numpy` - for data processing
- `threading` - for concurrent operations (built-in)

**Test**: Run a simple script that imports all libraries without errors.

### Step 2: Audio Input Setup (Day 1-2)
**Objective**: Get microphone working and capture audio input.

**Sub-tasks**:
1. **Test microphone access**:
   - Create `test_microphone.py`
   - Record 5 seconds of audio
   - Save to file and play back
   - Verify audio quality

2. **Create AudioRecorder class**:
   - Initialize microphone
   - Start/stop recording
   - Handle audio chunks
   - Error handling for missing microphone

**Test**: Record your voice saying "Hello" and verify the audio file plays correctly.

### Step 3: Basic Speech Recognition (Day 2-3)
**Objective**: Convert speech to text using Google's Speech Recognition API.

**Sub-tasks**:
1. **Test Google Speech Recognition**:
   - Create simple script to recognize "Hello World"
   - Test with different audio qualities
   - Handle network connectivity issues

2. **Create SpeechRecognizer class**:
   - Process audio chunks in real-time
   - Return transcribed text
   - Handle recognition errors gracefully
   - Add confidence scoring

**Test**: Say "Guard my room" and verify it's transcribed correctly 9/10 times.

### Step 4: Command Detection Logic (Day 3-4)
**Objective**: Detect activation command with high accuracy.

**Sub-tasks**:
1. **Define activation phrases**:
   - Primary: "Guard my room"
   - Alternatives: "Start guard mode", "Begin guarding"
   - Case-insensitive matching

2. **Implement command matching**:
   - Fuzzy string matching for slight variations
   - Handle background noise
   - Prevent false positives

3. **Add command validation**:
   - Require command to be spoken clearly
   - Optional: Ask for confirmation "Did you say 'Guard my room'?"

**Test**: Test with 20 different pronunciations and background noise levels. Achieve 90%+ accuracy.

### Step 5: Camera Access Setup (Day 4-5)
**Objective**: Initialize and test webcam functionality.

**Sub-tasks**:
1. **Test camera access**:
   - Create `test_camera.py`
   - Capture single frame
   - Display video feed
   - Handle missing camera gracefully

2. **Create CameraHandler class**:
   - Initialize camera with proper resolution
   - Capture frames continuously
   - Release camera resources properly

**Test**: Display live video feed for 30 seconds without crashes.

### Step 6: State Management System (Day 5-6)
**Objective**: Implement system states (idle, listening, guard_mode).

**Sub-tasks**:
1. **Define system states**:
   ```python
   class GuardState(Enum):
       IDLE = "idle"
       LISTENING = "listening"  # Listening for activation command
       GUARD_ACTIVE = "guard_active"  # Guard mode is on
       PROCESSING = "processing"  # Processing input
   ```

2. **Create StateManager class**:
   - Track current state
   - Handle state transitions
   - Log state changes
   - Validate state transitions

3. **Implement state transition logic**:
   - IDLE → LISTENING (on audio detection)
   - LISTENING → GUARD_ACTIVE (on command recognition)
   - GUARD_ACTIVE → IDLE (on deactivation command)

**Test**: Manually trigger state changes and verify correct transitions.

### Step 7: Core Guard Agent Integration (Day 6-7)
**Objective**: Combine all components into main guard agent.

**Sub-tasks**:
1. **Create GuardAgent main class**:
   - Initialize all components
   - Coordinate between audio, video, and state management
   - Handle component failures gracefully

2. **Implement main loop**:
   - Continuous audio monitoring
   - Command detection and processing
   - State-based behavior

3. **Add logging and debugging**:
   - Log all state changes
   - Log recognized commands
   - Performance metrics

**Test**: Run complete system for 10 minutes, activate/deactivate multiple times.

### Step 8: Error Handling and Edge Cases (Day 7)
**Objective**: Make the system robust and handle failures.

**Sub-tasks**:
1. **Handle hardware failures**:
   - Missing microphone
   - Missing camera
   - Audio/video driver issues

2. **Handle network issues**:
   - No internet connection
   - Speech recognition API failures
   - Fallback to offline recognition

3. **Handle edge cases**:
   - Very quiet environment
   - Very noisy environment
   - Multiple people speaking

**Test**: Deliberately cause failures and verify graceful handling.

### Step 9: Testing and Validation (Day 8)
**Objective**: Comprehensive testing of Milestone 1 functionality.

**Sub-tasks**:
1. **Unit tests**:
   - Test each component individually
   - Mock external dependencies
   - Test error conditions

2. **Integration tests**:
   - Test component interactions
   - Test full activation flow
   - Performance benchmarks

3. **User acceptance testing**:
   - Test with different voices
   - Test in different environments
   - Test with background noise

**Test**: Run automated test suite with 95%+ pass rate.

### Step 10: Demo Preparation (Day 8-9)
**Objective**: Create a polished demo for Milestone 1.

**Sub-tasks**:
1. **Create demo script**:
   - Clear demonstration of activation
   - Show state transitions
   - Display system feedback

2. **Record demo video**:
   - Show system startup
   - Demonstrate activation command
   - Show guard mode activation
   - Include audio and visual feedback

3. **Prepare documentation**:
   - Update README with current status
   - Document known issues
   - Provide setup instructions

## Technical Implementation Details

### Audio Processing Pipeline
```
Microphone → PyAudio → Audio Chunks → Speech Recognition → Text → Command Detection → State Change
```

### Key Classes and Methods

#### AudioRecorder
```python
class AudioRecorder:
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
    def start_recording(self):
        # Start continuous recording
        
    def stop_recording(self):
        # Stop and cleanup
        
    def get_audio_chunk(self):
        # Return audio data
```

#### SpeechRecognizer
```python
class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def recognize_speech(self, audio_data):
        # Convert audio to text
        
    def is_activation_command(self, text):
        # Check if text contains activation phrase
```

#### GuardAgent
```python
class GuardAgent:
    def __init__(self):
        self.state_manager = StateManager()
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.camera_handler = CameraHandler()
        
    def run(self):
        # Main loop
        
    def process_audio(self):
        # Handle audio input
        
    def handle_activation(self):
        # Process activation command
```

## Success Metrics for Milestone 1

1. **Command Recognition**: 90%+ accuracy on clear audio
2. **Response Time**: < 3 seconds from command to activation
3. **False Positives**: < 5% false activation rate
4. **System Stability**: Run for 30+ minutes without crashes
5. **Resource Usage**: < 50% CPU usage during normal operation

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies (microphone, camera)
- Test error conditions and edge cases

### Integration Tests
- Test component interactions
- Test full workflow from audio input to state change
- Performance and stress testing

### Manual Testing
- Test with different users/voices
- Test in various environments (quiet, noisy)
- Test edge cases (unclear speech, background conversations)

## Common Issues and Solutions

1. **PyAudio Installation Issues**:
   - On Linux: `sudo apt-get install portaudio19-dev`
   - Use conda if pip fails

2. **Permission Issues**:
   - Microphone permissions on macOS/Linux
   - Camera access permissions

3. **Speech Recognition Accuracy**:
   - Adjust microphone sensitivity
   - Use noise cancellation
   - Implement confidence thresholds

4. **Performance Issues**:
   - Optimize audio chunk processing
   - Use threading for concurrent operations
   - Implement proper resource cleanup

## Next Steps After Milestone 1

Once Milestone 1 is complete, you'll have:
- Working speech command activation
- Basic audio/video input
- State management system
- Foundation for face recognition (Milestone 2)
- Framework for LLM integration (Milestone 3)

The system will be ready to add face recognition and more sophisticated interaction logic in subsequent milestones.