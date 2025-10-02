#!/usr/bin/env python3
"""
Simplified Milestone 1 test - just test audio recording without full integration.
"""

import sys
import os
import time

# # Add paths
# root_dir = os.path.dirname(__file__)  # This file is in the project root
# src_dir = os.path.join(root_dir, 'src')
# sys.path.insert(0, src_dir)
# sys.path.insert(0, root_dir)

def test_audio_only():
    """Test just the audio recording functionality"""
    print("Testing Audio Recording (Fixed Version)")
    print("=" * 50)
    
    try:
        from audio.audio_recorder import AudioRecorder
        from audio.speech_recognizer import SpeechRecognizer
        
        # Test audio recorder
        print("1. Initializing audio recorder...")
        recorder = AudioRecorder()
        
        if not recorder.initialize():
            print("❌ Failed to initialize audio recorder")
            return False
        
        print("✓ Audio recorder initialized")
        
        # Test speech recognizer
        print("2. Initializing speech recognizer...")
        recognizer = SpeechRecognizer()
        print("✓ Speech recognizer initialized")
        print(f"   Available commands: {recognizer.get_activation_commands()}")
        
        # Test recording
        print("3. Testing recording (5 seconds)...")
        print("   Say 'Guard my room' during recording...")
        
        if not recorder.start_recording():
            print("❌ Failed to start recording")
            return False
        
        print("   Recording started...")
        audio_chunks = []
        start_time = time.time()
        
        while time.time() - start_time < 5:
            chunk = recorder.get_audio_chunk(timeout=0.1)
            if chunk:
                audio_chunks.append(chunk)
            print(f"   Recording... {time.time() - start_time:.1f}s", end='\r')
        
        print()
        recorder.stop_recording()
        recorder.cleanup()
        
        if audio_chunks:
            print(f"✓ Recorded {len(audio_chunks)} audio chunks")
            
            # Test speech recognition
            print("4. Testing speech recognition...")
            combined_audio = b''.join(audio_chunks)
            
            try:
                is_command, text, confidence = recognizer.process_audio_chunk(combined_audio, 44100)
                print(f"   Recognized text: '{text}'")
                print(f"   Command detected: {is_command}")
                print(f"   Confidence: {confidence:.2f}")
                
                if is_command:
                    print("🎉 SUCCESS: Activation command detected!")
                    return True
                elif text:
                    print("✓ Speech recognized but no activation command")
                    print("   Try saying 'Guard my room' more clearly")
                    return True
                else:
                    print("ℹ️  No speech detected - this is normal if you didn't speak")
                    return True
                    
            except Exception as e:
                print(f"❌ Speech recognition failed: {e}")
                return False
        else:
            print("❌ No audio recorded")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_only():
    """Test just the camera functionality"""
    print("\nTesting Camera (Quick Test)")
    print("=" * 50)
    
    try:
        from video.camera_handler import CameraHandler
        
        camera = CameraHandler()
        
        if camera.initialize():
            print("✓ Camera initialized")
            
            # Quick frame test
            frame = camera.capture_single_frame()
            if frame is not None:
                print(f"✓ Frame captured: {frame.shape}")
                return True
            else:
                print("❌ Failed to capture frame")
                return False
        else:
            print("❌ Camera initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def main():
    """Run simplified tests"""
    print("AI GUARD AGENT - SIMPLIFIED MILESTONE 1 TEST")
    print("Testing core functionality after PyAudio fix")
    print()
    
    # Test audio
    audio_ok = test_audio_only()
    
    # Test video
    video_ok = test_video_only()
    
    print("\n" + "=" * 50)
    print("SIMPLIFIED TEST RESULTS")
    print("=" * 50)
    print(f"Audio System:  {'PASS' if audio_ok else 'FAIL'}")
    print(f"Video System:  {'PASS' if video_ok else 'FAIL'}")
    
    if audio_ok and video_ok:
        print("\n🎉 Core systems working! You can now:")
        print("   - Run the full demo: python milestone_demos/milestone_1_demo.py")
        print("   - Run the main system: python main.py")
    elif audio_ok:
        print("\n⚠️  Audio works but camera failed. Check camera permissions.")
    elif video_ok:
        print("\n⚠️  Camera works but audio failed. Check microphone permissions.")
    else:
        print("\n❌ Both systems failed. Check system permissions and hardware.")
    
    return 0 if audio_ok else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)