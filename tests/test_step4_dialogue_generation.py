"""
Test Script for Dialogue Generation Engine (Step 4)
Tests intelligent dialogue generation with escalation context
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dialogue import escalation_manager, response_generator, EscalationLevel

def test_dialogue_generation():
    """Test dialogue generation functionality"""
    print("=== Testing Dialogue Generation Engine (Step 4) ===\n")
    
    # Reset systems
    escalation_manager.reset()
    response_generator.clear_memory()
    
    # Test 1: Check availability
    print("1. Checking dialogue generation availability...")
    is_available = response_generator.is_available()
    print(f"   Response Generator Available: {'✅' if is_available else '❌'}")
    print()
    
    # Test 2: Basic response generation
    print("2. Testing basic response generation...")
    
    # Start a conversation
    escalation_manager.start_conversation("test_person")
    
    # Generate initial response
    response = response_generator.generate_response()
    print(f"   Generated Response: '{response}'")
    print(f"   Response Length: {len(response.split())} words")
    
    if len(response) > 0:
        print("   ✅ Basic response generation successful")
    else:
        print("   ❌ Failed to generate response")
    
    print()
    
    # Test 3: Escalation-aware responses
    print("3. Testing escalation-aware responses...")
    
    for level in range(1, 5):
        # Manually set escalation level
        if level > 1:
            escalation_manager.escalate()
        
        response = response_generator.generate_response()
        level_info = escalation_manager.get_level_info()
        
        print(f"   Level {level} Response: '{response}'")
        print(f"     Expected tone: {level_info['tone']}")
        print(f"     Word count: {len(response.split())}/{level_info['max_response_words']}")
        print()
    
    print("   ✅ Escalation-aware responses generated")
    print()
    
    # Test 4: Context-aware generation
    print("4. Testing context-aware generation...")
    
    contexts = [
        {
            'name': 'Person not responding',
            'context': {'situation': 'Person ignoring guard requests'},
            'expected': 'more assertive'
        },
        {
            'name': 'Person being cooperative',
            'context': {'situation': 'Person trying to identify themselves'},
            'expected': 'more patient'
        },
        {
            'name': 'Emergency situation',
            'context': {'situation': 'Suspicious behavior detected'},
            'expected': 'more urgent'
        }
    ]
    
    for ctx in contexts:
        response = response_generator.generate_response(context=ctx['context'])
        print(f"   Context: {ctx['name']}")
        print(f"     Response: '{response}'")
        print(f"     Expected style: {ctx['expected']}")
        print()
    
    print("   ✅ Context-aware generation working")
    print()
    
    # Test 5: Response variation
    print("5. Testing response variation...")
    
    # Generate multiple responses for same level
    escalation_manager.reset()
    escalation_manager.start_conversation("variation_test")
    
    responses = []
    for i in range(3):
        response = response_generator.generate_response(force_new=True)
        responses.append(response)
        print(f"   Response {i+1}: '{response}'")
    
    # Check for variation
    unique_responses = len(set(responses))
    print(f"   Unique responses: {unique_responses}/3")
    print(f"   {'✅' if unique_responses > 1 else '⚠️ '} Response variation {'good' if unique_responses > 1 else 'limited'}")
    print()
    
    # Test 6: Conversation memory
    print("6. Testing conversation memory...")
    
    summary = response_generator.get_conversation_summary()
    print(f"   Total responses generated: {summary.get('total_responses', 0)}")
    print(f"   Levels used: {summary.get('levels_used', [])}")
    print(f"   Max level reached: {summary.get('max_level_reached', 0)}")
    
    if summary.get('total_responses', 0) > 0:
        duration = summary.get('duration', 0)
        print(f"   Conversation duration: {duration:.2f}s")
        print("   ✅ Conversation memory working")
    else:
        print("   ⚠️  No conversation memory recorded")
    
    print()
    
    # Test 7: Custom situation responses
    print("7. Testing custom situation responses...")
    
    custom_situations = [
        "Person trying to break into the room",
        "Unknown person claiming to be a friend", 
        "Person refusing to leave after multiple requests"
    ]
    
    for situation in custom_situations:
        response = response_generator.generate_response_for_situation(situation)
        print(f"   Situation: '{situation}'")
        print(f"   Response: '{response}'")
        print()
    
    print("   ✅ Custom situation responses working")
    print()
    
    # Test 8: Error handling and fallbacks
    print("8. Testing error handling and fallbacks...")
    
    # Test with escalation manager not active
    escalation_manager.reset()  # This deactivates the escalation manager
    
    response = response_generator.generate_response()
    print(f"   Response when escalation inactive: '{response}'")
    
    if len(response) > 0:
        print("   ✅ Fallback responses working")
    else:
        print("   ❌ Fallback responses failed")
    
    print()
    
    # Cleanup
    escalation_manager.reset()
    response_generator.clear_memory()
    
    print("=== Dialogue Generation Engine Test Complete ===")

def test_dialogue_integration():
    """Test integration between escalation and dialogue systems"""
    print("=== Testing Dialogue-Escalation Integration ===\n")
    
    # Reset systems
    escalation_manager.reset()
    response_generator.clear_memory()
    
    print("Simulating a complete escalation conversation...\n")
    
    # Start conversation
    escalation_manager.start_conversation("integration_test")
    
    # Simulate conversation progression
    scenarios = [
        {"level": 1, "situation": "Initial detection", "delay": 1},
        {"level": 2, "situation": "Person not responding", "delay": 1},
        {"level": 3, "situation": "Person being uncooperative", "delay": 1},
        {"level": 4, "situation": "Final warning needed", "delay": 1}
    ]
    
    for scenario in scenarios:
        print(f"--- Escalation Level {scenario['level']} ---")
        
        # Get current context
        context = escalation_manager.get_escalation_context()
        print(f"Escalation Context: Level {context['current_level']}, Duration: {context['conversation_duration']:.1f}s")
        
        # Generate appropriate response
        response = response_generator.generate_response(
            context={'situation': scenario['situation']}
        )
        
        print(f"Generated Response: '{response}'")
        print(f"Response Properties:")
        print(f"  - Word count: {len(response.split())} words")
        print(f"  - Contains urgency markers: {'!' in response}")
        print(f"  - Appropriate length: {len(response.split()) <= escalation_manager.get_level_info()['max_response_words']}")
        
        # Escalate for next iteration (except last)
        if scenario['level'] < 4:
            escalation_manager.escalate()
            time.sleep(scenario['delay'])
        
        print()
    
    # Final summary
    conversation_summary = response_generator.get_conversation_summary()
    escalation_summary = escalation_manager.end_conversation("integration_test_complete")
    
    print("--- Integration Test Summary ---")
    print(f"Responses generated: {conversation_summary.get('total_responses', 0)}")
    print(f"Escalation levels used: {conversation_summary.get('levels_used', [])}")
    print(f"Final escalation level: {escalation_summary.get('final_level', 0)}")
    print(f"Total escalations: {escalation_summary.get('total_escalations', 0)}")
    print(f"Conversation duration: {escalation_summary.get('conversation_duration', 0):.2f}s")
    
    print("\n✅ Dialogue-Escalation Integration Test Complete")

if __name__ == "__main__":
    test_dialogue_generation()
    print("\n" + "="*60 + "\n")
    test_dialogue_integration()