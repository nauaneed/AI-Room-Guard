"""
Simple Audio Cutoff Test
Focus on the specific issue of audio being cut off
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio import tts_manager
from dialogue import conversation_controller

def test_simple_audio_cutoff():
    """Simple test for audio cutoff issues"""
    print("=== Simple Audio Cutoff Test ===\n")
    
    if not tts_manager.is_available():
        print("❌ TTS not available")
        return
    
    print("1. Testing if audio gets cut off during conversation...")
    
    # Start conversation
    print("Starting conversation...")
    conversation_controller.start_conversation("cutoff_test")
    
    # Wait for initial response
    print("Waiting for initial response...")
    time.sleep(4)  # Give it more time
    
    print("\nSending person response that should trigger escalation...")
    
    # Send a response that should cause escalation
    conversation_controller.process_person_response("I don't have to tell you anything")
    
    print("Waiting for escalated response...")
    time.sleep(5)  # Wait longer for response
    
    print("\nSending another response...")
    conversation_controller.process_person_response("Go away")
    
    print("Waiting for final response...")
    time.sleep(5)
    
    # End conversation
    print("\nEnding conversation...")
    conversation_controller.end_conversation("cutoff_test_complete")
    
    print("✅ Simple cutoff test complete")

def test_manual_tts_interruption():
    """Test TTS interruption manually"""
    print("\n2. Testing manual TTS interruption...")
    
    if not tts_manager.is_available():
        print("❌ TTS not available")
        return
    
    # Test long message being interrupted
    long_message = "This is a very long message that should take several seconds to speak and we want to see if it can be properly interrupted by another message without causing audio artifacts or cutoffs."
    short_message = "Stop talking now!"
    
    print(f"Speaking long message: '{long_message[:50]}...'")
    
    # Start long message without waiting
    tts_manager.speak_text(long_message, wait_for_completion=False)
    
    # Wait 2 seconds
    print("Waiting 2 seconds...")
    time.sleep(2)
    
    print("Interrupting with short message...")
    # This should interrupt the long message
    tts_manager.speak_text(short_message, wait_for_completion=True)
    
    print("Short message completed")
    
    # Wait a bit more
    time.sleep(1)
    
    print("✅ Manual TTS interruption test complete")

if __name__ == "__main__":
    test_simple_audio_cutoff()
    test_manual_tts_interruption()