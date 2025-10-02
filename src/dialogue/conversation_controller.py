"""
Conversation Controller Module
Manages complete conversation flow with audio input/output
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from .escalation_manager import escalation_manager
from .response_generator import response_generator
import sys
import os

# Add audio module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from audio import tts_manager

class ConversationController:
    """Controls the complete conversation flow with escalation"""
    
    def __init__(self):
        """Initialize conversation controller"""
        self.escalation = escalation_manager
        self.response_gen = response_generator  
        self.tts = tts_manager
        
        # Conversation state
        self.is_conversation_active = False
        self.current_person_id = None
        self.conversation_thread = None
        self.stop_conversation = False
        
        # Speech coordination
        self.speech_lock = threading.Lock()  # Prevent overlapping speech
        self.is_speaking = False
        
        # Timing settings
        self.response_delay = 2.0  # Delay between response generation and speech
        self.escalation_check_interval = 1.0  # How often to check for auto-escalation (faster)
        self.max_silence_time = 15.0  # Max silence before auto-escalation (15 seconds)
        self.waiting_for_response = False  # Flag to track if we're waiting for person response
        self.last_response_time = None  # When we last spoke and started waiting
        
        # Callbacks for events
        self.on_conversation_start: Optional[Callable] = None
        self.on_response_generated: Optional[Callable] = None
        self.on_response_spoken: Optional[Callable] = None
        self.on_escalation: Optional[Callable] = None
        self.on_conversation_end: Optional[Callable] = None
        
        print("✅ Conversation controller initialized")
    
    def start_conversation(self, 
                          person_id: str = "unknown_person",
                          initial_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start a new conversation with escalation
        
        Args:
            person_id: Identifier for the person
            initial_context: Initial context for the conversation
            
        Returns:
            True if conversation started successfully
        """
        if self.is_conversation_active:
            print("⚠️  Conversation already active")
            return False
        
        try:
            # Initialize systems
            self.current_person_id = person_id
            self.is_conversation_active = True
            self.stop_conversation = False
            
            # Start escalation manager
            self.escalation.start_conversation(person_id)
            
            # Clear previous conversation memory
            self.response_gen.clear_memory()
            
            print(f"🎤 Starting conversation with {person_id}")
            
            # Trigger callback
            if self.on_conversation_start:
                self.on_conversation_start(person_id, initial_context)
            
            # Start conversation in separate thread
            self.conversation_thread = threading.Thread(
                target=self._conversation_loop,
                args=(initial_context,),
                daemon=True
            )
            self.conversation_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start conversation: {e}")
            self.is_conversation_active = False
            return False
    
    def _conversation_loop(self, initial_context: Optional[Dict[str, Any]] = None):
        """Main conversation loop running in separate thread"""
        
        try:
            # Generate and speak initial response
            self._generate_and_speak_response(initial_context)
            
            # Start waiting for response after initial message
            self.waiting_for_response = True
            self.last_response_time = time.time()
            
            # Main conversation loop
            while self.is_conversation_active and not self.stop_conversation:
                
                # Only check for escalation if we're not currently speaking
                with self.speech_lock:
                    currently_speaking = self.is_speaking
                
                if not currently_speaking and self.waiting_for_response:
                    # Check if we should auto-escalate due to no response
                    current_time = time.time()
                    time_since_last_response = current_time - self.last_response_time
                    
                    if time_since_last_response >= self.max_silence_time:
                        print(f"⏰ No response for {self.max_silence_time} seconds - auto-escalating")
                        self._handle_auto_escalation()
                    
                    # Check if conversation has expired
                    if self.escalation.is_conversation_expired():
                        print("⏰ Conversation expired due to timeout")
                        self.end_conversation("timeout")
                        break
                
                # Sleep before next check
                time.sleep(self.escalation_check_interval)
            
        except Exception as e:
            print(f"❌ Error in conversation loop: {e}")
            self.end_conversation("error")
    
    def _generate_and_speak_response(self, context: Optional[Dict[str, Any]] = None):
        """Generate response and speak it"""
        
        # Use lock to prevent overlapping speech
        with self.speech_lock:
            if self.is_speaking:
                print("🔇 Already speaking, skipping duplicate response")
                return
            
            self.is_speaking = True
            
        try:
            print("🤖 Generating response...")
            
            # Stop any ongoing audio before generating new response
            if self.tts.is_available() and self.tts.is_playing():
                print("🔇 Stopping previous audio before new response")
                self.tts.stop_audio()
                time.sleep(0.2)  # Give it time to stop
            
            # Generate response based on current escalation context
            response = self.response_gen.generate_response(context)
            
            if not response:
                print("❌ Failed to generate response")
                return
            
            print(f"💬 Generated: '{response}'")
            
            # Trigger callback
            if self.on_response_generated:
                self.on_response_generated(response, self.escalation.get_current_level().value)
            
            # Add delay before speaking (more natural)
            time.sleep(self.response_delay)
            
            # Check if conversation is still active
            if not self.is_conversation_active:
                return
            
            # Speak the response
            print("🔊 Speaking response...")
            
            if self.tts.is_available():
                success = self.tts.speak_text(response, wait_for_completion=True)
                
                if success:
                    print("✅ Response spoken successfully")
                    
                    # Start waiting for person response after we finish speaking
                    self.waiting_for_response = True
                    self.last_response_time = time.time()
                    print(f"⏳ Waiting for person response (15 second timeout)...")
                    
                    # Trigger callback
                    if self.on_response_spoken:
                        self.on_response_spoken(response)
                else:
                    print("❌ Failed to speak response")
            else:
                print("⚠️  TTS not available, response generated but not spoken")
                # Simulate speaking time
                estimated_speech_time = len(response.split()) * 0.6  # ~0.6s per word
                time.sleep(estimated_speech_time)
                
        except Exception as e:
            print(f"❌ Error generating/speaking response: {e}")
        finally:
            # Always release the speaking flag
            with self.speech_lock:
                self.is_speaking = False
    
    def _handle_auto_escalation(self):
        """Handle automatic escalation"""
        
        print("⬆️  Auto-escalation triggered")
        
        # Check if we're currently speaking - if so, delay escalation
        with self.speech_lock:
            if self.is_speaking:
                print("🔇 Delaying auto-escalation - currently speaking")
                return
        
        # Escalate
        escalated = self.escalation.escalate()
        
        if escalated:
            current_level = self.escalation.get_current_level().value
            print(f"📈 Escalated to level {current_level}")
            
            # Trigger callback
            if self.on_escalation:
                self.on_escalation(current_level, "auto")
            
            # Generate and speak escalated response
            escalation_context = {
                'escalation_reason': 'timeout',
                'auto_escalation': True
            }
            
            self._generate_and_speak_response(escalation_context)
            
            # Reset waiting timer for new level
            self.waiting_for_response = True
            self.last_response_time = time.time()
            
        else:
            print("⚠️  Cannot escalate further - at maximum level")
            
            # If at max level for too long, end conversation
            timing = self.escalation.get_timing_info()
            if timing.get('time_at_current_level', 0) > 30:  # 30 seconds at max level
                print("🏁 Ending conversation - maximum escalation time reached")
                self.end_conversation("max_escalation_timeout")
    
    def process_person_response(self, response_text: str) -> Dict[str, Any]:
        """
        Process a response from the person and take appropriate action
        
        Args:
            response_text: What the person said
            
        Returns:
            Analysis and action taken
        """
        if not self.is_conversation_active:
            return {'error': 'Conversation not active'}
        
        print(f"👤 Person responded: '{response_text}'")
        
        # Stop waiting for response - we got one!
        self.waiting_for_response = False
        response_time = time.time()
        time_to_respond = response_time - self.last_response_time if self.last_response_time else 0
        print(f"⏱️  Person responded in {time_to_respond:.1f} seconds")
        
        # Check if we're currently speaking
        with self.speech_lock:
            currently_speaking = self.is_speaking
        
        if currently_speaking:
            print("🔇 System currently speaking, will process response after speech completes")
            
            # Wait for speech to complete before processing response
            max_wait = 10  # Maximum 10 seconds
            wait_start = time.time()
            
            while self.tts.is_playing() and (time.time() - wait_start) < max_wait:
                time.sleep(0.1)
            
            print("✅ Speech completed, now processing person response")
        
        # Analyze the response
        analysis = self.escalation.process_response(response_text)
        
        print(f"📊 Response analysis: {analysis['recommended_action']} ({analysis['reason']})")
        
        # Take action based on analysis
        if analysis['recommended_action'] == 'end_conversation':
            # Person indicated they are leaving - end conversation politely
            print(f"✅ Person indicated they are leaving: '{response_text}'")
            self.end_conversation("person_leaving")
            
        elif analysis['recommended_action'] == 'escalate':
            # Manual escalation due to uncooperative response
            escalated = self.escalation.escalate()
            
            if escalated:
                current_level = self.escalation.get_current_level().value
                print(f"📈 Escalated to level {current_level} due to uncooperative response")
                
                # Trigger callback
                if self.on_escalation:
                    self.on_escalation(current_level, "uncooperative")
                
                # Generate escalated response
                escalation_context = {
                    'escalation_reason': 'uncooperative',
                    'person_response': response_text
                }
                
                self._generate_and_speak_response(escalation_context)
                
        elif analysis['recommended_action'] == 'request_clarification':
            # Ask for clarification
            print(f"❓ Requesting clarification from person")
            clarification_context = {
                'request_clarification': True,
                'unclear_response': response_text
            }
            
            self._generate_and_speak_response(clarification_context)
            
        elif analysis['recommended_action'] == 'continue_conversation':
            # Continue with current level - person seems cooperative
            print(f"✅ Person being cooperative, continuing conversation at current level")
            continue_context = {
                'cooperative_response': True,
                'person_response': response_text
            }
            
            self._generate_and_speak_response(continue_context)
        
        return analysis
    
    def manual_escalate(self, reason: str = "manual") -> bool:
        """Manually escalate the conversation"""
        
        if not self.is_conversation_active:
            print("⚠️  No active conversation to escalate")
            return False
        
        escalated = self.escalation.escalate()
        
        if escalated:
            current_level = self.escalation.get_current_level().value
            print(f"📈 Manually escalated to level {current_level}")
            
            # Trigger callback
            if self.on_escalation:
                self.on_escalation(current_level, reason)
            
            # Generate escalated response
            escalation_context = {
                'escalation_reason': reason,
                'manual_escalation': True
            }
            
            self._generate_and_speak_response(escalation_context)
            
            return True
        else:
            print("⚠️  Cannot escalate - already at maximum level")
            return False
    
    def end_conversation(self, reason: str = "manual") -> Dict[str, Any]:
        """End the current conversation"""
        
        if not self.is_conversation_active:
            return {'error': 'No active conversation'}
        
        print(f"🏁 Ending conversation (reason: {reason})")
        
        # Wait for any ongoing speech to complete before ending
        if self.tts.is_available():
            with self.speech_lock:
                if self.is_speaking:
                    print("⏳ Waiting for current speech to complete before ending conversation...")
            
            # Wait for speech to finish
            max_wait_time = 10  # Maximum 10 seconds to wait
            wait_start = time.time()
            
            while self.tts.is_playing() and (time.time() - wait_start) < max_wait_time:
                time.sleep(0.1)
            
            # Only force stop if we've waited too long
            if self.tts.is_playing():
                print("⚠️  Force stopping audio due to timeout")
                self.tts.force_stop_audio()
            else:
                print("✅ Speech completed naturally before conversation end")
        
        # Stop conversation loop
        self.stop_conversation = True
        self.is_conversation_active = False
        
        # Get conversation summary
        escalation_summary = self.escalation.end_conversation(reason)
        conversation_summary = self.response_gen.get_conversation_summary()
        
        # Combine summaries
        summary = {
            'person_id': self.current_person_id,
            'end_reason': reason,
            'escalation_summary': escalation_summary,
            'conversation_summary': conversation_summary,
            'timestamp': time.time()
        }
        
        # Trigger callback
        if self.on_conversation_end:
            self.on_conversation_end(summary)
        
        # Clean up
        self.current_person_id = None
        self.conversation_thread = None
        
        # Reset speaking flag
        with self.speech_lock:
            self.is_speaking = False
        
        print("✅ Conversation ended successfully")
        
        return summary
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status"""
        
        if not self.is_conversation_active:
            return {'active': False}
        
        escalation_context = self.escalation.get_escalation_context()
        timing = self.escalation.get_timing_info()
        
        return {
            'active': True,
            'person_id': self.current_person_id,
            'current_level': escalation_context.get('current_level', 1),
            'escalation_count': escalation_context.get('escalation_count', 0),
            'conversation_duration': escalation_context.get('conversation_duration', 0),
            'time_at_current_level': timing.get('time_at_current_level', 0),
            'time_until_next_escalation': timing.get('time_until_next_escalation', 0),
            'tts_available': self.tts.is_available(),
            'audio_playing': self.tts.is_playing() if self.tts.is_available() else False
        }
    
    def is_active(self) -> bool:
        """Check if conversation is currently active"""
        return self.is_conversation_active
    
    def set_callbacks(self, **callbacks):
        """Set event callbacks"""
        for event, callback in callbacks.items():
            if hasattr(self, f'on_{event}'):
                setattr(self, f'on_{event}', callback)
                print(f"✅ Callback set for event: {event}")
            else:
                print(f"⚠️  Unknown callback event: {event}")


# Global conversation controller instance
conversation_controller = ConversationController()