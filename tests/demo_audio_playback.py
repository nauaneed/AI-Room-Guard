#!/usr/bin/env python3
"""
Audio playback demo - Record audio and play it back immediately.
Demonstrates the audio recording -> playback pipeline.
"""

import sys
import os
import time

# # Add src directory to path
# root_dir = os.path.dirname(__file__)
# src_dir = os.path.join(root_dir, 'src')
# sys.path.insert(0, src_dir)

from src.audio.audio_recorder import AudioRecorder
from src.audio.audio_player import AudioPlayer
from src.utils.logger import setup_logging

def test_record_and_playback():
    """Record audio and immediately play it back"""
    print("🎤🔊 AUDIO RECORD & PLAYBACK DEMO")
    print("=" * 50)
    
    # Setup basic logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Initialize components
    recorder = AudioRecorder()
    player = AudioPlayer()
    
    print(f"Audio player backends: {player.get_available_backends()}")
    print(f"Using playback backend: {player.backend}")
    print()
    
    if not recorder.initialize():
        print("❌ Failed to initialize audio recorder")
        return False
    
    try:
        # Record audio
        duration = 3  # seconds
        print(f"🎤 Recording {duration} seconds of audio...")
        print("Say something now!")
        
        recorder.start_recording()
        audio_chunks = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            chunk = recorder.get_audio_chunk(timeout=0.1)
            if chunk:
                audio_chunks.append(chunk)
            
            # Show progress
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            if remaining > 0:
                print(f"Recording... {remaining:.1f}s remaining", end='\r')
        
        recorder.stop_recording()
        print(f"\n✅ Recording complete! Captured {len(audio_chunks)} audio chunks")
        
        if not audio_chunks:
            print("❌ No audio data recorded")
            return False
        
        # Combine audio data
        combined_audio = b''.join(audio_chunks)
        print(f"📊 Total audio data: {len(combined_audio)} bytes")
        
        # Play back the audio
        print("\n🔊 Playing back your recording...")
        playback_success = player.play_audio_data(
            combined_audio, 
            sample_rate=44100, 
            channels=1, 
            sample_width=2
        )
        
        if playback_success:
            print("✅ Playback successful!")
            print("\n🎉 Audio recording and playback pipeline is working!")
            return True
        else:
            print("❌ Playback failed")
            return False
    
    except KeyboardInterrupt:
        print("\n⚠️ Recording interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error during recording/playback: {e}")
        return False
    finally:
        recorder.cleanup()

def main():
    """Main demo function"""
    print("This demo will record audio from your microphone and play it back.")
    print("Make sure your microphone and speakers are working.")
    
    input("Press Enter to start the demo...")
    
    success = test_record_and_playback()
    
    if success:
        print("\n✅ Demo completed successfully!")
        print("The audio recording and playback system is fully functional.")
    else:
        print("\n❌ Demo failed. Check your audio hardware and try again.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)