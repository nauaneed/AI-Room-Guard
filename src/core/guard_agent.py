"""
Main Guard Agent module for the AI Guard Agent.
Coordinates all components and implements the main system logic.
"""

import logging
import threading
import time
import queue
from typing import Optional, Dict, Any
from config.settings import GuardState, AudioConfig, FaceRecognitionConfig
from src.core.state_manager import StateManager
from src.audio.audio_recorder import AudioRecorder
from src.audio.speech_recognizer import SpeechRecognizer
from src.video.camera_handler import CameraHandler
from src.vision.face_detector import FaceDetector
from src.vision.face_recognizer import FaceRecognizer
from src.core.user_database import TrustedUserDatabase
from src.dialogue.conversation_controller import ConversationController
from src.utils.smart_logger import get_smart_logger

class GuardAgent:
    """Main AI Guard Agent that coordinates all components"""
    
    def __init__(self):
        self.logger = get_smart_logger(__name__)
        self.raw_logger = logging.getLogger(__name__)  # Keep raw logger for some uses
        
        # Initialize components
        self.state_manager = StateManager()
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.camera_handler = CameraHandler()
        
        # Face recognition components
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.user_database = TrustedUserDatabase()
        
        # Conversation and escalation system
        self.conversation_controller = ConversationController()
        
        # Control flags
        self.is_running = False
        self.should_stop = threading.Event()
        self.camera_active = False  # Track if camera is active
        self.camera_initialized = False  # Track if camera is initialized
        
        # Threading
        self.main_thread = None
        self.audio_processing_thread = None
        self.face_recognition_thread = None
        
        # Audio processing
        self.audio_queue = queue.Queue(maxsize=AudioConfig.AUDIO_BUFFER_SIZE)
        
        # Face recognition processing
        self.face_recognition_queue = queue.Queue(maxsize=10)
        self.frame_skip_counter = 0
        
        # Performance tracking
        self.stats = {
            'start_time': None,
            'commands_processed': 0,
            'audio_chunks_processed': 0,
            'activations': 0,
            'false_positives': 0,
            'faces_detected': 0,
            'trusted_recognitions': 0,
            'unknown_detections': 0
        }
        
        # Trusted user detection tracking
        self.last_trusted_user_detection = 0.0  # Timestamp of last trusted user detection
        self.face_recognition_idle_until = 0.0  # Timestamp until when face recognition should idle
        self.last_escalation_face_check = 0.0  # Timestamp of last face check during escalation
        
        # Setup state change callbacks
        self.state_manager.add_state_changed_callback(self._on_state_changed)
        
        self.logger.info("Guard Agent initialized")
    
    def initialize(self) -> bool:
        """Initialize all components and verify functionality"""
        self.logger.info("Initializing Guard Agent components...")
        
        # Initialize audio recorder
        if not self.audio_recorder.initialize():
            self.logger.error("Failed to initialize audio recorder")
            return False
        
        # Don't initialize camera yet - only when guard is activated
        # Camera will be initialized when state changes to GUARD_ACTIVE
        
        # Test speech recognizer (no initialization needed)
        self.logger.info("Speech recognizer ready")
        
        self.logger.info("All components initialized successfully")
        return True
    
    def start(self) -> bool:
        """Start the guard agent"""
        if self.is_running:
            self.logger.warning("Guard agent is already running")
            return False
        
        if not self.initialize():
            self.logger.error("Failed to initialize components")
            return False
        
        self.is_running = True
        self.should_stop.clear()
        self.stats['start_time'] = time.time()
        
        # Start audio recording
        if not self.audio_recorder.start_recording():
            self.logger.error("Failed to start audio recording")
            self.is_running = False
            return False
        
        # Don't start camera capture yet - only when guard is activated
        
        # Start main processing thread
        self.main_thread = threading.Thread(target=self._main_loop)
        self.main_thread.daemon = True
        self.main_thread.start()
        
        # Start audio processing thread
        self.audio_processing_thread = threading.Thread(target=self._audio_processing_loop)
        self.audio_processing_thread.daemon = True
        self.audio_processing_thread.start()
        
        # Start face recognition thread
        self.face_recognition_thread = threading.Thread(target=self._face_recognition_loop)
        self.face_recognition_thread.daemon = True
        self.face_recognition_thread.start()
        
        # Change to listening state
        self.state_manager.change_state(GuardState.LISTENING, {'reason': 'agent started'})
        
        self.logger.info("Guard Agent started successfully")
        return True
    
    def stop(self):
        """Stop the guard agent"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping Guard Agent...")
        
        self.is_running = False
        self.should_stop.set()
        
        # Stop audio and video
        self.audio_recorder.stop_recording()
        if self.camera_active:
            self.camera_handler.stop_capture()
            self.camera_active = False
        if self.camera_initialized:
            self.camera_handler.cleanup()
            self.camera_initialized = False
        
        # Stop any active conversations
        if hasattr(self, 'conversation_controller') and self.conversation_controller.is_conversation_active:
            self.logger.info("🛑 Stopping active conversation...")
            self.conversation_controller.end_conversation("system_shutdown")
        
        # Wait for threads to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5.0)
        
        if self.audio_processing_thread and self.audio_processing_thread.is_alive():
            self.audio_processing_thread.join(timeout=5.0)
        
        if self.face_recognition_thread and self.face_recognition_thread.is_alive():
            self.face_recognition_thread.join(timeout=5.0)
            self.audio_processing_thread.join(timeout=5.0)
        
        # Return to idle state
        self.state_manager.change_state(GuardState.IDLE, {'reason': 'agent stopped'})
        
        self.logger.info("Guard Agent stopped")
    
    def _main_loop(self):
        """Main processing loop"""
        self.logger.system_event("Main loop started")
        
        while self.is_running and not self.should_stop.is_set():
            try:
                # Get current state
                current_state = self.state_manager.current_state
                
                if current_state == GuardState.LISTENING:
                    self._handle_listening_state()
                elif current_state == GuardState.PROCESSING:
                    self._handle_processing_state()
                elif current_state == GuardState.GUARD_ACTIVE:
                    self._handle_guard_active_state()
                elif current_state == GuardState.IDLE:
                    self._handle_idle_state()
                
                # Brief sleep to prevent tight loop (reduced for better concurrency)
                time.sleep(0.05)  # Reduced from 0.1s to 0.05s for faster response
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(1.0)  # Longer sleep on error
        
        self.logger.system_event("Main loop ended")
    
    def _audio_processing_loop(self):
        """Audio processing loop running in separate thread"""
        self.logger.system_event("Audio processing loop started")
        
        audio_buffer = []
        buffer_duration = 0.0
        target_duration = 3.0  # Process 3 seconds of audio at a time (optimized for responsiveness)
        
        while self.is_running and not self.should_stop.is_set():
            try:
                # Get audio chunk
                audio_chunk = self.audio_recorder.get_audio_chunk(timeout=0.5)
                
                if audio_chunk is None:
                    continue
                
                # Add to buffer
                audio_buffer.append(audio_chunk)
                buffer_duration += AudioConfig.CHUNK_SIZE / AudioConfig.RATE
                
                # Process when we have enough audio
                if buffer_duration >= target_duration:
                    combined_audio = b''.join(audio_buffer)
                    
                    # Add to processing queue with intelligent dropping
                    try:
                        self.audio_queue.put_nowait({
                            'audio_data': combined_audio,
                            'timestamp': time.time(),
                            'duration': buffer_duration
                        })
                        self.stats['audio_chunks_processed'] += 1
                    except queue.Full:
                        # Drop the oldest audio chunk to make room for new one
                        try:
                            old_chunk = self.audio_queue.get_nowait()
                            self.logger.debug(f"Dropped old audio chunk (age: {time.time() - old_chunk['timestamp']:.1f}s)")
                            # Try to add the new chunk again
                            self.audio_queue.put_nowait({
                                'audio_data': combined_audio,
                                'timestamp': time.time(),
                                'duration': buffer_duration
                            })
                            self.stats['audio_chunks_processed'] += 1
                        except queue.Empty:
                            # Queue became empty somehow, just log and continue
                            self.logger.warning("Audio queue was unexpectedly empty")
                        except queue.Full:
                            # Still full after dropping one, something's really wrong
                            self.logger.warning("Audio queue full even after dropping old chunk")
                    
                    # Reset buffer
                    audio_buffer = []
                    buffer_duration = 0.0
                
            except Exception as e:
                self.logger.error(f"Error in audio processing loop: {e}")
                time.sleep(0.5)
        
        self.logger.system_event("Audio processing loop ended")
    
    def _handle_listening_state(self):
        """Handle listening state - wait for activation commands (concurrent processing)"""
        try:
            # Check for audio to process (non-blocking)
            audio_item = self.audio_queue.get(timeout=0.1)
            
            # Process audio for commands WITHOUT changing state (concurrent processing)
            # This allows continuous listening while processing commands
            is_command, text, confidence = self.speech_recognizer.process_audio_chunk(
                audio_item['audio_data'], AudioConfig.RATE
            )
            
            self.stats['commands_processed'] += 1
            
            if is_command:
                self.logger.audio_command_event(text, confidence)
                self.stats['activations'] += 1
                
                # Activate guard mode
                self.state_manager.change_state(GuardState.GUARD_ACTIVE, {
                    'reason': 'activation command',
                    'command': text,
                    'confidence': confidence
                })
            # Note: No else clause to return to LISTENING - we stay in LISTENING for concurrent processing
            
        except queue.Empty:
            # No audio to process, continue listening
            pass
    
    def _handle_processing_state(self):
        """Handle processing state - currently just transitions back"""
        # In Milestone 1, processing is handled in the listening state
        # This state exists for future expansion
        time.sleep(0.1)
    
    def _handle_guard_active_state(self):
        """Handle guard active state - monitor for intruders (concurrent processing)"""
        self.logger.periodic_status("Guard mode is ACTIVE - monitoring room", "guard_active")
        
        # Check for deactivation command and conversation responses (reduced timeout for better responsiveness)
        try:
            audio_item = self.audio_queue.get(timeout=0.2)  # Reduced from 1.0s to 0.2s for better concurrency
            
            is_command, text, confidence = self.speech_recognizer.process_audio_chunk(
                audio_item['audio_data'], AudioConfig.RATE
            )
            
            if text:
                # Check for deactivation commands FIRST (highest priority)
                if (any(word in text.lower() for word in ['stop', 'deactivate', 'turn off', 'exit']) or
                    any(phrase in text.lower() for phrase in [
                        'stop surveillance', 'stop surveilance', 'end surveillance', 'disable guard',
                        'stop silence', 'top silence', 'stop guard', 'end guard', 'turn off guard'
                    ])):
                    self.logger.audio_command_event(text, 1.0)  # Deactivation commands are high priority
                    
                    # End any active conversation first
                    if (hasattr(self, 'conversation_controller') and 
                        self.conversation_controller.is_conversation_active):
                        print("🔚 Ending conversation due to deactivation command")
                        self.conversation_controller.end_conversation("user_deactivation")
                    
                    self.state_manager.change_state(GuardState.LISTENING, {'reason': 'deactivation command'})
                
                # Check if we have an active conversation (lower priority than deactivation)
                elif (hasattr(self, 'conversation_controller') and 
                      self.conversation_controller.is_conversation_active and
                      self.conversation_controller.waiting_for_response):
                    
                    # Route audio to conversation controller for response analysis
                    print(f"🎤 Routing response to conversation: '{text}'")
                    analysis = self.conversation_controller.process_person_response(text)
                    print(f"📊 Response analysis: {analysis}")
                    
                else:
                    # Log other audio when not in conversation, or during escalation waiting
                    is_escalation_active = (hasattr(self, 'conversation_controller') and 
                                          self.conversation_controller.is_conversation_active)
                    
                    if not is_escalation_active:
                        print(f"🎤 Audio detected: '{text}' (no active conversation)")
                    else:
                        # During escalation - show that we're still listening
                        current_time = time.time()
                        time_since_face_check = current_time - self.last_escalation_face_check
                        next_face_check_in = FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL - time_since_face_check
                        print(f"🎤🚨 Audio during escalation: '{text}' (next face check in {max(0, next_face_check_in):.1f}s)")
            
        except queue.Empty:
            pass
    
    def _handle_idle_state(self):
        """Handle idle state - minimal activity"""
        time.sleep(1.0)
    
    def _face_recognition_loop(self):
        """Face recognition processing loop"""
        self.logger.system_event("Face recognition loop started")
        
        while self.is_running and not self.should_stop.is_set():
            try:
                # Only process if camera is active (guard mode is on)
                if not self.camera_active:
                    time.sleep(0.5)  # Check every 500ms when camera is off
                    continue
                
                # Check if face recognition should be idle (non-blocking)
                current_time = time.time()
                if current_time < self.face_recognition_idle_until:
                    time.sleep(0.1)  # Short sleep, allows audio processing to continue
                    continue
                
                # Check if we're in escalation mode and should use different timing
                is_escalation_active = (hasattr(self, 'conversation_controller') and 
                                      self.conversation_controller.is_conversation_active)
                
                if is_escalation_active:
                    # During escalation: check face recognition every 5 seconds
                    if current_time - self.last_escalation_face_check < FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL:
                        time_until_next = FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL - (current_time - self.last_escalation_face_check)
                        # Print waiting status every 2 seconds to show system is active
                        if int(current_time * 2) % 4 == 0:  # Every 2 seconds with reduced frequency
                            self.logger.waiting_message(f"⏳ Escalation: Waiting {time_until_next:.1f}s for next face check (listening for audio...)", "escalation_waiting")
                        time.sleep(0.5)  # Check less frequently during escalation
                        continue
                    self.last_escalation_face_check = current_time
                    print(f"🔍 ESCALATION FACE CHECK - Scanning for trusted users...")
                    self.logger.info(f"🔍 Escalation face check at {current_time:.1f}s - checking for trusted users")
                
                # Skip frames for performance if configured (but not during escalation checks)
                if not is_escalation_active:
                    self.frame_skip_counter += 1
                    if self.frame_skip_counter < FaceRecognitionConfig.FACE_DETECTION_FRAME_SKIP:
                        time.sleep(0.033)  # ~30 FPS
                        continue
                    self.frame_skip_counter = 0
                
                # Get latest frame from camera
                frame = self.camera_handler.get_current_frame()
                if frame is None:
                    continue
                
                # Add frame to processing queue (non-blocking)
                try:
                    self.face_recognition_queue.put_nowait({
                        'frame': frame,
                        'timestamp': time.time()
                    })
                except queue.Full:
                    # Drop old frames if queue is full
                    try:
                        self.face_recognition_queue.get_nowait()
                        self.face_recognition_queue.put_nowait({
                            'frame': frame,
                            'timestamp': time.time()
                        })
                    except queue.Empty:
                        pass
                
                # Process face recognition
                self._process_face_recognition()
                
            except Exception as e:
                self.logger.error(f"Error in face recognition loop: {e}")
                time.sleep(0.5)
        
        self.logger.system_event("Face recognition loop ended")
    
    def _process_face_recognition(self):
        """Process face recognition on queued frames"""
        try:
            # Get frame from queue
            frame_item = self.face_recognition_queue.get(timeout=0.1)
            
            frame = frame_item['frame']
            timestamp = frame_item['timestamp']
            
            # Detect faces
            detected_faces = self.face_detector.detect_faces(frame)
            
            if detected_faces:
                self.stats['faces_detected'] += len(detected_faces)
                
                # Process each detected face
                for face in detected_faces:
                    # Generate face encoding
                    face_encoding = self.face_recognizer.generate_face_encoding(frame, face.location)
                    
                    if face_encoding is not None:
                        # Try to recognize the face
                        user_info, confidence = self.face_recognizer.recognize_face(face_encoding)
                        
                        if user_info and confidence >= FaceRecognitionConfig.RECOGNITION_THRESHOLD:
                            # Trusted user recognized
                            self.stats['trusted_recognitions'] += 1
                            self.last_trusted_user_detection = timestamp
                            self._handle_trusted_user_detected(user_info, confidence, timestamp)
                        else:
                            # Unknown person detected
                            self.stats['unknown_detections'] += 1
                            self._handle_unknown_person_detected(confidence, timestamp)
                            
        except queue.Empty:
            # No frames to process
            pass
        except Exception as e:
            self.logger.error(f"Error processing face recognition: {e}")
    
    def _handle_trusted_user_detected(self, user_info: Dict[str, Any], confidence: float, timestamp: float):
        """Handle trusted user detection with trust management"""
        user_name = user_info.get('name', 'Unknown')
        user_id = user_info.get('user_id', 'unknown')
        trust_level = user_info.get('trust_level')
        trust_score = user_info.get('trust_score', 0.0)
        access_granted = user_info.get('access_granted', False)
        
        self.logger.info(f"✅ Trusted user detected: {user_name} (confidence: {confidence:.3f}, "
                        f"trust: {trust_level.name if trust_level else 'N/A'}, "
                        f"score: {trust_score:.3f}, access: {access_granted})")
        
        # If there's an active escalation conversation, stop it since we now have a trusted user
        if (hasattr(self, 'conversation_controller') and 
            self.conversation_controller.is_conversation_active):
            self.logger.info(f"🛑 Stopping escalation conversation - trusted user {user_name} identified")
            self.logger.info(f"🔄 Conversation will end and normal trusted user greeting will proceed")
            self.conversation_controller.end_conversation("trusted_user_identified")
        
        # Set face recognition to idle for the configured duration (non-blocking approach)
        self.face_recognition_idle_until = time.time() + FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION
        self.logger.info(f"😴 Face recognition will idle for {FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION}s after detecting {user_name} (audio processing continues)")
        
        # Update last seen in database
        self.user_database.update_last_seen(user_id)
        
        # Log access granted but DON'T change states - stay in GUARD_ACTIVE to avoid camera cycling
        current_state = self.state_manager.current_state
        if current_state == GuardState.GUARD_ACTIVE and access_granted:
            self.logger.info(f"🔓 Access granted to {user_name} based on trust level (staying in guard mode)")
        elif current_state == GuardState.GUARD_ACTIVE and not access_granted:
            self.logger.warning(f"🔒 Access denied to {user_name} - insufficient trust level (staying in guard mode)")
    
    def _handle_unknown_person_detected(self, confidence: float, timestamp: float):
        """Handle unknown person detection"""
        self.logger.warning(f"⚠️ Unknown person detected (confidence: {confidence:.3f})")
        
        # If unknown person alert is enabled and we're in guard mode
        current_state = self.state_manager.current_state
        if (FaceRecognitionConfig.UNKNOWN_PERSON_ALERT and 
            current_state == GuardState.GUARD_ACTIVE):
            
            # Only start conversation if one isn't already active
            if not self.conversation_controller.is_conversation_active:
                # Start escalation conversation with unknown person
                person_id = f"unknown_person_{int(timestamp)}"
                self.logger.warning(f"🚨 Starting escalation conversation with {person_id}")
                
                # Start conversation in background thread
                conversation_thread = threading.Thread(
                    target=self._start_escalation_conversation,
                    args=(person_id, confidence),
                    daemon=True
                )
                conversation_thread.start()
                
                # STAY in GUARD_ACTIVE state - don't change to FACE_RECOGNITION
                # This allows face recognition and guard monitoring to continue during conversation
                self.logger.info("🔴 Guard remaining active during escalation conversation")
            else:
                self.logger.info("💬 Conversation already active, not starting new one")

    def _start_escalation_conversation(self, person_id: str, confidence: float):
        """Start escalation conversation with unknown person"""
        try:
            self.logger.info(f"🗣️  Starting conversation with {person_id}")
            
            # Start the conversation
            self.conversation_controller.start_conversation(person_id)
            
            # Monitor conversation status
            conversation_duration = 0
            check_interval = 2.0
            max_conversation_time = 120.0  # 2 minutes max
            
            while (self.conversation_controller.is_conversation_active and 
                   conversation_duration < max_conversation_time and 
                   self.is_running):
                
                time.sleep(check_interval)
                conversation_duration += check_interval
                
                # Log progress
                if conversation_duration % 10 == 0:  # Every 10 seconds
                    level = self.conversation_controller.escalation.current_level
                    self.logger.info(f"📊 Conversation active: {conversation_duration:.0f}s, Level: {level.value}")
            
            # End conversation if still active
            if self.conversation_controller.is_conversation_active:
                self.logger.info(f"🏁 Ending conversation with {person_id} (timeout)")
                self.conversation_controller.end_conversation("timeout")
            
            # DON'T change state - stay in GUARD_ACTIVE to continue monitoring
            self.logger.info("🔴 Conversation ended - guard remains active")
            
        except Exception as e:
            self.logger.error(f"❌ Error in escalation conversation: {e}")
            # DON'T change state on error either - stay in guard mode
            self.logger.info("🔴 Conversation error - guard remains active")

    def _on_state_changed(self, old_state: GuardState, new_state: GuardState, context: Dict[str, Any]):
        """Callback for state changes"""
        self.logger.info(f"State transition: {old_state.value} -> {new_state.value}")
        
        # Handle camera initialization and activation based on guard state
        if new_state == GuardState.GUARD_ACTIVE and not self.camera_active:
            self.logger.info("🎥 Initializing and starting camera for guard mode...")
            
            # Initialize camera if not already done
            if not self.camera_initialized:
                if self.camera_handler.initialize():
                    self.camera_initialized = True
                    self.logger.info("✅ Camera initialized successfully")
                else:
                    self.logger.error("❌ Failed to initialize camera")
                    return
            
            # Start camera capture
            if self.camera_handler.start_capture():
                self.camera_active = True
                self.logger.info("✅ Camera started successfully")
            else:
                self.logger.error("❌ Failed to start camera")
                
        elif old_state == GuardState.GUARD_ACTIVE and self.camera_active:
            self.logger.info("🎥 Stopping and releasing camera...")
            self.camera_handler.stop_capture()
            self.camera_active = False
            
            # Also release/cleanup the camera to turn off the light
            if self.camera_initialized:
                self.camera_handler.cleanup()
                self.camera_initialized = False
                self.logger.info("✅ Camera released - light should be off")
        
        # Log important state changes
        if new_state == GuardState.GUARD_ACTIVE:
            self.logger.warning("🔴 GUARD MODE ACTIVATED 🔴")
        elif old_state == GuardState.GUARD_ACTIVE:
            self.logger.info("🟢 Guard mode deactivated")
        elif new_state == GuardState.FACE_RECOGNITION:
            reason = context.get('reason', 'unknown')
            if reason == 'trusted_user_detected':
                user_name = context.get('user_name', 'Unknown')
                confidence = context.get('confidence', 0.0)
                self.logger.info(f"👤 Face recognition: {user_name} ({confidence:.3f})")
            elif reason == 'unknown_person_detected':
                confidence = context.get('confidence', 0.0)
                self.logger.warning(f"🚨 Unknown person alert (confidence: {confidence:.3f})")
            else:
                self.logger.info(f"👁️ Face recognition mode: {reason}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        runtime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        # Get enrolled users count
        enrolled_users = len(self.user_database.list_users()) if hasattr(self, 'user_database') else 0
        
        return {
            'is_running': self.is_running,
            'current_state': self.state_manager.current_state.value,
            'state_duration': self.state_manager.get_state_duration(),
            'runtime': runtime,
            'audio_available': self.audio_recorder.is_recording,
            'camera_available': self.camera_handler.is_camera_available(),
            'stats': self.stats.copy(),
            'audio_queue_size': self.audio_queue.qsize(),
            'face_recognition_queue_size': self.face_recognition_queue.qsize(),
            'enrolled_users': enrolled_users
        }
    
    def cleanup(self):
        """Cleanup all resources"""
        self.stop()
        self.audio_recorder.cleanup()
        self.camera_handler.cleanup()

# Test function for this module
def test_guard_agent():
    """Test the complete guard agent system"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    agent = GuardAgent()
    
    print("Testing Guard Agent...")
    print("Say 'Guard my room' to activate, then say 'stop' to deactivate")
    print("Press Ctrl+C to exit")
    
    try:
        if not agent.start():
            print("Failed to start agent")
            return False
        
        # Run for demo
        start_time = time.time()
        while time.time() - start_time < 60:  # Run for 1 minute
            status = agent.get_status()
            print(f"\rState: {status['current_state']} | "
                  f"Runtime: {status['runtime']:.1f}s | "
                  f"Commands: {status['stats']['commands_processed']} | "
                  f"Activations: {status['stats']['activations']}", end='')
            time.sleep(1)
        
        print("\nTest completed")
        return True
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return True
    except Exception as e:
        print(f"\nTest failed: {e}")
        return False
    finally:
        agent.cleanup()

if __name__ == "__main__":
    test_guard_agent()