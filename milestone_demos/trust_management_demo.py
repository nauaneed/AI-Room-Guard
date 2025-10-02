"""
Trust Management Demo

This demo showcases the advanced trust management system for face recognition,
demonstrating multi-level trust evaluation, confidence-based decisions, and access control.
"""

import sys
import os
import time
import cv2
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_recognizer import FaceRecognizer, RecognitionResult
from src.core.trust_manager import TrustManager, TrustLevel
from src.core.user_database import TrustedUserDatabase
from src.video.camera_handler import CameraHandler
from config.settings import VideoConfig

class TrustManagementDemo:
    """Trust management system demonstration"""
    
    def __init__(self):
        print("🔧 Initializing Trust Management Demo...")
        
        # Initialize components
        self.face_recognizer = FaceRecognizer(tolerance=0.6)
        self.trust_manager = TrustManager()
        self.user_database = TrustedUserDatabase()
        self.camera_handler = CameraHandler()
        
        # Demo configuration
        self.demo_running = False
        self.recognition_count = 0
        self.test_scenarios = [
            TrustLevel.LOW,     # Require low trust
            TrustLevel.MEDIUM,  # Require medium trust  
            TrustLevel.HIGH,    # Require high trust
            TrustLevel.MAXIMUM  # Require maximum trust
        ]
        self.current_scenario = 0
        
        print("✅ Trust Management Demo initialized!")
    
    def display_trust_summary(self):
        """Display current trust profiles"""
        print("\n" + "="*70)
        print("📊 CURRENT TRUST PROFILES")
        print("="*70)
        
        summaries = self.trust_manager.get_all_users_summary()
        
        if not summaries:
            print("No trust profiles found")
            return
        
        for summary in summaries:
            print(f"\n👤 {summary['name']} ({summary['user_id']})")
            print(f"   📈 Trust Level: {summary['current_trust_level']}")
            print(f"   📊 Trust Score: {summary['current_trust_score']:.3f}")
            print(f"   🔢 Interactions: {summary['total_interactions']}")
            print(f"   ✅ Success Rate: {summary['success_rate']:.1%}")
            print(f"   🕐 Last Seen: {summary['last_seen']}")
            print(f"   ⏱️  Days Since: {summary['days_since_last_interaction']:.1f}")
    
    def test_access_control(self, user_id: str, required_trust_level: TrustLevel):
        """Test access control with different trust levels"""
        current_trust = self.trust_manager.get_current_trust_level(user_id)
        access_granted = self.trust_manager.should_grant_access(user_id, required_trust_level)
        
        print(f"\n🔐 ACCESS CONTROL TEST")
        print(f"   Required: {required_trust_level.name}")
        print(f"   Current:  {current_trust.name}")
        print(f"   Result:   {'✅ GRANTED' if access_granted else '❌ DENIED'}")
        
        return access_granted
    
    def simulate_recognition_scenarios(self):
        """Simulate different recognition scenarios to build trust history"""
        print("\n🎭 Simulating Recognition Scenarios...")
        
        # Get a user to work with
        users = self.user_database.list_users()
        if not users:
            print("❌ No users found in database")
            return
        
        user = users[0]
        user_id = user['user_id']
        user_name = user['name']
        
        print(f"Testing with user: {user_name}")
        
        # Scenario 1: High confidence recognitions (build trust)
        print("\n📈 Scenario 1: High Confidence Recognitions")
        high_confidences = [0.92, 0.89, 0.94, 0.87, 0.91]
        for i, confidence in enumerate(high_confidences, 1):
            trust_level = self.trust_manager.record_recognition_event(
                user_id, confidence, f"High confidence test {i}"
            )
            print(f"   Recognition {i}: confidence={confidence:.3f} → {trust_level.name}")
            time.sleep(0.1)  # Small delay for realistic timing
        
        # Test access at different levels
        print("\n🔓 Access Control After High Confidence:")
        for level in [TrustLevel.MEDIUM, TrustLevel.HIGH, TrustLevel.MAXIMUM]:
            self.test_access_control(user_id, level)
        
        # Scenario 2: Variable confidence (realistic scenario)
        print("\n📊 Scenario 2: Variable Confidence Recognition")
        variable_confidences = [0.75, 0.68, 0.82, 0.71, 0.79, 0.66]
        for i, confidence in enumerate(variable_confidences, 1):
            trust_level = self.trust_manager.record_recognition_event(
                user_id, confidence, f"Variable confidence test {i}"
            )
            print(f"   Recognition {i}: confidence={confidence:.3f} → {trust_level.name}")
            time.sleep(0.1)
        
        # Test access again
        print("\n🔓 Access Control After Variable Confidence:")
        for level in [TrustLevel.MEDIUM, TrustLevel.HIGH, TrustLevel.MAXIMUM]:
            self.test_access_control(user_id, level)
        
        # Scenario 3: Low confidence recognitions (trust degradation)
        print("\n📉 Scenario 3: Low Confidence Recognition")
        low_confidences = [0.58, 0.54, 0.61, 0.52]
        for i, confidence in enumerate(low_confidences, 1):
            trust_level = self.trust_manager.record_recognition_event(
                user_id, confidence, f"Low confidence test {i}"
            )
            print(f"   Recognition {i}: confidence={confidence:.3f} → {trust_level.name}")
            time.sleep(0.1)
        
        # Final access test
        print("\n🔓 Final Access Control After Low Confidence:")
        for level in [TrustLevel.MEDIUM, TrustLevel.HIGH, TrustLevel.MAXIMUM]:
            self.test_access_control(user_id, level)
    
    def real_time_trust_demo(self):
        """Real-time trust evaluation demo using camera"""
        print("\n📹 Starting Real-Time Trust Evaluation Demo")
        print("Press 'q' to quit, 's' to switch trust requirement level")
        
        self.camera_handler.start_capture()
        current_requirement = self.test_scenarios[self.current_scenario]
        
        try:
            while True:
                frame = self.camera_handler.get_current_frame()
                if frame is None:
                    continue
                
                # Create display frame
                display_frame = frame.copy()
                
                # Detect and recognize faces
                try:
                    detected_faces = self.face_recognizer.face_detector.detect_faces(frame)
                    
                    for detected_face in detected_faces:
                        # Generate encoding
                        face_encoding = self.face_recognizer.generate_face_encoding(
                            frame, detected_face.location
                        )
                        
                        if face_encoding is not None:
                            # Recognize face with current trust requirement
                            user_info, confidence = self.face_recognizer.recognize_face(
                                face_encoding, current_requirement
                            )
                            
                            # Draw bounding box
                            top, right, bottom, left = detected_face.location
                            
                            if user_info:
                                # Known user - color based on access granted
                                trust_level = user_info.get('trust_level')
                                access_granted = user_info.get('access_granted', False)
                                trust_score = user_info.get('trust_score', 0.0)
                                
                                # Color coding: Green = access granted, Red = access denied
                                color = (0, 255, 0) if access_granted else (0, 0, 255)
                                
                                # Draw rectangle and labels
                                cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                                
                                # User info
                                user_name = user_info.get('name', 'Unknown')
                                label = f"{user_name}"
                                cv2.putText(display_frame, label, (left, top-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                                
                                # Trust info
                                trust_text = f"Trust: {trust_level.name if trust_level else 'N/A'} ({trust_score:.2f})"
                                cv2.putText(display_frame, trust_text, (left, bottom+20), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                                
                                # Access status
                                access_text = "ACCESS GRANTED" if access_granted else "ACCESS DENIED"
                                cv2.putText(display_frame, access_text, (left, bottom+40), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                                
                                # Confidence
                                conf_text = f"Conf: {confidence:.3f}"
                                cv2.putText(display_frame, conf_text, (left, bottom+60), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                                
                            else:
                                # Unknown user
                                color = (0, 165, 255)  # Orange for unknown
                                cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                                cv2.putText(display_frame, "UNKNOWN", (left, top-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                                cv2.putText(display_frame, f"Conf: {confidence:.3f}", (left, bottom+20), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                except Exception as e:
                    print(f"Recognition error: {e}")
                
                # Add demo info overlay
                cv2.putText(display_frame, f"Trust Requirement: {current_requirement.name}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(display_frame, "Press 's' to switch requirement, 'q' to quit", 
                          (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Display frame
                cv2.imshow('Trust Management Demo', display_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Switch to next trust requirement level
                    self.current_scenario = (self.current_scenario + 1) % len(self.test_scenarios)
                    current_requirement = self.test_scenarios[self.current_scenario]
                    print(f"🔄 Switched to trust requirement: {current_requirement.name}")
        
        finally:
            self.camera_handler.stop_capture()
            cv2.destroyAllWindows()
    
    def run_demo(self):
        """Run the complete trust management demo"""
        print("\n🚀 Starting Trust Management System Demo")
        print("="*70)
        
        # Initial trust summary
        self.display_trust_summary()
        
        # Simulate recognition scenarios
        self.simulate_recognition_scenarios()
        
        # Updated trust summary
        print("\n📊 UPDATED TRUST PROFILES AFTER TESTING")
        self.display_trust_summary()
        
        # Ask user if they want to run real-time demo
        print("\n🎯 Demo Options:")
        print("1. Run real-time camera trust evaluation")
        print("2. Exit demo")
        
        choice = input("\nEnter your choice (1-2): ").strip()
        
        if choice == "1":
            try:
                self.real_time_trust_demo()
            except KeyboardInterrupt:
                print("\n⏹️  Real-time demo stopped by user")
        
        print("\n✅ Trust Management Demo completed!")
        print("📈 Trust profiles have been updated with demonstration data")

def main():
    """Main demo function"""
    demo = TrustManagementDemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        print("\n🏁 Trust Management Demo finished")

if __name__ == "__main__":
    main()