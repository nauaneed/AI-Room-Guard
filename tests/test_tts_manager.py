#!/usr/bin/env python3
"""
Test the updated TTS Manager with Gemini TTS integration
"""

import sys
import os

# Add project root to path
sys.path.append('/home/navaneet/pypro/EE782/A2')

from src.audio.tts_manager import TTSManager

def test_tts_manager():
    """Test the TTS Manager with both Gemini and gTTS"""
    
    print("🚀 Testing TTS Manager with Gemini TTS")
    print("=" * 50)
    
    # Initialize TTS Manager
    print("🏗️  Initializing TTS Manager...")
    tts = TTSManager()
    
    # Test messages
    test_messages = [
        "Security alert: Unauthorized person detected in the restricted area.",
        "Please identify yourself and state your business.",
        "This area is under surveillance. You have 30 seconds to comply."
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 Test {i}: Testing message")
        print(f"📝 Message: {message}")
        
        try:
            # Generate audio (don't play immediately to avoid conflicts)
            audio_path = tts.text_to_speech(message, play_immediately=False)
            
            if audio_path:
                print(f"✅ Audio generated successfully: {audio_path}")
                
                # Check file size
                file_size = os.path.getsize(audio_path)
                print(f"📊 File size: {file_size} bytes")
                
                # Try to play it manually
                print("🔊 Playing audio...")
                tts.play_audio(audio_path)
                
                # Small delay between tests
                import time
                time.sleep(2)
                
            else:
                print("❌ Audio generation failed")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 TTS Manager testing completed!")
    
    # Cleanup
    try:
        tts.cleanup()
        print("🧹 Cleanup completed")
    except:
        pass

if __name__ == "__main__":
    test_tts_manager()