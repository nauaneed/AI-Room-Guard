"""
Audio playback utility for the AI Guard Agent.
Handles playing back recorded audio for testing purposes.
"""

import os
import wave
import tempfile
import logging
from typing import Optional
import io

# Try multiple audio playback libraries for best compatibility
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

class AudioPlayer:
    """Handles audio playback using multiple backends"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backend = self._choose_backend()
        self.logger.info(f"Audio player using backend: {self.backend}")
    
    def _choose_backend(self) -> str:
        """Choose the best available audio playback backend"""
        if PYGAME_AVAILABLE:
            return "pygame"
        elif PYAUDIO_AVAILABLE:
            return "pyaudio"
        elif PLAYSOUND_AVAILABLE:
            return "playsound"
        else:
            return "none"
    
    def play_audio_data(self, audio_data: bytes, sample_rate: int = 44100, channels: int = 1, sample_width: int = 2) -> bool:
        """
        Play raw audio data
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Sample rate (default 44100)
            channels: Number of channels (default 1 for mono)
            sample_width: Sample width in bytes (default 2 for 16-bit)
        
        Returns:
            True if playback successful, False otherwise
        """
        if self.backend == "none":
            self.logger.error("No audio playback backend available")
            return False
        
        # Create temporary WAV file
        temp_path = None
        try:
            temp_path = self._create_temp_wav(audio_data, sample_rate, channels, sample_width)
            if not temp_path:
                return False
            
            return self._play_file(temp_path)
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
            return False
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp audio file: {e}")
    
    def _create_temp_wav(self, audio_data: bytes, sample_rate: int, channels: int, sample_width: int) -> Optional[str]:
        """Create a temporary WAV file from raw audio data"""
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
            
            with os.fdopen(temp_fd, 'wb') as temp_file:
                with wave.open(temp_file, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(sample_width)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to create temp WAV file: {e}")
            return None
    
    def _play_file(self, file_path: str) -> bool:
        """Play audio file using the selected backend"""
        try:
            if self.backend == "pygame":
                return self._play_with_pygame(file_path)
            elif self.backend == "pyaudio":
                return self._play_with_pyaudio(file_path)
            elif self.backend == "playsound":
                return self._play_with_playsound(file_path)
            else:
                self.logger.error(f"Unknown backend: {self.backend}")
                return False
        except Exception as e:
            self.logger.error(f"Playback failed with {self.backend}: {e}")
            return False
    
    def _play_with_pygame(self, file_path: str) -> bool:
        """Play audio using pygame"""
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            pygame.mixer.quit()
            return True
            
        except Exception as e:
            self.logger.error(f"Pygame playback error: {e}")
            return False
    
    def _play_with_pyaudio(self, file_path: str) -> bool:
        """Play audio using PyAudio"""
        try:
            # Read WAV file
            with wave.open(file_path, 'rb') as wf:
                # Create PyAudio instance
                p = pyaudio.PyAudio()
                
                # Open stream
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                # Play audio
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                # Cleanup
                stream.stop_stream()
                stream.close()
                p.terminate()
                
            return True
            
        except Exception as e:
            self.logger.error(f"PyAudio playback error: {e}")
            return False
    
    def _play_with_playsound(self, file_path: str) -> bool:
        """Play audio using playsound"""
        try:
            playsound.playsound(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Playsound playback error: {e}")
            return False
    
    def get_available_backends(self) -> list:
        """Get list of available audio playback backends"""
        backends = []
        if PYGAME_AVAILABLE:
            backends.append("pygame")
        if PYAUDIO_AVAILABLE:
            backends.append("pyaudio")
        if PLAYSOUND_AVAILABLE:
            backends.append("playsound")
        return backends

# Test function
def test_audio_playback():
    """Test audio playback functionality"""
    import time
    
    print("Testing audio playback...")
    
    player = AudioPlayer()
    print(f"Available backends: {player.get_available_backends()}")
    print(f"Using backend: {player.backend}")
    
    # Create a simple test tone (sine wave)
    import numpy as np
    
    duration = 2  # seconds
    sample_rate = 44100
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(frequency * 2 * np.pi * t)
    
    # Convert to 16-bit integers
    wave_data = (wave_data * 32767).astype(np.int16)
    
    # Convert to bytes
    audio_bytes = wave_data.tobytes()
    
    print(f"Playing {duration}s test tone at {frequency}Hz...")
    success = player.play_audio_data(audio_bytes, sample_rate)
    
    if success:
        print("✓ Audio playback test successful")
    else:
        print("✗ Audio playback test failed")
    
    return success

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_audio_playback()