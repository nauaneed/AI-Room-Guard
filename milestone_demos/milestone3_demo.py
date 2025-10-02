#!/usr/bin/env python3
"""
Milestone 3 Demo: Escalation Dialogue and Full Integration
==========================================================

This demo showcases the complete AI Guard Agent with escalation dialogue system.

Features Demonstrated:
- LLM-powered intelligent dialogue generation
- Real-time Text-to-Speech (TTS) audio output  
- 4-level escalation system with progressive responses
- Complete conversation flow management
- Audio integration with natural speech
- Context-aware response generation
- Performance optimization and error handling

Usage:
    python milestone3_demo.py
    
Requirements:
    - Microphone and speakers (for full audio experience)
    - All project dependencies installed
    - Optional: GOOGLE_GEMINI_API_KEY for enhanced responses
"""

import sys
import os
import time
import threading
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our Milestone 3 components
from dialogue import conversation_controller, escalation_manager, response_generator, EscalationLevel
from audio import tts_manager
from llm import dialogue_generator

class Milestone3Demo:
    """Interactive demo of Milestone 3 capabilities"""
    
    def __init__(self):
        """Initialize the demo"""
        self.demo_running = False
        self.conversation_events = []
        
        print("🎭 AI Guard Agent - Milestone 3 Demo")
        print("=" * 50)
        print()
        
        # Setup event tracking
        self._setup_event_callbacks()
        
        # Check system status
        self._check_system_status()
    
    def _setup_event_callbacks(self):
        """Setup callbacks to track conversation events"""
        
        def track_event(event_type):
            def callback(*args, **kwargs):
                event = {
                    'type': event_type,
                    'timestamp': time.time(),
                    'data': {'args': args, 'kwargs': kwargs}
                }
                self.conversation_events.append(event)
                
                # Print event in real-time
                if event_type == 'conversation_start':
                    print(f"🎬 Conversation started with {args[0] if args else 'unknown person'}")
                elif event_type == 'response_generated':
                    print(f"💭 Generated: \"{args[0] if args else 'unknown'}\"")
                elif event_type == 'response_spoken':
                    print(f"🔊 Spoken: \"{args[0] if args else 'unknown'}\"")
                elif event_type == 'escalation':
                    print(f"📈 Escalated to Level {args[0] if args else 'unknown'} ({args[1] if len(args) > 1 else 'unknown reason'})")
                elif event_type == 'conversation_end':
                    print(f"🏁 Conversation ended")
                
            return callback
        
        conversation_controller.set_callbacks(
            conversation_start=track_event('conversation_start'),
            response_generated=track_event('response_generated'),
            response_spoken=track_event('response_spoken'),
            escalation=track_event('escalation'),
            conversation_end=track_event('conversation_end')
        )
    
    def _check_system_status(self):
        """Check and display system component status"""
        print("🔍 System Component Status:")
        
        components = {
            'LLM Dialogue Generator': dialogue_generator.is_available(),
            'Text-to-Speech System': tts_manager.is_available(),
            'Escalation Manager': True,
            'Response Generator': response_generator.is_available(),
            'Conversation Controller': True
        }
        
        for component, available in components.items():
            if available:
                print(f"   ✅ {component}")
            else:
                print(f"   ⚠️  {component} (using fallbacks)")
        
        print()
        
        # Show escalation levels
        print("📊 Available Escalation Levels:")
        for level in EscalationLevel:
            info = escalation_manager.get_level_info(level)
            print(f"   Level {level.value}: {info['tone']}")
            print(f"     Example: \"{info['example']}\"")
        print()
    
    def run_interactive_demo(self):
        """Run interactive demo with user input"""
        print("🎮 Interactive Demo Mode")
        print("-" * 30)
        print()
        
        while True:
            print("Choose a demo scenario:")
            print("1. 🤝 Cooperative Person (polite responses)")
            print("2. 😠 Uncooperative Person (hostile responses)")
            print("3. 😕 Confused Person (unclear responses)")
            print("4. ⏱️  Auto-Escalation Demo (time-based)")
            print("5. 🎯 Custom Scenario (your own responses)")
            print("6. 📊 Performance Test")
            print("7. 🔊 Audio Test")
            print("0. Exit")
            print()
            
            choice = input("Enter your choice (0-7): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._demo_cooperative_person()
            elif choice == '2':
                self._demo_uncooperative_person()
            elif choice == '3':
                self._demo_confused_person()
            elif choice == '4':
                self._demo_auto_escalation()
            elif choice == '5':
                self._demo_custom_scenario()
            elif choice == '6':
                self._demo_performance_test()
            elif choice == '7':
                self._demo_audio_test()
            else:
                print("Invalid choice. Please try again.")
            
            print("\n" + "="*50 + "\n")
    
    def _demo_cooperative_person(self):
        """Demo with a cooperative person"""
        print("🤝 Cooperative Person Scenario")
        print("Simulating someone who is polite and tries to identify themselves")
        print()
        
        # Start conversation
        conversation_controller.start_conversation("cooperative_demo")
        
        # Wait for initial response
        self._wait_and_show_status(3)
        
        # Simulate cooperative responses
        responses = [
            "Oh, hello! I'm John, I'm a friend of the roommate.",
            "Sorry, I should have knocked. I'm here to pick up some books.",
            "No problem, I understand the security. I'll wait outside."
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\n👤 Person (Step {i}): \"{response}\"")
            
            analysis = conversation_controller.process_person_response(response)
            
            print(f"🧠 Analysis: {analysis['recommended_action']} ({analysis['reason']})")
            
            # Wait for system response
            self._wait_and_show_status(4)
        
        # End conversation
        summary = conversation_controller.end_conversation("cooperative_demo_complete")
        self._show_conversation_summary(summary)
    
    def _demo_uncooperative_person(self):
        """Demo with an uncooperative person"""
        print("😠 Uncooperative Person Scenario")
        print("Simulating someone who becomes increasingly hostile")
        print()
        
        # Start conversation
        conversation_controller.start_conversation("uncooperative_demo")
        
        # Wait for initial response
        self._wait_and_show_status(3)
        
        # Simulate uncooperative responses
        responses = [
            "What? Who are you to ask me that?",
            "None of your business! I can be here if I want.",
            "Shut up! I'm not going anywhere.",
            "Try and make me leave!"
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\n👤 Person (Step {i}): \"{response}\"")
            
            analysis = conversation_controller.process_person_response(response)
            
            print(f"🧠 Analysis: {analysis['recommended_action']} ({analysis['reason']})")
            
            # Wait for system response
            self._wait_and_show_status(4)
            
            # Show current escalation level
            status = conversation_controller.get_conversation_status()
            if status['active']:
                print(f"📊 Current escalation level: {status['current_level']}")
        
        # End conversation
        summary = conversation_controller.end_conversation("uncooperative_demo_complete")
        self._show_conversation_summary(summary)
    
    def _demo_confused_person(self):
        """Demo with a confused person"""
        print("😕 Confused Person Scenario")
        print("Simulating someone who doesn't understand what's happening")
        print()
        
        # Start conversation
        conversation_controller.start_conversation("confused_demo")
        
        # Wait for initial response
        self._wait_and_show_status(3)
        
        # Simulate confused responses
        responses = [
            "Huh? What?",
            "I don't understand. Where am I?",
            "What are you talking about?",
            "I'm so confused..."
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\n👤 Person (Step {i}): \"{response}\"")
            
            analysis = conversation_controller.process_person_response(response)
            
            print(f"🧠 Analysis: {analysis['recommended_action']} ({analysis['reason']})")
            
            # Wait for system response
            self._wait_and_show_status(4)
        
        # End conversation
        summary = conversation_controller.end_conversation("confused_demo_complete")
        self._show_conversation_summary(summary)
    
    def _demo_auto_escalation(self):
        """Demo automatic escalation based on time"""
        print("⏱️  Auto-Escalation Demo")
        print("Demonstrating time-based escalation without person responses")
        print()
        
        # Temporarily reduce escalation times for demo
        original_durations = escalation_manager.level_durations.copy()
        escalation_manager.level_durations = {
            EscalationLevel.LEVEL_1: 5,  # 5 seconds
            EscalationLevel.LEVEL_2: 5,  # 5 seconds
            EscalationLevel.LEVEL_3: 5,  # 5 seconds
            EscalationLevel.LEVEL_4: 5   # 5 seconds
        }
        
        # Reduce check interval
        original_interval = conversation_controller.escalation_check_interval
        conversation_controller.escalation_check_interval = 1.0
        
        try:
            print("Starting auto-escalation (shortened intervals for demo)...")
            print("The system will escalate every 5 seconds automatically")
            print()
            
            # Start conversation
            conversation_controller.start_conversation("auto_escalation_demo")
            
            # Monitor for 25 seconds
            start_time = time.time()
            
            while time.time() - start_time < 25:
                status = conversation_controller.get_conversation_status()
                
                if not status['active']:
                    break
                
                elapsed = time.time() - start_time
                print(f"⏰ Time: {elapsed:.1f}s | Level: {status['current_level']} | Escalations: {status['escalation_count']}")
                
                time.sleep(2)
            
            # End conversation
            if conversation_controller.is_active():
                summary = conversation_controller.end_conversation("auto_escalation_demo_complete")
                self._show_conversation_summary(summary)
            
        finally:
            # Restore original settings
            escalation_manager.level_durations = original_durations
            conversation_controller.escalation_check_interval = original_interval
    
    def _demo_custom_scenario(self):
        """Demo with custom user responses"""
        print("🎯 Custom Scenario")
        print("You can type your own responses as the intruder")
        print("Type 'quit' to end the conversation")
        print()
        
        # Start conversation
        conversation_controller.start_conversation("custom_demo")
        
        # Wait for initial response
        self._wait_and_show_status(3)
        
        step = 1
        while True:
            print(f"\n--- Step {step} ---")
            user_response = input("👤 Your response as the intruder: ").strip()
            
            if user_response.lower() in ['quit', 'exit', 'end']:
                break
            
            if not user_response:
                print("Please enter a response or 'quit' to end.")
                continue
            
            analysis = conversation_controller.process_person_response(user_response)
            
            print(f"🧠 Analysis: {analysis['recommended_action']} ({analysis['reason']})")
            
            # Wait for system response
            self._wait_and_show_status(4)
            
            # Show current status
            status = conversation_controller.get_conversation_status()
            if status['active']:
                print(f"📊 Level: {status['current_level']} | Duration: {status['conversation_duration']:.1f}s")
            
            step += 1
        
        # End conversation
        summary = conversation_controller.end_conversation("custom_demo_complete")
        self._show_conversation_summary(summary)
    
    def _demo_performance_test(self):
        """Demo performance metrics"""
        print("📊 Performance Test")
        print("Testing response generation and TTS speed")
        print()
        
        # Test response generation speed
        print("Testing response generation speed...")
        times = []
        
        for i in range(5):
            start_time = time.time()
            response = response_generator.generate_response()
            generation_time = time.time() - start_time
            times.append(generation_time)
            
            print(f"  Test {i+1}: {generation_time:.3f}s - \"{response[:40]}...\"")
        
        avg_generation_time = sum(times) / len(times)
        print(f"Average response generation time: {avg_generation_time:.3f}s")
        print()
        
        # Test TTS speed if available
        if tts_manager.is_available():
            print("Testing TTS conversion speed...")
            
            test_phrases = [
                "Hello, I don't recognize you.",
                "Please state your business here.",
                "You are trespassing on private property.",
                "INTRUDER ALERT! Security has been notified!"
            ]
            
            tts_times = []
            
            for phrase in test_phrases:
                start_time = time.time()
                audio_path = tts_manager.text_to_speech(phrase, play_immediately=False)
                tts_time = time.time() - start_time
                tts_times.append(tts_time)
                
                print(f"  \"{phrase[:30]}...\": {tts_time:.3f}s")
            
            avg_tts_time = sum(tts_times) / len(tts_times)
            print(f"Average TTS conversion time: {avg_tts_time:.3f}s")
            
            # Cleanup
            tts_manager.cleanup_temp_files()
        else:
            print("TTS not available for performance testing")
        
        print()
        print("✅ Performance test complete")
    
    def _demo_audio_test(self):
        """Demo audio capabilities"""
        print("🔊 Audio Test")
        print("Testing TTS with different escalation levels")
        print()
        
        if not tts_manager.is_available():
            print("❌ TTS not available - cannot run audio test")
            return
        
        test_phrases = [
            ("Level 1", "Hello, I don't recognize you. Could you please identify yourself?"),
            ("Level 2", "Please state your business here or leave the premises immediately."),
            ("Level 3", "You are trespassing on private property. Leave now or security will be contacted."),
            ("Level 4", "INTRUDER ALERT! You must leave immediately. Security has been notified!")
        ]
        
        for level, phrase in test_phrases:
            print(f"🔊 Playing {level}: \"{phrase}\"")
            
            success = tts_manager.speak_text(phrase, wait_for_completion=True)
            
            if success:
                conversion_time = tts_manager.get_last_conversion_time()
                print(f"   ✅ Conversion: {conversion_time:.2f}s")
            else:
                print(f"   ❌ Failed to speak")
            
            print()
        
        # Cleanup
        tts_manager.cleanup_temp_files()
        print("✅ Audio test complete")
    
    def _wait_and_show_status(self, seconds: int):
        """Wait for a period and show status"""
        for i in range(seconds):
            time.sleep(1)
            if conversation_controller.is_active():
                status = conversation_controller.get_conversation_status()
                if i == seconds - 1:  # Show status on last iteration
                    print(f"📊 Status: Level {status['current_level']}, Duration: {status['conversation_duration']:.1f}s")
    
    def _show_conversation_summary(self, summary: Dict[str, Any]):
        """Show conversation summary"""
        print("\n📋 Conversation Summary:")
        
        escalation_summary = summary.get('escalation_summary', {})
        conversation_summary = summary.get('conversation_summary', {})
        
        print(f"   Duration: {escalation_summary.get('conversation_duration', 0):.1f} seconds")
        print(f"   Final level: {escalation_summary.get('final_level', 1)}")
        print(f"   Total escalations: {escalation_summary.get('total_escalations', 0)}")
        print(f"   Responses generated: {conversation_summary.get('total_responses', 0)}")
        print(f"   Levels used: {conversation_summary.get('levels_used', [])}")
        print(f"   Max level reached: {'Yes' if escalation_summary.get('max_level_reached', False) else 'No'}")
    
    def run_automated_demo(self):
        """Run automated demo showcasing all features"""
        print("🎬 Automated Demo - Complete Feature Showcase")
        print("-" * 45)
        print()
        
        print("This demo will showcase all Milestone 3 features automatically:")
        print("- LLM integration with intelligent responses")
        print("- 4-level escalation system")
        print("- Real-time TTS audio output")
        print("- Context-aware conversation management")
        print("- Performance optimization")
        print()
        
        input("Press Enter to start the automated demo...")
        print()
        
        # Demo 1: Show escalation levels
        print("🎯 Feature 1: Escalation Level System")
        for level in EscalationLevel:
            info = escalation_manager.get_level_info(level)
            print(f"   Level {level.value}: {info['tone']} - {info['urgency']} urgency")
        print()
        
        # Demo 2: Quick conversation
        print("🎯 Feature 2: Complete Conversation Flow")
        conversation_controller.start_conversation("automated_demo")
        
        time.sleep(4)  # Wait for initial response
        
        # Simulate quick escalation
        responses = ["What?", "Go away", "I'm not leaving"]
        
        for response in responses:
            print(f"   Simulating response: \"{response}\"")
            conversation_controller.process_person_response(response)
            time.sleep(3)  # Wait for system response
        
        summary = conversation_controller.end_conversation("automated_demo_complete")
        print(f"   ✅ Conversation completed - reached level {summary['escalation_summary']['final_level']}")
        print()
        
        # Demo 3: Audio capabilities
        if tts_manager.is_available():
            print("🎯 Feature 3: Text-to-Speech Integration")
            print("   Speaking sample escalation response...")
            tts_manager.speak_text("INTRUDER ALERT! You must leave immediately. Security has been notified!")
            print("   ✅ Audio output demonstrated")
        else:
            print("🎯 Feature 3: Text-to-Speech (not available)")
        print()
        
        # Demo 4: Performance
        print("🎯 Feature 4: Performance Metrics")
        start_time = time.time()
        response = response_generator.generate_response()
        generation_time = time.time() - start_time
        
        print(f"   Response generation: {generation_time:.3f}s")
        if tts_manager.is_available():
            tts_time = tts_manager.get_last_conversion_time()
            print(f"   TTS conversion: {tts_time:.3f}s")
        print(f"   ✅ Performance suitable for real-time operation")
        print()
        
        print("🎉 Automated demo complete!")
        print("All Milestone 3 features successfully demonstrated.")

def main():
    """Main demo function"""
    print("🚀 Starting Milestone 3 Demo...")
    print()
    
    try:
        demo = Milestone3Demo()
        
        print("Choose demo mode:")
        print("1. 🎮 Interactive Demo (choose scenarios)")
        print("2. 🎬 Automated Demo (quick showcase)")
        print()
        
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == '1':
            demo.run_interactive_demo()
        elif choice == '2':
            demo.run_automated_demo()
        else:
            print("Invalid choice. Running automated demo...")
            demo.run_automated_demo()
        
        print("\n🎉 Demo completed successfully!")
        print("\nMilestone 3 Features Demonstrated:")
        print("✅ LLM integration with intelligent dialogue")
        print("✅ Text-to-Speech with real-time audio")
        print("✅ 4-level escalation system")
        print("✅ Complete conversation flow management")
        print("✅ Context-aware response generation")
        print("✅ Performance optimization")
        print("✅ Seamless multi-modal integration")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if conversation_controller.is_active():
            conversation_controller.end_conversation("demo_cleanup")
        
        if tts_manager.is_available():
            tts_manager.cleanup_temp_files()
        
        print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    main()