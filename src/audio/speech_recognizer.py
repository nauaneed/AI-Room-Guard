"""
Speech recognition module for the AI Guard Agent.
Handles voice command detection and speech-to-text conversion.
"""

import speech_recognition as sr
import logging
import time
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher

from config.settings import AudioConfig
from src.utils.smart_logger import SmartLogger

import speech_recognition as sr
import logging
import difflib
import tempfile
import os
from typing import Optional, List, Tuple
from config.settings import AudioConfig
import io
import wave

# Try to import whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available, falling back to Google Speech Recognition")

class SpeechRecognizer:
    """Handles speech-to-text conversion and command detection"""
    
    def __init__(self, backend: str = None):
        self.logger = SmartLogger(__name__)
        
        # Determine backend
        if backend is None:
            backend = AudioConfig.SPEECH_BACKEND
        
        self.backend = backend.lower()
        
        # Initialize Google Speech Recognition (always available as fallback)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = AudioConfig.PHRASE_TIMEOUT
        
        # Initialize Whisper if requested and available
        self.whisper_model = None
        if self.backend == "whisper":
            if WHISPER_AVAILABLE:
                try:
                    self.whisper_model = whisper.load_model(AudioConfig.WHISPER_MODEL)
                    self.logger.info(f"Whisper model '{AudioConfig.WHISPER_MODEL}' loaded successfully")
                except Exception as e:
                    self.logger.error(f"Failed to load Whisper model: {e}")
                    self.logger.info("Falling back to Google Speech Recognition")
                    self.backend = "google"
            else:
                self.logger.warning("Whisper not available, using Google Speech Recognition")
                self.backend = "google"
        
        # Load activation commands
        self.activation_commands = [cmd.lower() for cmd in AudioConfig.ACTIVATION_COMMANDS]
        self.similarity_threshold = AudioConfig.COMMAND_SIMILARITY_THRESHOLD
        
        self.logger.info(f"Speech recognizer initialized with {len(self.activation_commands)} activation commands")
        self.logger.info(f"Using backend: {self.backend}")
    
    def audio_data_to_recognizer_format(self, audio_data: bytes, sample_rate: int = 44100) -> sr.AudioData:
        """Convert raw audio bytes to speech_recognition AudioData format"""
        try:
            # Create a wave file in memory
            audio_buffer = io.BytesIO()
            with wave.open(audio_buffer, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            
            # Reset buffer position
            audio_buffer.seek(0)
            
            # Convert to AudioData
            with sr.AudioFile(audio_buffer) as source:
                audio = self.recognizer.record(source)
            
            return audio
            
        except Exception as e:
            self.logger.error(f"Failed to convert audio data: {e}")
            return None
    
    def save_audio_to_temp_file(self, audio_data: bytes, sample_rate: int = 44100) -> str:
        """Save audio data to a temporary WAV file for Whisper"""
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
            
            with os.fdopen(temp_fd, 'wb') as temp_file:
                with wave.open(temp_file, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to save audio to temp file: {e}")
            return None
    
    def recognize_speech_whisper(self, audio_data: bytes, sample_rate: int = 44100) -> Optional[str]:
        """Convert audio data to text using Whisper"""
        if self.whisper_model is None:
            self.logger.error("Whisper model not loaded")
            return None
        
        temp_path = None
        try:
            # Save audio to temporary file
            temp_path = self.save_audio_to_temp_file(audio_data, sample_rate)
            if temp_path is None:
                return None
            
            # Transcribe with Whisper (English only for better accuracy)
            result = self.whisper_model.transcribe(
                temp_path, 
                language="en",  # Force English language
                task="transcribe"  # Transcription task (vs translate)
            )
            text = result["text"].strip()
            
            if text:
                self.logger.info(f"Whisper recognized speech: '{text}'")
                return text.lower().strip()
            else:
                self.logger.debug("Whisper: No speech detected")
                return None
                
        except Exception as e:
            self.logger.error(f"Whisper recognition error: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
    
    def recognize_speech_google(self, audio_data: bytes, sample_rate: int = 44100) -> Optional[str]:
        """Convert audio data to text using Google Speech Recognition"""
        try:
            # Convert to AudioData format
            audio = self.audio_data_to_recognizer_format(audio_data, sample_rate)
            if audio is None:
                return None
            
            # Recognize speech using Google's service
            text = self.recognizer.recognize_google(
                audio, 
                show_all=False
            )
            
            self.logger.audio_command_event(text, 1.0)
            return text.lower().strip()
            
        except sr.UnknownValueError:
            self.logger.debug("Google: Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Google Speech recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Google Speech recognition error: {e}")
            return None

    def recognize_speech(self, audio_data: bytes, sample_rate: int = 44100) -> Optional[str]:
        """Convert audio data to text using the configured backend"""
        if self.backend == "whisper":
            return self.recognize_speech_whisper(audio_data, sample_rate)
        else:
            return self.recognize_speech_google(audio_data, sample_rate)
    
    def is_activation_command(self, text: str) -> Tuple[bool, str, float]:
        """
        Check if the recognized text contains an activation command.
        
        Returns:
            Tuple of (is_command, matched_command, confidence)
        """
        if not text:
            return False, "", 0.0
        
        text = text.lower().strip()
        
        # First, try exact matching
        for command in self.activation_commands:
            if command in text:
                self.logger.audio_command_event(command, 1.0)
                return True, command, 1.0
        
        # If no exact match, try fuzzy matching
        best_match = ""
        best_similarity = 0.0
        
        for command in self.activation_commands:
            # Use sequence matcher for similarity
            similarity = difflib.SequenceMatcher(None, text, command).ratio()
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = command
        
        # Check if best match meets threshold
        if best_similarity >= self.similarity_threshold:
            self.logger.audio_command_event(best_match, best_similarity)
            return True, best_match, best_similarity
        
        self.logger.debug(f"No activation command found in: '{text}' (best similarity: {best_similarity:.2f})")
        return False, "", best_similarity
    
    def process_audio_chunk(self, audio_data: bytes, sample_rate: int = 44100) -> Tuple[bool, Optional[str], float]:
        """
        Process a single audio chunk and check for activation commands.
        
        Returns:
            Tuple of (command_detected, recognized_text, confidence)
        """
        # Recognize speech
        text = self.recognize_speech(audio_data, sample_rate)
        
        if text is None:
            return False, None, 0.0
        
        # Check for activation command
        is_command, matched_command, confidence = self.is_activation_command(text)
        
        return is_command, text, confidence
    
    def add_activation_command(self, command: str):
        """Add a new activation command"""
        command = command.lower().strip()
        if command not in self.activation_commands:
            self.activation_commands.append(command)
            self.logger.info(f"Added new activation command: '{command}'")
    
    def remove_activation_command(self, command: str):
        """Remove an activation command"""
        command = command.lower().strip()
        if command in self.activation_commands:
            self.activation_commands.remove(command)
            self.logger.info(f"Removed activation command: '{command}'")
    
    def get_activation_commands(self) -> List[str]:
        """Get list of current activation commands"""
        return self.activation_commands.copy()
    
    def switch_backend(self, backend: str) -> bool:
        """Switch speech recognition backend"""
        backend = backend.lower()
        
        if backend == "whisper":
            if not WHISPER_AVAILABLE:
                self.logger.error("Whisper not available")
                return False
            
            if self.whisper_model is None:
                try:
                    self.whisper_model = whisper.load_model(AudioConfig.WHISPER_MODEL)
                    self.logger.info(f"Whisper model '{AudioConfig.WHISPER_MODEL}' loaded successfully")
                except Exception as e:
                    self.logger.error(f"Failed to load Whisper model: {e}")
                    return False
            
            self.backend = "whisper"
            self.logger.info("Switched to Whisper backend")
            return True
            
        elif backend == "google":
            self.backend = "google"
            self.logger.info("Switched to Google Speech Recognition backend")
            return True
            
        else:
            self.logger.error(f"Unknown backend: {backend}")
            return False
    
    def get_backend(self) -> str:
        """Get current speech recognition backend"""
        return self.backend

# Test function for this module
def test_speech_recognition():
    """Test speech recognition with sample audio or user input"""
    import time
    from audio.audio_recorder import AudioRecorder
    
    recognizer = SpeechRecognizer()
    recorder = AudioRecorder()
    
    print("Testing speech recognition...")
    print(f"Backend: {recognizer.get_backend()}")
    print("Activation commands:", recognizer.get_activation_commands())
    
    if not recorder.initialize():
        print("Failed to initialize audio recorder")
        return False
    
    print("Say one of the activation commands. Recording for 5 seconds...")
    recorder.start_recording()
    
    # Collect audio for 5 seconds
    audio_chunks = []
    start_time = time.time()
    
    while time.time() - start_time < 5:
        chunk = recorder.get_audio_chunk(timeout=0.1)
        if chunk:
            audio_chunks.append(chunk)
    
    recorder.stop_recording()
    
    if not audio_chunks:
        print("No audio recorded")
        return False
    
    # Combine all chunks
    combined_audio = b''.join(audio_chunks)
    
    # Test speech recognition
    print("Processing audio...")
    is_command, text, confidence = recognizer.process_audio_chunk(combined_audio, 44100)
    
    print(f"Recognized text: '{text}'")
    print(f"Command detected: {is_command}")
    print(f"Confidence: {confidence:.2f}")
    
    return is_command

if __name__ == "__main__":
    # Run test when module is executed directly
    logging.basicConfig(level=logging.INFO)
    test_speech_recognition()