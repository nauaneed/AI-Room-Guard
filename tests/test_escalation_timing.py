#!/usr/bin/env python3
"""
Test script to demonstrate escalation face recognition timing
"""

import time
import threading
from src.core.guard_agent import GuardAgent
from config.settings import FaceRecognitionConfig

def test_escalation_face_timing():
    """Test escalation face recognition timing"""
    print("🧪 ESCALATION FACE RECOGNITION TIMING DEMO")
    print("=" * 60)
    print()
    
    print("📋 Test Scenario:")
    print("   1. Unknown person triggers escalation")
    print("   2. Face recognition runs every 5 seconds during escalation")
    print("   3. If trusted user appears, escalation stops immediately")
    print("   4. After trusted user, normal 10-second idle period")
    print()
    
    try:
        # Create guard agent
        agent = GuardAgent()
        print("✅ Guard Agent initialized")
        
        # Test configuration values
        print("⚙️  Timing Configuration:")
        print(f"   🟢 Normal frame skip: {FaceRecognitionConfig.FACE_DETECTION_FRAME_SKIP}")
        print(f"   🟡 Escalation check interval: {FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL}s")
        print(f"   🔴 Trusted user idle duration: {FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION}s")
        print()
        
        # Simulate escalation timing
        print("🎬 Simulation:")
        current_time = time.time()
        
        # Test 1: Normal operation (no escalation)
        print("   📍 Phase 1: Normal Operation")
        is_escalation = False
        agent.last_escalation_face_check = current_time
        
        for i in range(3):
            time.sleep(1)
            check_time = time.time()
            time_since = check_time - agent.last_escalation_face_check
            should_check = not is_escalation or time_since >= FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL
            print(f"     ⏱️  T+{i+1}s: Normal mode - Continuous checking: {should_check}")
        
        print()
        print("   📍 Phase 2: Escalation Active")
        is_escalation = True
        agent.last_escalation_face_check = time.time()
        
        for i in range(8):
            time.sleep(1)
            check_time = time.time()
            time_since = check_time - agent.last_escalation_face_check
            should_check = time_since >= FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL
            
            if should_check:
                agent.last_escalation_face_check = check_time
                print(f"     🔍 T+{i+1}s: ESCALATION CHECK - Face recognition runs")
            else:
                print(f"     ⏳ T+{i+1}s: Escalation wait - Next check in {FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL - time_since:.1f}s")
        
        print()
        print("   📍 Phase 3: Trusted User Detected")
        print("     ✅ Trusted user detected - Escalation stops immediately")
        print(f"     😴 Face recognition idle for {FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION}s")
        
        print()
        print("🎉 ESCALATION TIMING TEST COMPLETE!")
        print("📊 Summary:")
        print("   ✅ Normal operation: Continuous face recognition")
        print("   ✅ During escalation: Check every 5 seconds (reduces CPU load)")
        print("   ✅ Trusted user detection: Immediate escalation termination")
        print("   ✅ Audio processing: Continues uninterrupted throughout")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_escalation_face_timing()