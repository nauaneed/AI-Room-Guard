"""
Smart logging utility for the AI Guard Agent.
Provides event-based logging to reduce spam and only log meaningful changes.
"""

import logging
import time
from typing import Dict, Set, Optional
from config.settings import SystemConfig

class SmartLogger:
    """Smart logger that suppresses repetitive messages and only logs events"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
        
        # Track last logged messages to prevent spam
        self.last_messages: Dict[str, float] = {}
        self.message_counts: Dict[str, int] = {}
        self.suppressed_counts: Dict[str, int] = {}
        
        # Track state for event-based logging
        self.last_state = None
        self.last_face_count = 0
        self.last_recognized_user = None
        self.last_trust_score = {}
        
        # Minimum intervals between similar messages (seconds)
        self.min_intervals = {
            'guard_active': 60.0,      # "Guard mode is ACTIVE" every 60s max
            'waiting': 10.0,           # Waiting messages every 10s max
            'face_check': 5.0,         # Face recognition status every 5s max
            'audio_processing': 30.0,  # Audio loop status every 30s max
        }
    
    def should_log_event(self, event_type: str) -> bool:
        """Check if this event type should be logged based on configuration"""
        return SystemConfig.LOG_EVENTS.get(event_type, True)
    
    def should_log_message(self, message_key: str, message: str, force: bool = False) -> bool:
        """Determine if a message should be logged based on timing and content"""
        if force:
            return True
            
        current_time = time.time()
        
        # Check if this is a repetitive message
        if message_key in self.last_messages:
            time_since_last = current_time - self.last_messages[message_key]
            min_interval = self.min_intervals.get(message_key, 5.0)
            
            if time_since_last < min_interval:
                # Suppress this message
                self.suppressed_counts[message_key] = self.suppressed_counts.get(message_key, 0) + 1
                return False
        
        # Log this message
        self.last_messages[message_key] = current_time
        self.message_counts[message_key] = self.message_counts.get(message_key, 0) + 1
        
        # If we had suppressed messages, mention the count
        if message_key in self.suppressed_counts and self.suppressed_counts[message_key] > 0:
            suppressed = self.suppressed_counts[message_key]
            self.logger.debug(f"[Suppressed {suppressed} similar messages]")
            self.suppressed_counts[message_key] = 0
            
        return True
    
    def info_event(self, event_type: str, message: str, message_key: Optional[str] = None, force: bool = False):
        """Log an INFO message only if it's an actual event"""
        if not self.should_log_event(event_type):
            return
            
        if message_key and not self.should_log_message(message_key, message, force):
            return
            
        self.logger.info(message)
    
    def info_change(self, message: str, state_key: str, new_value, force: bool = False):
        """Log INFO only when a value actually changes"""
        if hasattr(self, f'last_{state_key}'):
            last_value = getattr(self, f'last_{state_key}')
            if last_value == new_value and not force:
                return  # No change, don't log
            setattr(self, f'last_{state_key}', new_value)
        else:
            setattr(self, f'last_{state_key}', new_value)
            
        self.logger.info(message)
    
    def state_change(self, old_state: str, new_state: str, reason: str = ""):
        """Log state changes (always logged as they're important)"""
        if self.should_log_event('state_changes'):
            reason_text = f" ({reason})" if reason else ""
            self.logger.info(f"🔄 State: {old_state} → {new_state}{reason_text}")
        self.last_state = new_state
    
    def face_detection_change(self, face_count: int, details: str = ""):
        """Log face detection changes (only when count changes)"""
        if self.should_log_event('face_detection'):
            if face_count != self.last_face_count:
                if face_count > 0:
                    self.logger.info(f"👁️  Faces detected: {face_count} {details}")
                else:
                    self.logger.info(f"👁️  No faces detected {details}")
                self.last_face_count = face_count
    
    def face_recognition_event(self, user_name: str, confidence: float, is_trusted: bool):
        """Log face recognition events (always important)"""
        if self.should_log_event('face_recognition'):
            if is_trusted:
                self.logger.info(f"✅ Trusted user: {user_name} (confidence: {confidence:.3f})")
            else:
                self.logger.info(f"⚠️  Unknown person (confidence: {confidence:.3f})")
    
    def audio_command_event(self, command: str, confidence: float):
        """Log audio command events (always important)"""
        if self.should_log_event('audio_commands'):
            self.logger.info(f"🎤 Command: '{command}' (confidence: {confidence:.2f})")
    
    def escalation_event(self, event: str, person_id: str = "", level: int = 1):
        """Log escalation events (always important)"""
        if self.should_log_event('escalation_events'):
            if event == "start":
                self.logger.info(f"🚨 Escalation started: {person_id} (Level {level})")
            elif event == "stop":
                self.logger.info(f"🛑 Escalation stopped: {person_id}")
            elif event == "escalate":
                self.logger.info(f"⬆️  Escalation level increased: {person_id} (Level {level})")
    
    def trust_change_event(self, user_id: str, old_score: float, new_score: float, reason: str = ""):
        """Log trust score changes (only when significant)"""
        if self.should_log_event('trust_changes'):
            score_diff = abs(new_score - old_score)
            if score_diff > 0.05:  # Only log if change > 5%
                direction = "↗️" if new_score > old_score else "↘️"
                self.logger.info(f"🔐 Trust {direction}: {user_id} {old_score:.3f} → {new_score:.3f} {reason}")
    
    def system_event(self, message: str):
        """Log system events (always important)"""
        if self.should_log_event('system_events'):
            self.logger.info(message)
    
    def periodic_status(self, message: str, message_key: str):
        """Log periodic status (only if enabled and not too frequent)"""
        if self.should_log_event('periodic_status'):
            self.info_event('periodic_status', message, message_key)
    
    def waiting_message(self, message: str, message_key: str):
        """Log waiting messages (only if enabled and not too frequent)"""
        if self.should_log_event('waiting_messages'):
            self.info_event('waiting_messages', message, message_key)
    
    # Delegate other logging methods to the underlying logger
    def info(self, message: str):
        """Standard info logging for backward compatibility"""
        self.logger.info(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)
    
    def get_stats(self) -> Dict:
        """Get logging statistics"""
        return {
            'total_messages': sum(self.message_counts.values()),
            'suppressed_messages': sum(self.suppressed_counts.values()),
            'message_types': len(self.message_counts),
            'active_suppressions': len([k for k, v in self.suppressed_counts.items() if v > 0])
        }

def get_smart_logger(name: str) -> SmartLogger:
    """Get a smart logger instance"""
    return SmartLogger(name)