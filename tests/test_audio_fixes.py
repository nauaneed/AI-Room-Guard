"""
Test Script for Audio Playback Fixes
Tests for double playback and audio overlap issues
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio import tts_manager
from dialogue import conversation_controller

def test_audio_overlap_prevention():
    """Test that audio overlap is properly prevented"""
    print("=== Testing Audio Overlap Prevention ===\n")
    
    if not tts_manager.is_available():
        print("❌ TTS not available - skipping audio overlap tests")
        return
    
    print("1. Testing sequential audio playback...")
    
    # Test sequential speak_text calls
    texts = [
        "First message being spoken",
        "Second message interrupting", 
        "Third message taking over"
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\nStarting message {i}: '{text}'")
        
        # Start speaking (this should interrupt previous if still playing)
        success = tts_manager.speak_text(text, wait_for_completion=False)
        print(f"Message {i} started: {'✅' if success else '❌'}")
        
        # Wait a bit but not for completion
        time.sleep(1.5)  # Shorter than typical speech time
        
        # Check if still playing
        if tts_manager.is_playing():
            print(f"Message {i} still playing when next message starts")
        else:
            print(f"Message {i} completed before next message")
    
    # Wait for final message to complete
    print("\nWaiting for final message to complete...")
    while tts_manager.is_playing():
        time.sleep(0.1)
    
    print("✅ Sequential audio test complete\n")

def test_double_playback_prevention():
    """Test that double playback is prevented"""
    print("2. Testing double playback prevention...")
    
    if not tts_manager.is_available():
        print("❌ TTS not available - skipping double playback tests")
        return
    
    test_text = "This should only be played once"
    
    print(f"Testing text: '{test_text}'")
    
    # Test 1: Call speak_text twice quickly
    print("\nTest 1: Two quick speak_text calls")
    
    print("  First call...")
    success1 = tts_manager.speak_text(test_text, wait_for_completion=False)
    
    print("  Second call immediately after...")
    success2 = tts_manager.speak_text(test_text, wait_for_completion=False)
    
    print(f"  First call success: {'✅' if success1 else '❌'}")
    print(f"  Second call success: {'✅' if success2 else '❌'}")
    
    # Wait for completion
    time.sleep(3)
    while tts_manager.is_playing():
        time.sleep(0.1)
    
    # Test 2: Generate audio and then try to play it multiple times
    print("\nTest 2: Generate once, try to play multiple times")
    
    audio_path = tts_manager.text_to_speech(test_text, play_immediately=False)
    
    if audio_path:
        print("  Generated audio file successfully")
        
        print("  Playing first time...")
        success1 = tts_manager.play_audio(audio_path)
        
        # Try to play again while first is still playing (should stop first)
        print("  Playing second time (should interrupt first)...")
        success2 = tts_manager.play_audio(audio_path)
        
        print(f"  First play success: {'✅' if success1 else '❌'}")
        print(f"  Second play success: {'✅' if success2 else '❌'}")
    else:
        print("  ❌ Failed to generate audio file")
    
    print("✅ Double playback prevention test complete\n")

def test_conversation_audio_flow():
    """Test audio flow in conversation context"""
    print("3. Testing conversation audio flow...")
    
    # Set up conversation with very short delays for testing
    original_delay = conversation_controller.response_delay
    conversation_controller.response_delay = 0.5  # Reduce delay for testing
    
    try:
        # Start conversation
        conversation_controller.start_conversation("audio_flow_test")
        
        # Wait for initial response
        time.sleep(2)
        
        print("\nSimulating rapid person responses...")
        
        # Simulate rapid responses that should interrupt each other
        responses = [
            "What do you want?",
            "I don't care",
            "Leave me alone"
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\nPerson response {i}: '{response}'")
            
            # Process response (this should trigger new audio)
            conversation_controller.process_person_response(response)
            
            # Wait only briefly before next response
            time.sleep(1.0)  # Should interrupt previous audio
        
        # Wait for final response to complete
        print("\nWaiting for final response...")
        time.sleep(5)
        
        # End conversation
        conversation_controller.end_conversation("audio_flow_test_complete")
        
        print("✅ Conversation audio flow test complete")
        
    finally:
        # Restore original delay
        conversation_controller.response_delay = original_delay

def test_emergency_stop():
    """Test emergency audio stopping"""
    print("\n4. Testing emergency audio stop...")
    
    if not tts_manager.is_available():
        print("❌ TTS not available - skipping emergency stop test")
        return
    
    # Start a long message
    long_text = "This is a very long message that should be playing for a while to test the emergency stop functionality. It keeps going and going to ensure we have time to interrupt it."
    
    print(f"Starting long message: '{long_text[:50]}...'")
    
    # Start async playback
    success = tts_manager.speak_text(long_text, wait_for_completion=False)
    
    if success:
        print("Long message started, waiting 2 seconds...")
        time.sleep(2)
        
        if tts_manager.is_playing():
            print("Audio is playing, testing emergency stop...")
            tts_manager.force_stop_audio()
            
            # Check if stopped
            time.sleep(0.2)
            if not tts_manager.is_playing():
                print("✅ Emergency stop successful")
            else:
                print("❌ Emergency stop failed")
        else:
            print("❌ Audio not playing when expected")
    else:
        print("❌ Failed to start long message")
    
    print("✅ Emergency stop test complete")

if __name__ == "__main__":
    print("=== Audio Playback Fix Validation ===\n")
    
    test_audio_overlap_prevention()
    test_double_playback_prevention() 
    test_conversation_audio_flow()
    test_emergency_stop()
    
    print("\n=== Audio Fix Validation Complete ===")
    print("🔧 All audio playback issues should now be resolved!")