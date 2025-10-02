#!/usr/bin/env python3
"""
Robust microphone test with error handling and buffer management.
"""

import pyaudio
import wave
import time
import os
import tempfile
import numpy as np

def test_microphone_robust():
    """Test microphone with robust error handling"""
    print("🎤 ROBUST MICROPHONE TEST")
    print("=" * 40)
    
    p = pyaudio.PyAudio()
    
    try:
        # List all input devices
        print("📋 Available input devices:")
        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append((i, info))
                print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
        
        if not input_devices:
            print("❌ No input devices found!")
            return False
        
        # Use the first available input device
        device_index, device_info = input_devices[0]
        print(f"\n🎤 Using device: {device_info['name']}")
        
        # Test different configurations
        configs = [
            {"rate": 44100, "chunk": 1024, "channels": 1},
            {"rate": 44100, "chunk": 2048, "channels": 1},
            {"rate": 22050, "chunk": 1024, "channels": 1},
            {"rate": 16000, "chunk": 1024, "channels": 1},
        ]
        
        for config in configs:
            print(f"\n🧪 Testing config: {config['rate']}Hz, chunk={config['chunk']}, channels={config['channels']}")
            
            try:
                # Test opening stream
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=config['channels'],
                    rate=config['rate'],
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=config['chunk']
                )
                
                print("✅ Stream opened successfully")
                
                # Test reading a few chunks
                max_level = 0
                for i in range(10):  # Test for 1 second
                    try:
                        data = stream.read(config['chunk'], exception_on_overflow=False)
                        
                        # Calculate audio level
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        rms = np.sqrt(np.mean(audio_array**2))
                        level = int(rms / 3000 * 100)
                        max_level = max(max_level, level)
                        
                        # Show live level
                        bar = '█' * (level // 5) + '░' * (20 - level // 5)
                        print(f"\r   Audio level: [{bar}] {level:3d}%", end='', flush=True)
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"\n❌ Read error: {e}")
                        break
                
                stream.stop_stream()
                stream.close()
                
                print(f"\n   Max level detected: {max_level}%")
                
                if max_level > 0:
                    print("✅ Microphone is working with this configuration!")
                    return True
                else:
                    print("⚠️  No audio detected")
                
            except Exception as e:
                print(f"❌ Failed to open stream: {e}")
                continue
        
        print("\n❌ No working configuration found")
        return False
        
    finally:
        p.terminate()

def test_system_microphone():
    """Test system microphone permissions and availability"""
    print("\n🔧 SYSTEM MICROPHONE CHECK")
    print("=" * 40)
    
    # Check if microphone device files exist
    mic_devices = [
        "/dev/dsp",
        "/dev/audio",
        "/proc/asound/cards"
    ]
    
    for device in mic_devices:
        if os.path.exists(device):
            print(f"✅ {device} exists")
        else:
            print(f"❌ {device} not found")
    
    # Check ALSA info
    try:
        import subprocess
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("\n📋 ALSA recording devices:")
            print(result.stdout)
        else:
            print("❌ Could not get ALSA device list")
    except Exception as e:
        print(f"❌ ALSA check failed: {e}")

def test_simple_record():
    """Very simple recording test"""
    print("\n🎙️  SIMPLE RECORD TEST")
    print("=" * 30)
    print("Recording 3 seconds of audio...")
    
    try:
        p = pyaudio.PyAudio()
        
        # Use very safe parameters
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,  # Lower sample rate
            input=True,
            frames_per_buffer=4096,  # Larger buffer
            input_device_index=None  # Use default
        )
        
        frames = []
        for i in range(0, int(16000 / 4096 * 3)):  # 3 seconds
            try:
                data = stream.read(4096, exception_on_overflow=False)
                frames.append(data)
                print(f"\rFrame {i+1}...", end='', flush=True)
            except Exception as e:
                print(f"\nRead error: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        if frames:
            # Calculate some basic stats
            all_data = b''.join(frames)
            audio_array = np.frombuffer(all_data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array**2))
            
            print(f"\n✅ Recorded {len(frames)} frames")
            print(f"📊 Audio RMS level: {rms:.2f}")
            print(f"📊 Data size: {len(all_data)} bytes")
            
            if rms > 10:  # Some threshold for detecting actual audio
                print("✅ Audio detected!")
                return True
            else:
                print("⚠️  Very low audio levels")
                return False
        else:
            print("\n❌ No data recorded")
            return False
            
    except Exception as e:
        print(f"\n❌ Recording failed: {e}")
        return False

def main():
    """Run comprehensive microphone tests"""
    print("🎤 COMPREHENSIVE MICROPHONE DIAGNOSTICS")
    print("=" * 60)
    
    # Run system checks
    test_system_microphone()
    
    # Run simple record test
    simple_success = test_simple_record()
    
    # Run robust test
    robust_success = test_microphone_robust()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if simple_success or robust_success:
        print("✅ MICROPHONE IS WORKING!")
        print("🎤 Audio input detected successfully")
    else:
        print("❌ MICROPHONE ISSUES DETECTED")
        print("🔧 Possible solutions:")
        print("   1. Check if microphone is muted in system settings")
        print("   2. Check microphone permissions for this application")
        print("   3. Try: pulseaudio --kill && pulseaudio --start")
        print("   4. Check: alsamixer (ensure microphone is not muted)")
        print("   5. Test with: arecord -d 3 test.wav")
    
    return simple_success or robust_success

if __name__ == "__main__":
    main()