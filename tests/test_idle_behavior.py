#!/usr/bin/env python3
"""
Test script to demonstrate the new 10-second idle behavior after trusted user detection
"""

import time
from config.settings import FaceRecognitionConfig

def simulate_face_recognition_loop():
    """Simulate the face recognition loop with idle behavior"""
    print("🧪 Testing Face Recognition Idle Behavior")
    print(f"📋 Configuration: {FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION}s idle after trusted user")
    print("=" * 60)
    
    # Simulate the idle tracking variables
    face_recognition_idle_until = 0.0
    
    # Simulate detection timestamps
    current_time = time.time()
    
    print(f"⏰ Current time: {current_time:.1f}")
    print("\n🔍 Simulating face detection loop...")
    
    for i in range(15):  # 15 iterations
        loop_time = time.time()
        
        # Simulate the idle check that we added to the face recognition loop
        if loop_time < face_recognition_idle_until:
            remaining_idle_time = face_recognition_idle_until - loop_time
            print(f"😴 [Loop {i+1:2d}] Face recognition idle for {remaining_idle_time:.1f}s more (trusted user detected)")
            time.sleep(1.0)  # Sleep for 1 second and check again
            continue
        
        # Simulate normal face detection
        print(f"🔍 [Loop {i+1:2d}] Processing face detection at {loop_time:.1f}")
        
        # Simulate trusted user detection at iteration 5
        if i == 4:  # 5th iteration
            print(f"✅ [Loop {i+1:2d}] 🎯 TRUSTED USER DETECTED! Setting idle for {FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION}s")
            face_recognition_idle_until = loop_time + FaceRecognitionConfig.TRUSTED_USER_IDLE_DURATION
            print(f"😴 [Loop {i+1:2d}] Face recognition will idle until {face_recognition_idle_until:.1f}")
        
        time.sleep(1.0)  # Simulate processing delay
    
    print("\n🏁 Test completed!")
    print("📝 Summary:")
    print("   - Normal processing until trusted user detected")
    print("   - After detection: 10 seconds of idle (no face processing)")
    print("   - After idle period: Normal processing resumes")

if __name__ == "__main__":
    simulate_face_recognition_loop()