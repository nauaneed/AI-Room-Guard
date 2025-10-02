"""
Recognition Response System Demo

This demo showcases the comprehensive response system for face recognition events,
including welcome messages, alerts, logging, and escalation triggers.
"""

import cv2
import time
import sys
import os
import threading
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.vision.face_recognizer import FaceRecognizer
from src.core.response_system import ResponseSystem, ResponseType, AlertLevel
from src.core.trust_manager import TrustLevel
from src.video.camera_handler import CameraHandler
from src.vision.face_detector import FaceDetector

class ResponseSystemDemo:
    """Demo class for recognition response system"""
    
    def __init__(self):
        print("🔧 Initializing Recognition Response System Demo...")
        
        # Initialize components
        self.face_recognizer = FaceRecognizer()
        self.response_system = self.face_recognizer.response_system
        self.camera_handler = CameraHandler()
        self.face_detector = FaceDetector()
        
        # Demo state
        self.demo_running = False
        self.current_trust_requirement = TrustLevel.MEDIUM
        
        # Register custom response handlers
        self._register_custom_handlers()
        
        print("✅ Recognition Response System Demo initialized!")
    
    def _register_custom_handlers(self):
        """Register custom response handlers for demo"""
        
        def welcome_handler(event):
            if event.event_type == ResponseType.ACCESS_GRANTED:
                print(f"🎉 WELCOME HANDLER: {event.user_name} has been welcomed!")
        
        def alert_handler(event):
            if event.alert_level.value >= AlertLevel.HIGH.value:
                print(f"🚨 ALERT HANDLER: High-level alert triggered!")
                print(f"   Event: {event.event_type.value}")
                print(f"   Message: {event.message}")
        
        def security_handler(event):
            if event.event_type == ResponseType.UNKNOWN_PERSON:
                print(f"🛡️ SECURITY HANDLER: Unknown person detection logged")
        
        # Register handlers
        self.response_system.register_response_handler(ResponseType.ACCESS_GRANTED, welcome_handler)
        self.response_system.register_response_handler(ResponseType.UNKNOWN_PERSON, alert_handler)
        self.response_system.register_response_handler(ResponseType.UNKNOWN_PERSON, security_handler)
        
        print("📝 Custom response handlers registered")
    
    def run_simulated_demo(self):
        """Run simulated recognition scenarios"""
        print("\n🎭 Running Simulated Recognition Response Demo")
        print("=" * 70)
        
        scenarios = [
            {
                'name': 'High Trust User Access',
                'user_id': 'user_ddded5e2',
                'user_name': 'Navaneet',
                'confidence': 0.92,
                'trust_requirement': TrustLevel.HIGH
            },
            {
                'name': 'Medium Trust User Access', 
                'user_id': 'user_ddded5e2',
                'user_name': 'Navaneet',
                'confidence': 0.68,
                'trust_requirement': TrustLevel.HIGH
            },
            {
                'name': 'Low Confidence Recognition',
                'user_id': 'user_ddded5e2', 
                'user_name': 'Navaneet',
                'confidence': 0.55,
                'trust_requirement': TrustLevel.MEDIUM
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            print("-" * 50)
            
            # Simulate face recognition
            user_info = {
                'user_id': scenario['user_id'],
                'name': scenario['user_name']
            }
            
            # This will trigger the response system
            result = self.face_recognizer.recognize_face(
                unknown_encoding=None,  # We'll mock this in a real scenario
                required_trust_level=scenario['trust_requirement']
            )
            
            time.sleep(1)  # Allow processing
        
        # Simulate unknown person detections
        print(f"\n📋 Scenario 4: Unknown Person Detection Escalation")
        print("-" * 50)
        
        for i in range(5):
            confidence = 0.3 + (i * 0.05)
            response_event = self.response_system.generate_unknown_person_response(confidence)
            self.response_system.process_recognition_event(response_event)
            time.sleep(0.2)
        
        time.sleep(2)  # Allow processing
        
        # Show event statistics
        print("\n📊 Event Statistics")
        print("=" * 50)
        self.response_system.print_event_summary(hours=1)
    
    def run_real_time_demo(self):
        """Run real-time camera-based demo"""
        print("\n📹 Starting Real-Time Recognition Response Demo")
        print("Controls:")
        print("  'q' - Quit demo")
        print("  's' - Switch trust requirement level")
        print("  'r' - Show recent events")
        print("  'c' - Clear event history")
        
        try:
            # Start camera
            if not self.camera_handler.start_capture():
                print("❌ Failed to start camera")
                return
            
            self.demo_running = True
            
            # Display window
            cv2.namedWindow('Recognition Response Demo', cv2.WINDOW_NORMAL)
            
            while self.demo_running:
                frame = self.camera_handler.get_current_frame()
                
                if frame is not None:
                    # Create display frame
                    display_frame = frame.copy()
                    
                    # Add info overlay
                    self._add_info_overlay(display_frame)
                    
                    # Detect faces
                    detected_faces = self.face_detector.detect_faces(frame)
                    
                    # Process each face
                    for detected_face in detected_faces:
                        # Draw bounding box
                        top, right, bottom, left = detected_face.location
                        cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        
                        # Generate face encoding
                        face_encoding = self.face_recognizer.generate_face_encoding(frame, detected_face.location)
                        
                        if face_encoding is not None:
                            # Recognize face (this will trigger response system)
                            user_info, confidence = self.face_recognizer.recognize_face(
                                face_encoding, self.current_trust_requirement
                            )
                            
                            # Add recognition info to display
                            if user_info:
                                label = f"{user_info['name']} ({confidence:.2f})"
                                access = "✓" if user_info.get('access_granted', False) else "✗"
                                label += f" {access}"
                                color = (0, 255, 0) if user_info.get('access_granted', False) else (0, 165, 255)
                            else:
                                label = f"Unknown ({confidence:.2f})"
                                color = (0, 0, 255)
                            
                            cv2.putText(display_frame, label, (left, top - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    cv2.imshow('Recognition Response Demo', display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self._switch_trust_level()
                elif key == ord('r'):
                    self._show_recent_events()
                elif key == ord('c'):
                    self._clear_event_history()
                
                time.sleep(0.1)  # Control frame rate
        
        except Exception as e:
            print(f"❌ Demo error: {e}")
        
        finally:
            # Cleanup
            self.demo_running = False
            cv2.destroyAllWindows()
            self.camera_handler.stop_capture()
    
    def _add_info_overlay(self, frame):
        """Add information overlay to frame"""
        height, width = frame.shape[:2]
        
        # Add background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width - 10, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Add text information
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Recognition Response System Demo", (20, 35), font, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Trust Requirement: {self.current_trust_requirement.name}", (20, 60), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", (20, 80), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Press 's' to switch trust level, 'r' for events, 'q' to quit", (20, 100), font, 0.4, (255, 255, 255), 1)
    
    def _switch_trust_level(self):
        """Switch trust requirement level"""
        levels = [TrustLevel.LOW, TrustLevel.MEDIUM, TrustLevel.HIGH, TrustLevel.MAXIMUM]
        current_index = levels.index(self.current_trust_requirement)
        next_index = (current_index + 1) % len(levels)
        self.current_trust_requirement = levels[next_index]
        print(f"🔄 Switched trust requirement to: {self.current_trust_requirement.name}")
    
    def _show_recent_events(self):
        """Show recent recognition events"""
        print("\n📋 Recent Recognition Events:")
        recent_events = self.response_system.get_recent_events(hours=1)
        
        if not recent_events:
            print("  No recent events")
            return
        
        for event in recent_events[-10:]:  # Show last 10 events
            timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
            print(f"  [{timestamp}] {event.event_type.value}: {event.message}")
    
    def _clear_event_history(self):
        """Clear event history"""
        self.response_system.event_history.clear()
        self.response_system.save_event_history()
        print("🗑️ Event history cleared")

def main():
    """Main demo function"""
    demo = ResponseSystemDemo()
    
    print("\n🚀 Recognition Response System Demo")
    print("=" * 60)
    print("This demo showcases the recognition response system with:")
    print("  ✅ Welcome messages for trusted users")
    print("  🚨 Alert system for unknown users")
    print("  📊 Event logging and statistics")
    print("  🔄 Escalation triggers")
    print("  🎯 Custom response handlers")
    
    while True:
        print("\n🎯 Demo Options:")
        print("1. Run simulated recognition scenarios")
        print("2. Run real-time camera demo")
        print("3. Show event statistics")
        print("4. Exit demo")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                demo.run_simulated_demo()
            elif choice == '2':
                demo.run_real_time_demo()
            elif choice == '3':
                demo.response_system.print_event_summary()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
        
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🏁 Recognition Response System Demo finished")

if __name__ == "__main__":
    main()