"""
Test Script for TTS Integration (Step 2)
Tests text-to-speech conversion and audio playback
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio import tts_manager

def test_tts_basic():
    """Test basic TTS functionality"""
    print("=== Testing TTS Integration (Step 2) ===\n")
    
    # Test 1: Check if TTS is available
    print("1. Checking TTS availability...")
    is_available = tts_manager.is_available()
    print(f"   TTS Available: {'✅' if is_available else '❌'}")
    
    if not is_available:
        print("   ❌ TTS not available - audio system initialization failed")
        return
    else:
        print("   ✅ TTS successfully initialized\n")
    
    # Test 2: Basic text-to-speech conversion (without playing)
    print("2. Testing TTS conversion...")
    test_text = "Please identify yourself"
    
    try:
        audio_path = tts_manager.text_to_speech(test_text, play_immediately=False)
        
        if audio_path and os.path.exists(audio_path):
            print(f"   ✅ TTS conversion successful")
            print(f"   Audio file: {os.path.basename(audio_path)}")
            print(f"   Conversion time: {tts_manager.get_last_conversion_time():.2f}s")
        else:
            print("   ❌ TTS conversion failed")
            return
            
    except Exception as e:
        print(f"   ❌ TTS conversion error: {e}")
        return
    
    print()
    
    # Test 3: Audio playback
    print("3. Testing audio playback...")
    try:
        playback_success = tts_manager.play_audio(audio_path)
        
        if playback_success:
            print("   ✅ Audio playback successful")
        else:
            print("   ❌ Audio playback failed")
            
    except Exception as e:
        print(f"   ❌ Audio playback error: {e}")
    
    print()
    
    # Test 4: High-level speak_text method
    print("4. Testing high-level speak_text method...")
    
    test_phrases = [
        "Hello, I don't recognize you.",
        "Please state your business here.",
        "You are trespassing on private property."
    ]
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"   Testing phrase {i}: '{phrase}'")
        try:
            success = tts_manager.speak_text(phrase, wait_for_completion=True)
            print(f"   {'✅' if success else '❌'} Phrase {i} {'successful' if success else 'failed'}")
        except Exception as e:
            print(f"   ❌ Phrase {i} error: {e}")
        print()
    
    # Test 5: Test different settings
    print("5. Testing TTS settings...")
    
    # Test slow speed
    print("   Testing slow speed...")
    tts_manager.set_speed(True)
    slow_success = tts_manager.speak_text("This is slow speech", wait_for_completion=True)
    print(f"   {'✅' if slow_success else '❌'} Slow speed test")
    
    # Reset to normal speed
    tts_manager.set_speed(False)
    
    print()
    
    # Test 6: Cleanup
    print("6. Testing cleanup...")
    tts_manager.cleanup_temp_files()
    print("   ✅ Cleanup completed")
    
    print("\n=== TTS Integration Test Complete ===")

def test_tts_quick():
    """Quick TTS test without audio playback (for CI/headless environments)"""
    print("=== Quick TTS Test (No Audio) ===\n")
    
    if not tts_manager.is_available():
        print("❌ TTS not available")
        return
    
    # Test conversion only
    test_text = "Quick test without audio playback"
    audio_path = tts_manager.text_to_speech(test_text, play_immediately=False)
    
    if audio_path and os.path.exists(audio_path):
        print("✅ TTS conversion successful")
        print(f"   File size: {os.path.getsize(audio_path)} bytes")
        
        # Cleanup
        tts_manager.cleanup_temp_files()
    else:
        print("❌ TTS conversion failed")

if __name__ == "__main__":
    # Check if we're in a headless environment
    if os.getenv('DISPLAY') is None and 'COLAB_GPU' not in os.environ:
        print("Headless environment detected - running quick test")
        test_tts_quick()
    else:
        test_tts_basic()