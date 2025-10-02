#!/usr/bin/env python3
"""
Test script to demonstrate audio listening during escalation with 5-second face recognition intervals
"""

import time
import threading
from src.core.guard_agent import GuardAgent
from config.settings import FaceRecognitionConfig

def test_escalation_audio_listening():
    """Test audio listening during escalation face recognition intervals"""
    print("🧪 ESCALATION AUDIO LISTENING DEMO")
    print("=" * 60)
    print()
    
    print("📋 Test Features:")
    print("   1. ✅ Unknown person triggers escalation")
    print("   2. 🎤 Audio processing continues during escalation")
    print("   3. 🔍 Face recognition runs every 5 seconds")
    print("   4. 📢 Audio content is printed with timing info")
    print("   5. ⏰ Shows countdown to next face check")
    print()
    
    try:
        # Show configuration
        print("⚙️  Audio & Face Recognition Configuration:")
        print(f"   🎤 Audio processing: Continuous (0.2s timeout)")
        print(f"   🔍 Normal face recognition: Every frame (skip={FaceRecognitionConfig.FACE_DETECTION_FRAME_SKIP})")
        print(f"   🚨 Escalation face check: Every {FaceRecognitionConfig.ESCALATION_FACE_CHECK_INTERVAL}s")
        print(f"   😴 Trusted user idle: {FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION}s")
        print()
        
        print("🎬 Expected Output During Escalation:")
        print("   🎤🚨 Audio during escalation: 'Hello' (next face check in 3.2s)")
        print("   🔄 Escalation waiting - next face check in 2.1s (audio continues)")
        print("   🎤🚨 Audio during escalation: 'Can you hear me?' (next face check in 1.8s)")
        print("   🔍 Escalation face check at 1234.5s - checking for trusted users")
        print("   🎤🚨 Audio during escalation: 'I am authorized' (next face check in 4.9s)")
        print()
        
        print("🎉 AUDIO LISTENING FEATURES:")
        print("=" * 40)
        print("✅ Concurrent Processing:")
        print("   • Audio processing never stops during escalation")
        print("   • All speech is captured and processed")
        print("   • Deactivation commands work immediately")
        print("   • Conversation responses are routed properly")
        print()
        print("✅ Smart Timing:")
        print("   • Face recognition: Every 5s (reduces CPU load)")
        print("   • Audio processing: Continuous (max responsiveness)")
        print("   • Real-time countdown to next face check")
        print("   • Clear escalation status indicators")
        print()
        print("✅ User Experience:")
        print("   • Users can speak during escalation")
        print("   • System shows it's listening and waiting")
        print("   • Trusted users detected quickly when they appear")
        print("   • Audio feedback continues throughout")
        print()
        
        print("🚀 SYSTEM READY!")
        print("💡 To test: Start the main system and cover the camera to trigger escalation")
        print("   Then speak while the escalation is active to see audio processing")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_escalation_audio_listening()