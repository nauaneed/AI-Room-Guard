"""
Escalation Manager Module
Handles escalation logic and state management for security conversations
"""

import time
from typing import Dict, Any, Optional
from enum import Enum

class EscalationLevel(Enum):
    """Escalation levels for security conversations"""
    LEVEL_1 = 1  # Polite inquiry
    LEVEL_2 = 2  # Firm request
    LEVEL_3 = 3  # Strong warning
    LEVEL_4 = 4  # Alarm/Final warning

class EscalationManager:
    """Manages escalation state and progression logic"""
    
    def __init__(self):
        """Initialize escalation manager"""
        self.current_level = EscalationLevel.LEVEL_1
        self.escalation_start_time = None
        self.last_escalation_time = None
        self.escalation_count = 0
        self.conversation_active = False
        
        # Escalation timing settings (in seconds)
        self.level_durations = {
            EscalationLevel.LEVEL_1: 15,  # 15 seconds at level 1
            EscalationLevel.LEVEL_2: 20,  # 20 seconds at level 2
            EscalationLevel.LEVEL_3: 15,  # 15 seconds at level 3
            EscalationLevel.LEVEL_4: 30   # 30 seconds at level 4 before reset
        }
        
        # Escalation characteristics for each level
        self.level_characteristics = {
            EscalationLevel.LEVEL_1: {
                'tone': 'polite and curious',
                'description': 'Friendly identification request',
                'max_response_words': 20,
                'urgency': 'low',
                'example': 'Hello, I don\'t recognize you. Could you please identify yourself?'
            },
            EscalationLevel.LEVEL_2: {
                'tone': 'firm and authoritative',
                'description': 'Clear request to identify or leave',
                'max_response_words': 25,
                'urgency': 'medium',
                'example': 'Please state your business here or leave the premises immediately.'
            },
            EscalationLevel.LEVEL_3: {
                'tone': 'stern and warning',
                'description': 'Clear warning about trespassing',
                'max_response_words': 30,
                'urgency': 'high',
                'example': 'You are trespassing on private property. Leave now or security will be contacted.'
            },
            EscalationLevel.LEVEL_4: {
                'tone': 'urgent and alarming',
                'description': 'Final warning with security notification',
                'max_response_words': 35,
                'urgency': 'critical',
                'example': 'INTRUDER ALERT! You must leave immediately. Security has been notified!'
            }
        }
        
        # Response timeout settings
        self.response_timeout = 10  # Seconds to wait for response before escalating
        self.conversation_timeout = 120  # Total conversation timeout (2 minutes)
        
        print("✅ Escalation manager initialized")
    
    def start_conversation(self, person_id: Optional[str] = None) -> None:
        """Start a new escalation conversation"""
        current_time = time.time()
        
        self.conversation_active = True
        self.current_level = EscalationLevel.LEVEL_1
        self.escalation_start_time = current_time
        self.last_escalation_time = current_time
        self.escalation_count = 0
        
        print(f"🚨 Escalation conversation started (Person ID: {person_id or 'Unknown'})")
        print(f"   Starting at Level {self.current_level.value}")
    
    def should_escalate(self) -> bool:
        """Check if escalation should occur based on timing"""
        if not self.conversation_active:
            return False
        
        current_time = time.time()
        time_since_last_escalation = current_time - self.last_escalation_time
        
        # Check if we should escalate based on level duration
        current_duration = self.level_durations[self.current_level]
        
        return time_since_last_escalation >= current_duration
    
    def escalate(self) -> bool:
        """Escalate to next level if possible"""
        if not self.conversation_active:
            return False
        
        if self.current_level == EscalationLevel.LEVEL_4:
            print("⚠️  Already at maximum escalation level")
            return False
        
        # Move to next level
        next_level_value = self.current_level.value + 1
        self.current_level = EscalationLevel(next_level_value)
        self.last_escalation_time = time.time()
        self.escalation_count += 1
        
        print(f"⬆️  Escalated to Level {self.current_level.value}")
        return True
    
    def get_current_level(self) -> EscalationLevel:
        """Get current escalation level"""
        return self.current_level
    
    def get_level_info(self, level: Optional[EscalationLevel] = None) -> Dict[str, Any]:
        """Get information about a specific escalation level"""
        target_level = level or self.current_level
        return self.level_characteristics[target_level].copy()
    
    def get_escalation_context(self) -> Dict[str, Any]:
        """Get context information for response generation"""
        if not self.conversation_active:
            return {}
        
        current_time = time.time()
        conversation_duration = current_time - self.escalation_start_time
        time_at_current_level = current_time - self.last_escalation_time
        
        return {
            'current_level': self.current_level.value,
            'escalation_count': self.escalation_count,
            'conversation_duration': conversation_duration,
            'time_at_current_level': time_at_current_level,
            'level_info': self.get_level_info(),
            'should_escalate_soon': self.should_escalate(),
            'conversation_active': self.conversation_active
        }
    
    def is_conversation_expired(self) -> bool:
        """Check if conversation has exceeded timeout"""
        if not self.conversation_active:
            return False
        
        current_time = time.time()
        conversation_duration = current_time - self.escalation_start_time
        
        return conversation_duration >= self.conversation_timeout
    
    def end_conversation(self, reason: str = "manual") -> Dict[str, Any]:
        """End the escalation conversation"""
        if not self.conversation_active:
            return {}
        
        current_time = time.time()
        conversation_duration = current_time - self.escalation_start_time
        
        summary = {
            'reason': reason,
            'final_level': self.current_level.value,
            'total_escalations': self.escalation_count,
            'conversation_duration': conversation_duration,
            'max_level_reached': self.current_level == EscalationLevel.LEVEL_4
        }
        
        print(f"🏁 Escalation conversation ended ({reason})")
        print(f"   Final level: {self.current_level.value}")
        print(f"   Duration: {conversation_duration:.1f}s")
        print(f"   Total escalations: {self.escalation_count}")
        
        # Reset state
        self.conversation_active = False
        self.current_level = EscalationLevel.LEVEL_1
        self.escalation_start_time = None
        self.last_escalation_time = None
        self.escalation_count = 0
        
        return summary
    
    def process_response(self, response_text: str) -> Dict[str, Any]:
        """Process a response from the person and determine next action"""
        if not self.conversation_active:
            return {'action': 'none', 'reason': 'conversation not active'}
        
        response_text = response_text.strip().lower()
        
        # Enhanced response analysis
        positive_indicators = ['hello', 'hi', 'friend', 'roommate', 'invited', 'permission', 'live here', 
                              'guest', 'authorized', 'allowed', 'belong here', 'visiting']
        negative_indicators = ['no', 'none of your business', 'shut up', 'go away', 'leave me alone', 
                              'fuck', 'get lost', 'mind your own', 'screw you']
        identification_attempts = ['i am', 'my name is', 'i\'m', 'this is', 'name', 'called']
        cooperative_indicators = ['sorry', 'excuse me', 'understand', 'explain', 'here to', 'looking for']
        leaving_indicators = ['leaving', 'going', 'exit', 'sorry', 'mistake', 'wrong room']
        
        analysis = {
            'response_text': response_text,
            'has_positive_indicators': any(indicator in response_text for indicator in positive_indicators),
            'has_negative_indicators': any(indicator in response_text for indicator in negative_indicators),
            'attempts_identification': any(attempt in response_text for attempt in identification_attempts),
            'shows_cooperation': any(coop in response_text for coop in cooperative_indicators),
            'indicates_leaving': any(leave in response_text for leave in leaving_indicators),
            'response_length': len(response_text),
            'timestamp': time.time()
        }
        
        # Determine action based on response analysis
        if analysis['indicates_leaving']:
            # Person is leaving - end conversation
            action = 'end_conversation'
            reason = 'person indicated they are leaving'
        elif analysis['attempts_identification'] or analysis['has_positive_indicators']:
            # Person is trying to identify themselves or being cooperative
            action = 'continue_conversation'
            reason = 'cooperative response - person attempting identification'
        elif analysis['shows_cooperation']:
            # Person seems cooperative but may need clarification
            action = 'request_clarification'
            reason = 'cooperative but needs clarification'
        elif analysis['has_negative_indicators']:
            # Person is being uncooperative - escalate
            action = 'escalate'
            reason = 'uncooperative/hostile response'
        elif len(response_text) < 5:
            # Very short or unclear response - ask for clarification
            action = 'request_clarification'
            reason = 'response too short or unclear'
        else:
            # Neutral response - continue but may escalate based on level
            if self.current_level.value >= 3:
                # At higher levels, neutral responses aren't enough
                action = 'escalate'
                reason = 'insufficient response at high escalation level'
            else:
                action = 'continue_conversation'
                reason = 'neutral response accepted at current level'
        
        analysis['recommended_action'] = action
        analysis['reason'] = reason
        
        return analysis
    
    def get_timing_info(self) -> Dict[str, float]:
        """Get timing information for the current conversation"""
        if not self.conversation_active:
            return {}
        
        current_time = time.time()
        return {
            'conversation_duration': current_time - self.escalation_start_time,
            'time_at_current_level': current_time - self.last_escalation_time,
            'time_until_next_escalation': max(0, self.level_durations[self.current_level] - (current_time - self.last_escalation_time)),
            'conversation_timeout_remaining': max(0, self.conversation_timeout - (current_time - self.escalation_start_time))
        }
    
    def is_active(self) -> bool:
        """Check if conversation is currently active"""
        return self.conversation_active
    
    def reset(self) -> None:
        """Reset escalation manager to initial state"""
        self.end_conversation("reset")
        print("🔄 Escalation manager reset")


# Global escalation manager instance
escalation_manager = EscalationManager()