"""
Text-to-Speech Manager Module
Handles text-to-speech conversion and audio playback with Gemini TTS support
"""

import os
import time
import tempfile
from typing import Optional
from pathlib import Path
import pygame
from gtts import gTTS

# Try to import Google Cloud TTS for Gemini TTS
try:
    import json
    import base64
    import requests
    GEMINI_TTS_AVAILABLE = True
except ImportError:
    GEMINI_TTS_AVAILABLE = False

# Try to import Gemini AI SDK for direct TTS (legacy)
try:
    import google.generativeai as genai
    GEMINI_AI_AVAILABLE = True
except ImportError:
    GEMINI_AI_AVAILABLE = False

class TTSManager:
    """Manages text-to-speech conversion and audio playback"""
    
    def __init__(self):
        """Initialize TTS manager"""
        self.temp_dir = tempfile.gettempdir()
        self.audio_files = []  # Track temporary files for cleanup
        self.last_conversion_time = 0.0
        self.is_initialized = False
        
        # TTS Settings
        self.language = 'en'
        self.tts_speed_slow = False  # False = normal speed, True = slow speed
        self.use_gemini_tts = True  # Prefer Gemini TTS when available
        
        # Gemini TTS setup using direct HTTP API
        self.gemini_api_key = None
        self.gemini_model = "gemini-2.5-flash-preview-tts"
        
        if GEMINI_TTS_AVAILABLE:
            # Check for API key
            self.gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
            
            if self.gemini_api_key:
                print("✅ Gemini TTS initialized with direct HTTP API")
                print(f"🎤 Using model: {self.gemini_model}")
            else:
                print("⚠️  GOOGLE_GEMINI_API_KEY not found, falling back to gTTS")
                self.use_gemini_tts = False
        else:
            print("⚠️  Required libraries not available for Gemini TTS")
            self.use_gemini_tts = False
        
        # Initialize pygame mixer for audio playback
        self._initialize_audio()
    
    def _initialize_audio(self) -> None:
        """Initialize pygame audio system"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.is_initialized = True
            print("✅ TTS Audio system initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize audio system: {e}")
            self.is_initialized = False
    
    def is_available(self) -> bool:
        """Check if TTS is available"""
        return self.is_initialized
    
    def _generate_audio_with_gemini_tts(self, text: str) -> Optional[str]:
        """Generate audio using Gemini TTS via direct HTTP API"""
        if not self.gemini_api_key:
            return None
        
        try:
            # Create temporary filename
            timestamp = int(time.time() * 1000)
            audio_filename = f"gemini_tts_audio_{timestamp}.mp3"
            audio_path = os.path.join(self.temp_dir, audio_filename)
            
            # API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            
            # Headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Create security-focused prompt for better TTS quality
            security_prompt = f"Speak as a professional security guard - authoritative, clear, and firm but polite. Say: {text}"
            
            # Request data with AUDIO response modality
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": security_prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["AUDIO"]
                }
            }
            
            # Make API request
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse response for audio content
                if 'candidates' in result:
                    for candidate in result['candidates']:
                        if 'content' in candidate and 'parts' in candidate['content']:
                            for part in candidate['content']['parts']:
                                if 'inlineData' in part:
                                    inline_data = part['inlineData']
                                    audio_b64 = inline_data.get('data', '')
                                    
                                    if audio_b64:
                                        # Decode base64 to PCM audio bytes
                                        audio_data = base64.b64decode(audio_b64)
                                        
                                        # Gemini TTS outputs PCM format - convert to WAV
                                        # Save PCM data temporarily
                                        pcm_path = audio_path.replace('.mp3', '.pcm')
                                        with open(pcm_path, 'wb') as f:
                                            f.write(audio_data)
                                        
                                        # Convert PCM to WAV using ffmpeg
                                        wav_path = audio_path.replace('.mp3', '.wav')
                                        try:
                                            import subprocess
                                            subprocess.run([
                                                'ffmpeg', '-f', 's16le', '-ar', '24000', '-ac', '1',
                                                '-i', pcm_path, '-y', wav_path
                                            ], check=True, capture_output=True)
                                            
                                            # Clean up PCM file
                                            os.unlink(pcm_path)
                                            
                                            self.audio_files.append(wav_path)
                                            print(f"✅ Gemini TTS audio generated and converted: {len(audio_data)} bytes PCM -> WAV")
                                            return wav_path
                                            
                                        except subprocess.CalledProcessError as e:
                                            print(f"❌ FFmpeg conversion failed: {e}")
                                            # Clean up and fallback
                                            if os.path.exists(pcm_path):
                                                os.unlink(pcm_path)
                                            if os.path.exists(wav_path):
                                                os.unlink(wav_path)
                                            raise Exception("Failed to convert PCM to WAV")
                
                print("❌ No audio content found in Gemini TTS response")
                return None
                
            else:
                print(f"❌ Gemini TTS API error ({response.status_code}): {response.text}")
                return None
            
        except Exception as e:
            print(f"❌ Gemini TTS generation failed: {e}")
            return None
    
    def text_to_speech(self, text: str, play_immediately: bool = True) -> Optional[str]:
        """
        Convert text to speech and optionally play it
        
        Args:
            text: Text to convert to speech
            play_immediately: Whether to play the audio immediately
            
        Returns:
            Path to the generated audio file, or None if failed
        """
        if not text.strip():
            print("⚠️  Empty text provided for TTS")
            return None
        
        try:
            start_time = time.time()
            audio_path = None
            
            # Try Gemini TTS first if available
            if self.use_gemini_tts and self.gemini_api_key:
                print(f"🎙️  Generating audio with Gemini TTS: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                audio_path = self._generate_audio_with_gemini_tts(text)
            
            # Fall back to gTTS if Gemini TTS failed or unavailable
            if not audio_path:
                print(f"🔊 Converting to speech with gTTS: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                
                # Create temporary filename
                timestamp = int(time.time() * 1000)
                audio_filename = f"tts_audio_{timestamp}.mp3"
                audio_path = os.path.join(self.temp_dir, audio_filename)
                
                # Generate speech using gTTS
                tts = gTTS(
                    text=text,
                    lang=self.language,
                    slow=self.tts_speed_slow
                )
                
                # Save to temporary file
                # Save to temporary file
                tts.save(audio_path)
                
                # Track the file for cleanup
                self.audio_files.append(audio_path)
            
            # Record conversion time
            self.last_conversion_time = time.time() - start_time
            
            print(f"✅ TTS conversion complete ({self.last_conversion_time:.2f}s)")
            
            # Play immediately if requested
            if play_immediately:
                self.play_audio(audio_path)
            
            return audio_path
            
        except Exception as e:
            print(f"❌ TTS conversion failed: {e}")
            return None
    
    def play_audio(self, audio_path: str) -> bool:
        """
        Play audio file using pygame
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if playback started successfully, False otherwise
        """
        if not self.is_available():
            print("❌ Audio system not available")
            return False
        
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return False
        
        try:
            print(f"🔊 Playing audio: {os.path.basename(audio_path)}")
            
            # Load and play the audio
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print("✅ Audio playback complete")
            return True
            
        except Exception as e:
            print(f"❌ Audio playback failed: {e}")
            return False
    
    def speak_text(self, text: str, wait_for_completion: bool = True) -> bool:
        """
        High-level method to convert text to speech and play it
        
        Args:
            text: Text to speak
            wait_for_completion: Whether to wait for playback to complete
            
        Returns:
            True if successful, False otherwise
        """
        audio_path = self.text_to_speech(text, play_immediately=False)
        
        if audio_path:
            if wait_for_completion:
                return self.play_audio(audio_path)
            else:
                # Start playback asynchronously
                try:
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.play()
                    return True
                except Exception as e:
                    print(f"❌ Async audio playback failed: {e}")
                    return False
        
        return False
    
    def stop_audio(self) -> None:
        """Stop current audio playback"""
        try:
            pygame.mixer.music.stop()
            print("🔇 Audio playback stopped")
        except Exception as e:
            print(f"❌ Failed to stop audio: {e}")
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        try:
            return pygame.mixer.music.get_busy()
        except:
            return False
    
    def set_language(self, language_code: str) -> None:
        """Set TTS language (e.g., 'en', 'es', 'fr')"""
        self.language = language_code
        print(f"🌐 TTS language set to: {language_code}")
    
    def set_speed(self, slow: bool) -> None:
        """Set TTS speed (True for slow, False for normal)"""
        self.tts_speed_slow = slow
        speed_text = "slow" if slow else "normal"
        print(f"⏩ TTS speed set to: {speed_text}")
    
    def get_last_conversion_time(self) -> float:
        """Get last TTS conversion time in seconds"""
        return self.last_conversion_time
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary audio files"""
        cleaned_count = 0
        for audio_file in self.audio_files:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                    cleaned_count += 1
            except Exception as e:
                print(f"⚠️  Failed to delete {audio_file}: {e}")
        
        self.audio_files.clear()
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} temporary audio files")
    
    def test_tts(self) -> bool:
        """Test TTS functionality"""
        test_text = "Hello, this is a test of the text to speech system."
        
        if not self.is_available():
            print("❌ TTS not available for testing")
            return False
        
        try:
            print("🧪 Testing TTS functionality...")
            success = self.speak_text(test_text)
            
            if success:
                print("✅ TTS test successful")
            else:
                print("❌ TTS test failed")
                
            return success
            
        except Exception as e:
            print(f"❌ TTS test error: {e}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_temp_files()


# Global TTS manager instance
tts_manager = TTSManager()