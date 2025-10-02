#!/usr/bin/env python3
"""
Simple audio test script to diagnose PyAudio issues.
Run this before the main demo to check if audio recording works.
"""

import sys
import os
import time

# # Add src and root directory to path
# root_dir = os.path.dirname(__file__)  # This file is in the project root
# src_dir = os.path.join(root_dir, 'src')
# sys.path.insert(0, src_dir)
# sys.path.insert(0, root_dir)

def test_pyaudio_basic():
    """Test basic PyAudio functionality"""
    print("Testing PyAudio basic functionality...")
    
    try:
        import pyaudio
        print("✓ PyAudio imported successfully")
        
        # Test PyAudio initialization
        p = pyaudio.PyAudio()
        print("✓ PyAudio initialized")
        
        # List audio devices
        device_count = p.get_device_count()
        print(f"✓ Found {device_count} audio devices")
        
        # Find input devices
        input_devices = []
        for i in range(device_count):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    input_devices.append((i, info['name']))
            except:
                pass
        
        if input_devices:
            print(f"✓ Found {len(input_devices)} input devices:")
            for idx, name in input_devices:
                print(f"    {idx}: {name}")
        else:
            print("❌ No input devices found")
            return False
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"❌ PyAudio test failed: {e}")
        return False

def test_simple_recording():
    """Test simple audio recording without callbacks"""
    print("\nTesting simple audio recording...")
    
    try:
        import pyaudio
        import wave
        
        # Audio parameters
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 3
        
        p = pyaudio.PyAudio()
        
        print("Recording for 3 seconds... speak now!")
        
        # Open stream
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        frames = []
        
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            print(f"Recording... {i+1}/{int(RATE / CHUNK * RECORD_SECONDS)}", end='\r')
        
        print("\nRecording finished!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save the recorded audio
        wf = wave.open("test_recording.wav", 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print("✓ Audio saved as 'test_recording.wav'")
        return True
        
    except Exception as e:
        print(f"❌ Recording test failed: {e}")
        return False

def test_speech_recognition():
    """Test speech recognition with the recorded audio"""
    print("\nTesting speech recognition...")
    
    try:
        import speech_recognition as sr
        
        r = sr.Recognizer()
        
        # Try to recognize the test recording
        try:
            with sr.AudioFile("test_recording.wav") as source:
                audio = r.record(source)
            
            print("Processing audio...")
            text = r.recognize_google(audio)
            print(f"✓ Recognized: '{text}'")
            return True
            
        except sr.UnknownValueError:
            print("❌ Could not understand the audio")
            return False
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Speech recognition test failed: {e}")
        return False

def main():
    """Run audio diagnostics"""
    print("=" * 50)
    print("AUDIO SYSTEM DIAGNOSTICS")
    print("=" * 50)
    
    results = []
    
    # Test PyAudio basic functionality
    results.append(test_pyaudio_basic())
    
    # Test simple recording
    if results[-1]:  # Only if PyAudio works
        results.append(test_simple_recording())
        
        # Test speech recognition
        if results[-1]:  # Only if recording works
            results.append(test_speech_recognition())
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC RESULTS")
    print("=" * 50)
    
    tests = ["PyAudio Basic", "Audio Recording", "Speech Recognition"]
    for i, (test, result) in enumerate(zip(tests[:len(results)], results)):
        status = "PASS" if result else "FAIL"
        print(f"{test:20}: {status}")
    
    if all(results):
        print("\n🎉 All audio tests passed! You can run the main demo.")
    else:
        print("\n❌ Some audio tests failed.")
        print("\nTroubleshooting tips:")
        if not results[0]:
            print("- Try reinstalling PyAudio: pip uninstall pyaudio && pip install pyaudio")
            print("- On Linux: sudo apt-get install portaudio19-dev python3-pyaudio")
            print("- On macOS: brew install portaudio")
        print("- Check microphone permissions in system settings")
        print("- Make sure no other applications are using the microphone")
    
    # Cleanup
    if os.path.exists("test_recording.wav"):
        try:
            os.remove("test_recording.wav")
            print("\nCleaned up test files.")
        except:
            pass

if __name__ == "__main__":
    main()