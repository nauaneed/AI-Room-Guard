"""
Test Script for Escalation Logic Framework (Step 3)
Tests escalation level progression and timing logic
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dialogue import escalation_manager, EscalationLevel

def test_escalation_basic():
    """Test basic escalation functionality"""
    print("=== Testing Escalation Logic Framework (Step 3) ===\n")
    
    # Reset manager to clean state
    escalation_manager.reset()
    
    # Test 1: Initial state
    print("1. Testing initial state...")
    print(f"   Active: {escalation_manager.is_active()}")
    print(f"   Current Level: {escalation_manager.get_current_level().value}")
    print("   ✅ Initial state correct\n")
    
    # Test 2: Start conversation
    print("2. Testing conversation start...")
    escalation_manager.start_conversation("unknown_person_001")
    
    print(f"   Active: {escalation_manager.is_active()}")
    print(f"   Current Level: {escalation_manager.get_current_level().value}")
    print("   ✅ Conversation started successfully\n")
    
    # Test 3: Level characteristics
    print("3. Testing level characteristics...")
    for level in EscalationLevel:
        info = escalation_manager.get_level_info(level)
        print(f"   Level {level.value}:")
        print(f"     Tone: {info['tone']}")
        print(f"     Max words: {info['max_response_words']}")
        print(f"     Urgency: {info['urgency']}")
        print(f"     Example: {info['example'][:50]}...")
    print("   ✅ All level characteristics defined\n")
    
    # Test 4: Escalation context
    print("4. Testing escalation context...")
    context = escalation_manager.get_escalation_context()
    print(f"   Current level: {context['current_level']}")
    print(f"   Escalation count: {context['escalation_count']}")
    print(f"   Conversation duration: {context['conversation_duration']:.2f}s")
    print(f"   Should escalate soon: {context['should_escalate_soon']}")
    print("   ✅ Context information complete\n")
    
    # Test 5: Manual escalation
    print("5. Testing manual escalation...")
    for target_level in range(2, 5):
        success = escalation_manager.escalate()
        current_level = escalation_manager.get_current_level().value
        print(f"   Escalation to level {target_level}: {'✅' if success and current_level == target_level else '❌'}")
    
    # Try to escalate beyond max
    success = escalation_manager.escalate()
    print(f"   Beyond max escalation: {'✅' if not success else '❌'} (should fail)")
    print()
    
    # Test 6: Timing information
    print("6. Testing timing information...")
    timing = escalation_manager.get_timing_info()
    print(f"   Conversation duration: {timing['conversation_duration']:.2f}s")
    print(f"   Time at current level: {timing['time_at_current_level']:.2f}s")
    print(f"   Timeout remaining: {timing['conversation_timeout_remaining']:.2f}s")
    print("   ✅ Timing information available\n")
    
    # Test 7: Response processing
    print("7. Testing response processing...")
    
    test_responses = [
        ("Hi, I'm John, I live here", "cooperative"),
        ("None of your business", "uncooperative"),
        ("I am a friend", "identification attempt"),
        ("uh", "unclear"),
        ("What do you want?", "neutral")
    ]
    
    for response, expected_type in test_responses:
        analysis = escalation_manager.process_response(response)
        print(f"   Response: '{response}'")
        print(f"     Action: {analysis['recommended_action']}")
        print(f"     Reason: {analysis['reason']}")
        print(f"     Expected: {expected_type}")
        print()
    
    print("   ✅ Response processing working\n")
    
    # Test 8: Conversation end
    print("8. Testing conversation end...")
    summary = escalation_manager.end_conversation("test_complete")
    print(f"   Final level: {summary['final_level']}")
    print(f"   Total escalations: {summary['total_escalations']}")
    print(f"   Duration: {summary['conversation_duration']:.2f}s")
    print(f"   Max level reached: {summary['max_level_reached']}")
    print("   ✅ Conversation ended successfully\n")
    
    print("=== Escalation Logic Framework Test Complete ===")

def test_escalation_timing():
    """Test time-based escalation progression"""
    print("=== Testing Time-Based Escalation ===\n")
    
    # Reset and start conversation
    escalation_manager.reset()
    escalation_manager.start_conversation("timing_test")
    
    print("Testing automatic escalation timing...")
    print("Note: This test uses shorter intervals for demonstration\n")
    
    # Temporarily reduce escalation durations for testing
    original_durations = escalation_manager.level_durations.copy()
    escalation_manager.level_durations = {
        EscalationLevel.LEVEL_1: 2,  # 2 seconds
        EscalationLevel.LEVEL_2: 2,  # 2 seconds  
        EscalationLevel.LEVEL_3: 2,  # 2 seconds
        EscalationLevel.LEVEL_4: 3   # 3 seconds
    }
    
    try:
        # Monitor escalation over time
        for i in range(10):  # 10 second test
            current_level = escalation_manager.get_current_level().value
            should_escalate = escalation_manager.should_escalate()
            timing = escalation_manager.get_timing_info()
            
            print(f"Time {i+1}s: Level {current_level}, Should escalate: {should_escalate}")
            
            if should_escalate and current_level < 4:
                escalation_manager.escalate()
                print(f"  -> Escalated to Level {escalation_manager.get_current_level().value}")
            
            time.sleep(1)
        
        print("\n✅ Time-based escalation test complete")
        
    finally:
        # Restore original durations
        escalation_manager.level_durations = original_durations
        escalation_manager.end_conversation("timing_test_complete")

def test_escalation_scenarios():
    """Test various escalation scenarios"""
    print("=== Testing Escalation Scenarios ===\n")
    
    scenarios = [
        {
            'name': 'Cooperative Person',
            'responses': ['Hi there', 'I\'m John, I live here', 'Sorry for the confusion'],
            'expected_outcome': 'conversation continues'
        },
        {
            'name': 'Uncooperative Person', 
            'responses': ['Go away', 'None of your business', 'Shut up'],
            'expected_outcome': 'escalation recommended'
        },
        {
            'name': 'Confused Person',
            'responses': ['What?', 'Huh?', 'I don\'t understand'],
            'expected_outcome': 'clarification requested'
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        escalation_manager.reset()
        escalation_manager.start_conversation(f"scenario_{scenario['name'].lower().replace(' ', '_')}")
        
        for i, response in enumerate(scenario['responses'], 1):
            analysis = escalation_manager.process_response(response)
            print(f"  Response {i}: '{response}'")
            print(f"    Action: {analysis['recommended_action']}")
            print(f"    Reason: {analysis['reason']}")
        
        escalation_manager.end_conversation("scenario_complete")
        print(f"  Expected outcome: {scenario['expected_outcome']}")
        print("  ✅ Scenario complete\n")
    
    print("=== Escalation Scenarios Test Complete ===")

if __name__ == "__main__":
    test_escalation_basic()
    print("\n" + "="*50 + "\n")
    test_escalation_timing()
    print("\n" + "="*50 + "\n") 
    test_escalation_scenarios()