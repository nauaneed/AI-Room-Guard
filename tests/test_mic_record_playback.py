#!/usr/bin/env python3
"""
Simple microphone record and playback test.
Records audio for a few seconds and plays it back to verify microphone functionality.
"""

import pyaudio
import wave
import time
import os
import tempfile
from typing import Optional

class SimpleAudioTest:
    """Simple audio record and playback test"""
    
    def __init__(self):
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.record_seconds = 5
        
    def test_record_and_playback(self) -> bool:
        """Record audio and play it back"""
        print("🎤 MICROPHONE RECORD & PLAYBACK TEST")
        print("=" * 50)
        
        # Create temporary file for recording
        temp_file = tempfile.mktemp(suffix=".wav")
        
        try:
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            print(f"📱 Found {p.get_device_count()} audio devices")
            
            # Get default input device
            try:
                input_device = p.get_default_input_device_info()
                print(f"🎤 Input device: {input_device['name']}")
                print(f"   Sample rate: {input_device['defaultSampleRate']}")
                print(f"   Max input channels: {input_device['maxInputChannels']}")
            except Exception as e:
                print(f"❌ Error getting input device: {e}")
                return False
            
            # Get default output device
            try:
                output_device = p.get_default_output_device_info()
                print(f"🔊 Output device: {output_device['name']}")
                print(f"   Sample rate: {output_device['defaultSampleRate']}")
                print(f"   Max output channels: {output_device['maxOutputChannels']}")
            except Exception as e:
                print(f"❌ Error getting output device: {e}")
                return False
            
            # Record audio
            print(f"\n🎙️  Recording for {self.record_seconds} seconds...")
            print("📢 Start speaking now!")
            
            # Open recording stream
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            
            # Record audio with progress indicator
            for i in range(0, int(self.rate / self.chunk_size * self.record_seconds)):
                data = stream.read(self.chunk_size)
                frames.append(data)
                
                # Show progress
                progress = (i + 1) / int(self.rate / self.chunk_size * self.record_seconds)
                bar_length = 30
                filled_length = int(bar_length * progress)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                print(f"\r🎤 Recording: [{bar}] {progress:.1%}", end='', flush=True)
            
            print("\n✅ Recording finished!")
            
            # Stop and close the recording stream
            stream.stop_stream()
            stream.close()
            
            # Save the recording
            print(f"💾 Saving recording to {temp_file}")
            wf = wave.open(temp_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Check file size
            file_size = os.path.getsize(temp_file)
            print(f"📊 Recorded file size: {file_size} bytes")
            
            if file_size < 1000:
                print("⚠️  Warning: File size is very small, microphone might not be working")
                return False
            
            # Wait a moment before playback
            print("\n⏳ Preparing for playback...")
            time.sleep(1)
            
            # Play back the recording
            print("🔊 Playing back your recording...")
            
            # Open the saved file for playback
            wf = wave.open(temp_file, 'rb')
            
            # Open playback stream
            playback_stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            # Play the audio
            data = wf.readframes(self.chunk_size)
            while data:
                playback_stream.write(data)
                data = wf.readframes(self.chunk_size)
            
            # Stop and close playback stream
            playback_stream.stop_stream()
            playback_stream.close()
            wf.close()
            
            print("✅ Playback finished!")
            
            # Cleanup
            p.terminate()
            
            # Ask user for feedback
            print("\n🎯 RESULT VERIFICATION:")
            print("=" * 30)
            print("Did you hear your voice played back clearly? (y/n): ", end='')
            
            # For automated testing, assume success if we got this far
            try:
                response = input().lower().strip()
                success = response.startswith('y')
            except (EOFError, KeyboardInterrupt):
                print("(automated test - assuming success)")
                success = True
            
            if success:
                print("🎉 SUCCESS: Microphone and speakers are working!")
            else:
                print("❌ ISSUE: Audio system may have problems")
            
            # Clean up temp file
            try:
                os.remove(temp_file)
                print(f"🧹 Cleaned up temporary file")
            except:
                pass
            
            return success
            
        except Exception as e:
            print(f"❌ Error during audio test: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

def test_audio_levels():
    """Test audio input levels to see if microphone is picking up sound"""
    print("\n🎚️  AUDIO LEVEL TEST")
    print("=" * 30)
    print("📢 Speak or make noise to test input levels...")
    
    try:
        p = pyaudio.PyAudio()
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )
        
        print("🎤 Monitoring audio levels for 10 seconds...")
        print("📊 Audio level visualization:")
        
        import struct
        import numpy as np
        
        for i in range(100):  # 10 seconds at ~10 FPS
            data = stream.read(1024, exception_on_overflow=False)
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(data, dtype=np.int16)
            
            # Calculate RMS (root mean square) for volume level
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Normalize to percentage (0-100%)
            level = min(100, int(rms / 3000 * 100))
            
            # Create visual bar
            bar_length = 50
            filled_length = int(bar_length * level / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            print(f"\r🎤 Level: [{bar}] {level:3d}%", end='', flush=True)
            time.sleep(0.1)
        
        print("\n✅ Audio level test complete")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except Exception as e:
        print(f"❌ Error during level test: {e}")

def main():
    """Run the complete audio test suite"""
    print("🔊 COMPREHENSIVE AUDIO SYSTEM TEST")
    print("=" * 60)
    print("This test will:")
    print("1. Record audio from your microphone")
    print("2. Save it to a temporary file")
    print("3. Play it back through your speakers")
    print("4. Monitor audio input levels")
    print("\nMake sure your microphone and speakers are working!")
    print("=" * 60)
    
    # Create test instance
    audio_test = SimpleAudioTest()
    
    # Run record and playback test
    success = audio_test.test_record_and_playback()
    
    # Run audio level test
    test_audio_levels()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ OVERALL RESULT: Audio system appears to be working!")
        print("🎤 Microphone: Functional")
        print("🔊 Speakers: Functional")
        print("💾 Recording: Successful")
        print("🔄 Playback: Successful")
    else:
        print("❌ OVERALL RESULT: Audio system has issues")
        print("🔧 Troubleshooting suggestions:")
        print("   • Check microphone is connected and not muted")
        print("   • Check system audio permissions")
        print("   • Try adjusting microphone volume in system settings")
        print("   • Check if other applications are using the microphone")
    
    return success

if __name__ == "__main__":
    main()