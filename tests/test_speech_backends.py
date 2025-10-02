#!/usr/bin/env python3
"""
Speech recognition backend comparison demo.
Tests both Whisper and Google Speech Recognition backends.
"""

import sys
import os
import time

# # Add src directory to path
# root_dir = os.path.dirname(__file__)
# src_dir = os.path.join(root_dir, 'src')
# sys.path.insert(0, src_dir)

from src.audio.speech_recognizer import SpeechRecognizer
from src.audio.audio_recorder import AudioRecorder
from src.utils.logger import setup_logging

def test_backend_comparison():
    """Test and compare both speech recognition backends"""
    
    setup_logging()
    
    print("🎤 SPEECH RECOGNITION BACKEND COMPARISON")
    print("=" * 60)
    
    # Initialize audio recorder
    recorder = AudioRecorder()
    if not recorder.initialize():
        print("❌ Failed to initialize audio recorder")
        return
    
    # Test Whisper backend
    print("\n🤖 Testing WHISPER backend...")
    whisper_recognizer = SpeechRecognizer(backend="whisper")
    print(f"Backend: {whisper_recognizer.get_backend()}")
    
    print("Recording 5 seconds with Whisper...")
    print("Say 'Guard my room' clearly...")
    
    recorder.start_recording()
    audio_chunks = []
    start_time = time.time()
    
    while time.time() - start_time < 5:
        chunk = recorder.get_audio_chunk(timeout=0.1)
        if chunk:
            audio_chunks.append(chunk)
    
    recorder.stop_recording()
    
    if audio_chunks:
        combined_audio = b''.join(audio_chunks)
        is_command, text, confidence = whisper_recognizer.process_audio_chunk(combined_audio, 44100)
        
        print(f"✓ Whisper Results:")
        print(f"  Recognized: '{text}'")
        print(f"  Command detected: {is_command}")
        print(f"  Confidence: {confidence:.2f}")
    else:
        print("❌ No audio recorded for Whisper")
    
    print("\n" + "="*40)
    
    # Test Google backend
    print("\n🌐 Testing GOOGLE backend...")
    google_recognizer = SpeechRecognizer(backend="google")
    print(f"Backend: {google_recognizer.get_backend()}")
    
    print("Recording 5 seconds with Google...")
    print("Say 'Guard my room' clearly...")
    
    time.sleep(2)  # Brief pause between tests
    
    recorder.start_recording()
    audio_chunks = []
    start_time = time.time()
    
    while time.time() - start_time < 5:
        chunk = recorder.get_audio_chunk(timeout=0.1)
        if chunk:
            audio_chunks.append(chunk)
    
    recorder.stop_recording()
    
    if audio_chunks:
        combined_audio = b''.join(audio_chunks)
        is_command, text, confidence = google_recognizer.process_audio_chunk(combined_audio, 44100)
        
        print(f"✓ Google Results:")
        print(f"  Recognized: '{text}'")
        print(f"  Command detected: {is_command}")
        print(f"  Confidence: {confidence:.2f}")
    else:
        print("❌ No audio recorded for Google")
    
    print("\n" + "="*60)
    print("📊 COMPARISON SUMMARY:")
    print("• Whisper: Works offline, generally more accurate")
    print("• Google: Requires internet, fast processing")
    print("• Default backend in config: 'whisper'")
    print("=" * 60)

if __name__ == "__main__":
    test_backend_comparison()