"""
Test Script for Audio Threading and Cutoff Issues
Tests specifically for audio being cut off by overlapping responses
"""

import sys
import os
import time
import threading

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio import tts_manager
from dialogue import conversation_controller, escalation_manager

def test_threading_audio_cutoff():
    """Test that audio doesn't get cut off by threading issues"""
    print("=== Testing Threading Audio Cutoff Issues ===\n")
    
    if not tts_manager.is_available():
        print("❌ TTS not available - skipping threading tests")
        return
    
    print("1. Testing conversation with rapid escalation...")
    
    # Reset conversation controller
    if conversation_controller.is_active():
        conversation_controller.end_conversation("reset")
    
    # Reduce timing to force rapid escalation
    original_durations = escalation_manager.level_durations.copy()
    escalation_manager.level_durations = {
        escalation_manager.EscalationLevel.LEVEL_1: 2,  # 2 seconds
        escalation_manager.EscalationLevel.LEVEL_2: 2,  # 2 seconds
        escalation_manager.EscalationLevel.LEVEL_3: 2,  # 2 seconds
        escalation_manager.EscalationLevel.LEVEL_4: 3   # 3 seconds
    }
    
    # Reduce response delay to make it faster
    original_delay = conversation_controller.response_delay
    conversation_controller.response_delay = 0.5
    
    # Reduce escalation check interval
    original_interval = conversation_controller.escalation_check_interval
    conversation_controller.escalation_check_interval = 1.0
    
    try:
        print("Starting conversation with accelerated timing...")
        
        # Start conversation
        conversation_controller.start_conversation("threading_test")
        
        # Wait for initial response to start
        time.sleep(1)
        
        print("\nSimulating rapid uncooperative responses...")
        
        # Send rapid responses that should cause escalation
        responses = [
            "I don't have to tell you",
            "Mind your own business", 
            "Get lost",
            "I'm not leaving"
        ]
        
        for i, response in enumerate(responses):
            print(f"\n--- Response {i+1}: '{response}' ---")
            
            # Check current speaking status
            with conversation_controller.speech_lock:
                is_speaking = conversation_controller.is_speaking
            
            print(f"System currently speaking: {is_speaking}")
            
            # Process response
            conversation_controller.process_person_response(response)
            
            # Wait briefly and check if audio was interrupted
            time.sleep(1.5)
            
            # Check final speaking status
            with conversation_controller.speech_lock:
                is_speaking_after = conversation_controller.is_speaking
            
            print(f"System speaking after response: {is_speaking_after}")
        
        # Wait for final response to complete
        print("\nWaiting for final system response...")
        time.sleep(5)
        
        # Check if still speaking
        with conversation_controller.speech_lock:
            final_speaking = conversation_controller.is_speaking
        
        print(f"Final speaking status: {final_speaking}")
        
        # End conversation
        conversation_controller.end_conversation("threading_test_complete")
        
        print("✅ Threading test completed")
        
    finally:
        # Restore original settings
        escalation_manager.level_durations = original_durations
        conversation_controller.response_delay = original_delay
        conversation_controller.escalation_check_interval = original_interval

def test_speech_lock_mechanism():
    """Test the speech lock mechanism directly"""
    print("\n2. Testing speech lock mechanism...")
    
    if not tts_manager.is_available():
        print("❌ TTS not available - skipping speech lock test")
        return
    
    # Reset conversation
    if conversation_controller.is_active():
        conversation_controller.end_conversation("reset")
    
    # Start conversation
    conversation_controller.start_conversation("speech_lock_test")
    
    # Wait for initial response
    time.sleep(2)
    
    print("\nTesting overlapping response generation...")
    
    # Try to trigger multiple responses simultaneously
    def trigger_response(context_name):
        print(f"  Thread {context_name}: Attempting to generate response")
        context = {'test_context': context_name}
        conversation_controller._generate_and_speak_response(context)
        print(f"  Thread {context_name}: Response generation complete")
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=trigger_response, args=(f"thread_{i+1}",))
        threads.append(thread)
    
    # Start all threads at once
    print("Starting 3 simultaneous response generation threads...")
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("All threads completed")
    
    # End conversation
    conversation_controller.end_conversation("speech_lock_test_complete")
    
    print("✅ Speech lock test completed")

def test_audio_interruption_scenarios():
    """Test various audio interruption scenarios"""
    print("\n3. Testing audio interruption scenarios...")
    
    if not tts_manager.is_available():
        print("❌ TTS not available - skipping interruption tests")
        return
    
    # Test 1: Long message interrupted by short message
    print("\nScenario 1: Long message interrupted by short message")
    
    long_text = "This is a very long message that should take a while to speak and we want to make sure it can be properly interrupted by a shorter message when needed."
    short_text = "Stop!"
    
    print(f"Starting long message: '{long_text[:50]}...'")
    
    # Start long message asynchronously
    tts_manager.speak_text(long_text, wait_for_completion=False)
    
    # Wait a bit
    time.sleep(2)
    
    if tts_manager.is_playing():
        print("Long message is playing, interrupting with short message...")
        tts_manager.speak_text(short_text, wait_for_completion=True)
        print("Short message completed")
    else:
        print("Long message already completed")
    
    # Test 2: Multiple rapid interruptions
    print("\nScenario 2: Multiple rapid interruptions")
    
    messages = [
        "First message",
        "Second message",
        "Third message", 
        "Final message"
    ]
    
    for i, message in enumerate(messages):
        print(f"Message {i+1}: '{message}'")
        tts_manager.speak_text(message, wait_for_completion=False)
        time.sleep(0.5)  # Very short delay
    
    # Wait for final message
    print("Waiting for final message to complete...")
    while tts_manager.is_playing():
        time.sleep(0.1)
    
    print("✅ Audio interruption scenarios completed")

if __name__ == "__main__":
    print("=== Comprehensive Audio Threading and Cutoff Test ===\n")
    
    test_threading_audio_cutoff()
    test_speech_lock_mechanism()
    test_audio_interruption_scenarios()
    
    print("\n=== Audio Threading Test Complete ===")
    print("🔧 If audio is still being cut off, there may be deeper timing issues!")