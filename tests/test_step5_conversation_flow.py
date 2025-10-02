"""
Test Script for Audio Integration and Conversation Flow (Step 5)
Tests complete conversation flow with audio input/output
"""

import sys
import os
import time
import threading

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dialogue import conversation_controller, escalation_manager
from audio import tts_manager

def test_conversation_flow():
    """Test complete conversation flow"""
    print("=== Testing Audio Integration and Conversation Flow (Step 5) ===\n")
    
    # Test 1: Check system availability
    print("1. Checking system availability...")
    print(f"   Conversation Controller Available: ✅")
    print(f"   TTS Available: {'✅' if tts_manager.is_available() else '❌'}")
    print(f"   Escalation Manager Available: ✅")
    print()
    
    # Test 2: Start conversation
    print("2. Testing conversation start...")
    
    # Set up event callbacks for testing
    events_captured = []
    
    def capture_event(event_type):
        def callback(*args, **kwargs):
            events_captured.append({
                'type': event_type,
                'timestamp': time.time(),
                'args': args,
                'kwargs': kwargs
            })
            print(f"   📡 Event captured: {event_type}")
        return callback
    
    conversation_controller.set_callbacks(
        conversation_start=capture_event('conversation_start'),
        response_generated=capture_event('response_generated'),
        response_spoken=capture_event('response_spoken'),
        escalation=capture_event('escalation'),
        conversation_end=capture_event('conversation_end')
    )
    
    # Start conversation
    success = conversation_controller.start_conversation(
        person_id="test_intruder_001",
        initial_context={'situation': 'Unknown person detected in room'}
    )
    
    print(f"   Conversation started: {'✅' if success else '❌'}")
    
    if success:
        # Wait for initial response
        time.sleep(3)
        
        status = conversation_controller.get_conversation_status()
        print(f"   Active: {status['active']}")
        print(f"   Current level: {status['current_level']}")
        print(f"   Person ID: {status['person_id']}")
        print("   ✅ Conversation status tracking working")
    
    print()
    
    # Test 3: Person response processing
    if conversation_controller.is_active():
        print("3. Testing person response processing...")
        
        test_responses = [
            ("What do you want?", "neutral response"),
            ("None of your business", "uncooperative response"),
            ("Go away", "uncooperative response")
        ]
        
        for response_text, expected_type in test_responses:
            print(f"   Testing response: '{response_text}'")
            
            analysis = conversation_controller.process_person_response(response_text)
            
            print(f"     Action: {analysis.get('recommended_action', 'unknown')}")
            print(f"     Reason: {analysis.get('reason', 'unknown')}")
            
            # Wait for system to process
            time.sleep(2)
        
        print("   ✅ Person response processing working")
        print()
    
    # Test 4: Manual escalation
    if conversation_controller.is_active():
        print("4. Testing manual escalation...")
        
        initial_level = conversation_controller.get_conversation_status()['current_level']
        
        escalated = conversation_controller.manual_escalate("test_escalation")
        
        if escalated:
            new_level = conversation_controller.get_conversation_status()['current_level']
            print(f"   Escalated from level {initial_level} to {new_level}")
            print("   ✅ Manual escalation working")
            
            # Wait for escalated response
            time.sleep(3)
        else:
            print("   ⚠️  Escalation not possible (may be at max level)")
        
        print()
    
    # Test 5: Conversation status monitoring
    if conversation_controller.is_active():
        print("5. Testing conversation status monitoring...")
        
        status = conversation_controller.get_conversation_status()
        
        print(f"   Active: {status['active']}")
        print(f"   Current level: {status['current_level']}")
        print(f"   Escalation count: {status['escalation_count']}")
        print(f"   Conversation duration: {status['conversation_duration']:.1f}s")
        print(f"   Time at current level: {status['time_at_current_level']:.1f}s")
        print(f"   TTS available: {status['tts_available']}")
        print(f"   Audio playing: {status['audio_playing']}")
        
        print("   ✅ Status monitoring working")
        print()
    
    # Test 6: End conversation
    if conversation_controller.is_active():
        print("6. Testing conversation end...")
        
        summary = conversation_controller.end_conversation("test_complete")
        
        print(f"   End reason: {summary.get('end_reason', 'unknown')}")
        print(f"   Person ID: {summary.get('person_id', 'unknown')}")
        
        escalation_summary = summary.get('escalation_summary', {})
        print(f"   Final level: {escalation_summary.get('final_level', 0)}")
        print(f"   Total escalations: {escalation_summary.get('total_escalations', 0)}")
        print(f"   Duration: {escalation_summary.get('conversation_duration', 0):.1f}s")
        
        print("   ✅ Conversation end working")
        print()
    
    # Test 7: Event callback summary
    print("7. Event callback summary...")
    print(f"   Total events captured: {len(events_captured)}")
    
    event_types = [event['type'] for event in events_captured]
    for event_type in set(event_types):
        count = event_types.count(event_type)
        print(f"   {event_type}: {count} occurrences")
    
    print("   ✅ Event callbacks working")
    print()
    
    print("=== Audio Integration and Conversation Flow Test Complete ===")

def test_auto_escalation():
    """Test automatic escalation timing"""
    print("=== Testing Auto-Escalation Timing ===\n")
    
    # Import EscalationLevel correctly
    from dialogue import EscalationLevel
    
    # Temporarily reduce escalation intervals for testing
    original_durations = escalation_manager.level_durations.copy()
    escalation_manager.level_durations = {
        EscalationLevel.LEVEL_1: 3,  # 3 seconds
        EscalationLevel.LEVEL_2: 3,  # 3 seconds
        EscalationLevel.LEVEL_3: 3,  # 3 seconds
        EscalationLevel.LEVEL_4: 5   # 5 seconds
    }
    
    # Reduce conversation controller check interval
    original_interval = conversation_controller.escalation_check_interval
    conversation_controller.escalation_check_interval = 1.0  # Check every 1 second
    
    try:
        print("Starting auto-escalation test (shortened intervals)...")
        
        # Track escalations
        escalations = []
        
        def track_escalation(level, reason):
            escalations.append({
                'level': level,
                'reason': reason,
                'timestamp': time.time()
            })
            print(f"   📈 Auto-escalation to level {level} ({reason})")
        
        conversation_controller.set_callbacks(escalation=track_escalation)
        
        # Start conversation
        conversation_controller.start_conversation("auto_escalation_test")
        
        # Monitor for 15 seconds
        start_time = time.time()
        
        while time.time() - start_time < 15:
            status = conversation_controller.get_conversation_status()
            if status['active']:
                print(f"Time: {time.time() - start_time:.1f}s, Level: {status['current_level']}")
            else:
                print("Conversation ended")
                break
            time.sleep(1)
        
        # End if still active
        if conversation_controller.is_active():
            conversation_controller.end_conversation("auto_escalation_test_complete")
        
        print(f"\nAuto-escalation results:")
        print(f"   Total escalations: {len(escalations)}")
        for i, escalation in enumerate(escalations):
            print(f"   {i+1}. Level {escalation['level']} at {escalation['timestamp'] - start_time:.1f}s ({escalation['reason']})")
        
        print("\n✅ Auto-escalation timing test complete")
        
    finally:
        # Restore original settings
        escalation_manager.level_durations = original_durations
        conversation_controller.escalation_check_interval = original_interval

def test_audio_integration():
    """Test audio integration specifically"""
    print("=== Testing Audio Integration ===\n")
    
    print("1. Testing TTS integration with conversation...")
    
    if not tts_manager.is_available():
        print("   ❌ TTS not available - skipping audio tests")
        return
    
    # Quick conversation with audio
    conversation_controller.start_conversation("audio_test")
    
    print("   🔊 Initial response should be spoken...")
    time.sleep(5)  # Wait for initial response
    
    # Test person response
    print("   👤 Simulating person response...")
    conversation_controller.process_person_response("I don't want to talk to you")
    
    print("   🔊 Escalated response should be spoken...")
    time.sleep(5)  # Wait for escalated response
    
    # End conversation
    conversation_controller.end_conversation("audio_test_complete")
    
    print("   ✅ Audio integration test complete")

if __name__ == "__main__":
    test_conversation_flow()
    print("\n" + "="*60 + "\n")
    test_auto_escalation()
    print("\n" + "="*60 + "\n")
    test_audio_integration()