"""
Audio recording module for the AI Guard Agent.
Handles microphone input and audio data capture.
"""

import pyaudio
import threading
import queue
import time
import logging
from typing import Optional, Callable, Dict, Any, List
import numpy as np
import audioop
from src.utils.smart_logger import SmartLogger

import pyaudio
import wave
import threading
import queue
import logging
from typing import Optional, Generator
from config.settings import AudioConfig

class AudioRecorder:
    """Handles audio recording from microphone"""
    
    def __init__(self):
        self.logger = SmartLogger(__name__)
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.pyaudio_instance = None
        self.stream = None
        self.recording_thread = None
        
        # Audio configuration
        self.chunk_size = AudioConfig.CHUNK_SIZE
        self.format = pyaudio.paInt16  # 16-bit audio
        self.channels = AudioConfig.CHANNELS
        self.rate = AudioConfig.RATE
        
    def initialize(self) -> bool:
        """Initialize PyAudio and check microphone availability"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Check if microphone is available
            device_count = self.pyaudio_instance.get_device_count()
            self.logger.info(f"Found {device_count} audio devices")
            
            # Find default input device
            default_input = self.pyaudio_instance.get_default_input_device_info()
            self.logger.info(f"Using microphone: {default_input['name']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {e}")
            return False
    
    def start_recording(self) -> bool:
        """Start continuous audio recording"""
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return False
            
        try:
            # Open audio stream without callback to avoid PY_SSIZE_T_CLEAN issue
            self.stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_recording = True
            
            # Start recording thread instead of using callback
            self.recording_thread = threading.Thread(target=self._recording_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            self.logger.info("Audio recording started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop audio recording and cleanup"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        self.logger.info("Audio recording stopped")
    
    def _recording_loop(self):
        """Recording loop that runs in a separate thread"""
        while self.is_recording and self.stream:
            try:
                # Read audio data from stream
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                if self.is_recording:  # Check again in case we stopped while reading
                    self.audio_queue.put(data)
            except Exception as e:
                if self.is_recording:  # Only log if we're still supposed to be recording
                    self.logger.error(f"Error in recording loop: {e}")
                break
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        """Get next audio chunk from the queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def has_audio_data(self) -> bool:
        """Check if audio data is available"""
        return not self.audio_queue.empty()
    
    def save_audio_chunk(self, audio_data: bytes, filename: str):
        """Save audio chunk to file for testing/debugging"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)
            
            self.logger.info(f"Audio saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save audio: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_recording()
        
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
            self.pyaudio_instance = None
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Test function for this module
def test_audio_recording():
    """Test audio recording functionality"""
    import time
    
    recorder = AudioRecorder()
    
    if not recorder.initialize():
        print("Failed to initialize audio recorder")
        return False
    
    print("Starting 5-second audio test...")
    recorder.start_recording()
    
    # Record for 5 seconds
    audio_chunks = []
    start_time = time.time()
    
    while time.time() - start_time < 5:
        chunk = recorder.get_audio_chunk(timeout=0.1)
        if chunk:
            audio_chunks.append(chunk)
    
    recorder.stop_recording()
    
    # Save test recording
    if audio_chunks:
        combined_audio = b''.join(audio_chunks)
        recorder.save_audio_chunk(combined_audio, "test_recording.wav")
        print(f"Recorded {len(audio_chunks)} audio chunks")
        return True
    else:
        print("No audio data recorded")
        return False

if __name__ == "__main__":
    # Run test when module is executed directly
    logging.basicConfig(level=logging.INFO)
    test_audio_recording()