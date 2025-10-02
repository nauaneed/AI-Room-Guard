"""
Test Script for LLM Integration (Step 1)
Tests basic LLM connection and response generation
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm import dialogue_generator

def test_llm_basic():
    """Test basic LLM functionality"""
    print("=== Testing LLM Integration (Step 1) ===\n")
    
    # Test 1: Check if LLM is available
    print("1. Checking LLM availability...")
    is_available = dialogue_generator.is_available()
    print(f"   LLM Available: {'✅' if is_available else '❌'}")
    
    if not is_available:
        print("   Note: LLM not available - will use fallback responses")
        print("   To enable LLM: Set GOOGLE_GEMINI_API_KEY environment variable")
        print("   Get free API key at: https://makersuite.google.com/app/apikey\n")
    else:
        print("   ✅ LLM successfully configured\n")
    
    # Test 2: Generate simple response
    print("2. Testing basic response generation...")
    try:
        response = dialogue_generator.generate_response(
            "An unknown person has entered the room", 
            escalation_level=1
        )
        print(f"   Generated Response: '{response}'")
        print(f"   Response Time: {dialogue_generator.get_last_response_time():.2f}s")
        
        if len(response) > 0:
            print("   ✅ Response generation successful\n")
        else:
            print("   ❌ Empty response generated\n")
            
    except Exception as e:
        print(f"   ❌ Error generating response: {e}\n")
    
    # Test 3: Test different escalation levels
    print("3. Testing escalation levels...")
    for level in range(1, 5):
        try:
            response = dialogue_generator.generate_response(
                "Person refuses to identify themselves",
                escalation_level=level
            )
            print(f"   Level {level}: '{response}'")
        except Exception as e:
            print(f"   Level {level}: ❌ Error - {e}")
    
    print("\n=== LLM Integration Test Complete ===")
    
    # Show conversation history
    history = dialogue_generator.get_conversation_history()
    print(f"\nConversation History: {len(history)} interactions")

if __name__ == "__main__":
    test_llm_basic()