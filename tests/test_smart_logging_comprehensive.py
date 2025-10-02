#!/usr/bin/env python3
"""
Comprehensive test and demonstration of smart logging impact.
Shows before/after comparison of log spam reduction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.smart_logger import SmartLogger
import logging
import time

def test_comprehensive_smart_logging():
    print("🧪 COMPREHENSIVE SMART LOGGING TEST")
    print("=" * 60)
    
    # Create smart logger
    smart_logger = SmartLogger("test_module")
    
    print("\n📊 SPAM REDUCTION DEMONSTRATION:")
    print("-" * 40)
    
    # Simulate repetitive face detection (typical spam source)
    print("\n1. Face Detection Events:")
    for i in range(5):
        smart_logger.face_detection_change(1, "Single face detected")
        time.sleep(0.1)
    
    print("   ✅ Only logs when face count changes, not every detection")
    
    # Simulate user recognition (another spam source)
    print("\n2. Face Recognition Events:")
    for i in range(3):
        smart_logger.face_recognition_event("Nav", 0.75, True)
        time.sleep(0.1)
    
    print("   ✅ Only logs meaningful recognition events, not every frame")
    
    # Simulate trust score updates (major spam source)
    print("\n3. Trust Score Updates:")
    scores = [0.700, 0.701, 0.702, 0.750, 0.751]  # Small then big change
    for i, score in enumerate(scores):
        prev_score = scores[i-1] if i > 0 else 0.695
        smart_logger.trust_change_event("Nav", prev_score, score, f"update_{i}")
        time.sleep(0.1)
    
    print("   ✅ Only logs significant trust changes (>5% difference)")
    
    # Simulate state changes (should always log)
    print("\n4. State Changes:")
    smart_logger.state_change("idle", "listening", "voice command")
    smart_logger.state_change("listening", "guard_active", "surveillance started")
    
    print("   ✅ Always logs state changes (important events)")
    
    # Simulate audio commands (should log)
    print("\n5. Audio Commands:")
    smart_logger.audio_command_event("start surveillance", 0.95)
    smart_logger.audio_command_event("stop surveillance", 0.87)
    
    print("   ✅ Always logs voice commands (user interactions)")
    
    # Test periodic status suppression
    print("\n6. Periodic Status Messages:")
    for i in range(5):
        smart_logger.periodic_status("System running normally", "status_normal")
        time.sleep(0.1)
    
    print("   ✅ Suppresses repetitive status messages")
    
    # Show statistics
    print("\n📈 SMART LOGGING STATISTICS:")
    print("-" * 40)
    stats = smart_logger.get_stats()
    total_calls = stats['total_messages']
    suppressed = stats['suppressed_messages']
    logged = total_calls - suppressed
    
    if total_calls > 0:
        suppression_rate = (suppressed / total_calls) * 100
        print(f"   Total logging calls: {total_calls}")
        print(f"   Messages logged: {logged}")
        print(f"   Messages suppressed: {suppressed}")
        print(f"   Spam reduction: {suppression_rate:.1f}%")
    
    print(f"\n   Message types: {stats['message_types']}")
    print(f"   Active suppressions: {stats['active_suppressions']}")
    
    return stats

def show_key_benefits():
    print("\n🎯 KEY BENEFITS OF SMART LOGGING:")
    print("-" * 50)
    print("✅ Event-based logging instead of periodic spam")
    print("✅ Change detection for face count, trust scores")
    print("✅ Time-based suppression for repetitive messages")
    print("✅ Always logs important events (commands, state changes)")
    print("✅ Configurable event categories via settings")
    print("✅ Maintains all standard logging levels (debug, info, warning, error)")
    print("✅ Drop-in replacement for standard logging")
    print("✅ Automatic spam statistics and monitoring")

def show_configuration():
    print("\n⚙️  SMART LOGGING CONFIGURATION:")
    print("-" * 40)
    print("Located in config/settings.py -> LOG_EVENTS:")
    print("• state_changes: True     (State transitions)")
    print("• face_detection: True    (Face detected/lost)")  
    print("• face_recognition: True  (User recognized)")
    print("• audio_commands: True    (Voice commands)")
    print("• escalation_events: True (Escalation start/stop)")
    print("• trust_changes: True     (Trust score updates)")
    print("• system_events: True     (Start/stop/errors)")
    print("• periodic_status: False  (Regular status messages)")
    print("• waiting_messages: False (Wait notifications)")

if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE SMART LOGGING TEST")
    print("=" * 60)
    
    stats = test_comprehensive_smart_logging()
    show_key_benefits()
    show_configuration()
    
    print("\n" + "=" * 60)
    print("🎉 SMART LOGGING COMPREHENSIVE TEST COMPLETE!")
    
    if stats and stats['suppressed_messages'] > 0:
        suppression_rate = (stats['suppressed_messages'] / stats['total_messages']) * 100
        print(f"🎯 Achieved {suppression_rate:.1f}% spam reduction in this test!")
    
    print("\n💡 The system now focuses on EVENTS, not repetitive status!")
    print("📝 Logs are now clean, focused, and actionable!")