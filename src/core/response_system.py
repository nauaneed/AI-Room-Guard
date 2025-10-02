"""
Recognition Response System

This module implements comprehensive response mechanisms for face recognition events,
including welcome messages for trusted users, alert systems for unknown users,
event logging, and escalation triggers.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
from src.utils.smart_logger import SmartLogger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = SmartLogger(__name__)

class ResponseType(Enum):
    """Types of recognition responses"""
    WELCOME = "welcome"
    ALERT = "alert"
    WARNING = "warning"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    UNKNOWN_PERSON = "unknown_person"
    TRUSTED_USER = "trusted_user"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

@dataclass
class RecognitionEvent:
    """Recognition event data structure"""
    timestamp: float
    event_type: ResponseType
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    confidence: float = 0.0
    trust_level: Optional[str] = None
    trust_score: float = 0.0
    access_granted: bool = False
    alert_level: AlertLevel = AlertLevel.INFO
    message: str = ""
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'confidence': self.confidence,
            'trust_level': self.trust_level,
            'trust_score': self.trust_score,
            'access_granted': self.access_granted,
            'alert_level': self.alert_level.value,
            'message': self.message,
            'context': self.context or {}
        }

class ResponseSystem:
    """
    Comprehensive recognition response system
    
    Features:
    - Welcome messages for trusted users
    - Alert system for unknown users
    - Event logging and persistence
    - Escalation triggers
    - Response customization
    - Real-time notifications
    """
    
    def __init__(self, log_file: str = "data/recognition_events.json"):
        self.log_file = log_file
        self.event_history: List[RecognitionEvent] = []
        self.response_handlers: Dict[ResponseType, List[Callable]] = {}
        self.alert_thresholds = {
            'unknown_person_count': 3,
            'unknown_person_timeframe': 300,  # 5 minutes
            'low_confidence_count': 5,
            'low_confidence_timeframe': 600,  # 10 minutes
            'access_denied_count': 3,
            'access_denied_timeframe': 180   # 3 minutes
        }
        
        # Response templates
        self.welcome_messages = [
            "Welcome back, {name}! Access granted.",
            "Hello {name}! Nice to see you again.",
            "Good {time_of_day}, {name}! Welcome.",
            "Hi {name}! Your access has been approved.",
            "Welcome, {name}! Hope you're having a great day!"
        ]
        
        self.alert_messages = {
            AlertLevel.INFO: "Information: {message}",
            AlertLevel.LOW: "Notice: {message}",
            AlertLevel.MEDIUM: "Warning: {message}",
            AlertLevel.HIGH: "ALERT: {message}",
            AlertLevel.CRITICAL: "CRITICAL ALERT: {message}"
        }
        
        # Load existing events
        self.load_event_history()
        
        # Response queue for async processing
        self.response_queue = queue.Queue()
        self.response_thread = threading.Thread(target=self._process_responses, daemon=True)
        self.response_thread.start()
        
        logger.info("Recognition Response System initialized")
    
    def load_event_history(self) -> None:
        """Load recognition events from file"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
                # Keep only recent events (last 30 days)
                cutoff_time = time.time() - (30 * 86400)
                recent_events = [event for event in data if event.get('timestamp', 0) >= cutoff_time]
                logger.info(f"Loaded {len(recent_events)} recent recognition events")
        except FileNotFoundError:
            logger.info("No existing event history found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading event history: {e}")
    
    def save_event_history(self) -> None:
        """Save recognition events to file"""
        try:
            # Create directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            # Convert events to dictionaries
            data = [event.to_dict() for event in self.event_history]
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.event_history)} recognition events")
        except Exception as e:
            logger.error(f"Error saving event history: {e}")
    
    def register_response_handler(self, response_type: ResponseType, handler: Callable) -> None:
        """Register a response handler for specific event types"""
        if response_type not in self.response_handlers:
            self.response_handlers[response_type] = []
        self.response_handlers[response_type].append(handler)
        logger.info(f"Registered response handler for {response_type.value}")
    
    def generate_trusted_user_response(self, user_id: str, user_name: str, 
                                     confidence: float, trust_level: str, 
                                     trust_score: float, access_granted: bool) -> RecognitionEvent:
        """Generate response for trusted user recognition"""
        current_time = time.time()
        hour = datetime.fromtimestamp(current_time).hour
        
        # Determine time of day
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Generate welcome message
        import random
        message_template = random.choice(self.welcome_messages)
        message = message_template.format(name=user_name, time_of_day=time_of_day)
        
        # Determine event type and alert level
        if access_granted:
            event_type = ResponseType.ACCESS_GRANTED
            alert_level = AlertLevel.INFO
        else:
            event_type = ResponseType.ACCESS_DENIED
            alert_level = AlertLevel.MEDIUM
            message = f"Access denied for {user_name} - insufficient trust level"
        
        event = RecognitionEvent(
            timestamp=current_time,
            event_type=event_type,
            user_id=user_id,
            user_name=user_name,
            confidence=confidence,
            trust_level=trust_level,
            trust_score=trust_score,
            access_granted=access_granted,
            alert_level=alert_level,
            message=message,
            context={
                'recognition_type': 'trusted_user',
                'time_of_day': time_of_day
            }
        )
        
        return event
    
    def generate_unknown_person_response(self, confidence: float) -> RecognitionEvent:
        """Generate response for unknown person detection"""
        current_time = time.time()
        
        # Check for escalation
        alert_level = self._calculate_unknown_person_alert_level()
        
        message = f"Unknown person detected (confidence: {confidence:.3f})"
        if alert_level.value >= AlertLevel.MEDIUM.value:
            message += " - Multiple unknown detections"
        
        event = RecognitionEvent(
            timestamp=current_time,
            event_type=ResponseType.UNKNOWN_PERSON,
            confidence=confidence,
            alert_level=alert_level,
            message=message,
            context={
                'recognition_type': 'unknown_person',
                'escalation_check': True
            }
        )
        
        return event
    
    def process_recognition_event(self, event: RecognitionEvent) -> None:
        """Process a recognition event and trigger appropriate responses"""
        # Add to history
        self.event_history.append(event)
        
        # Limit history size
        max_events = 1000
        if len(self.event_history) > max_events:
            self.event_history = self.event_history[-max_events:]
        
        # Queue for async processing
        self.response_queue.put(event)
        
        # Save to file
        self.save_event_history()
        
        logger.info_event('response_system', f"Processed recognition event: {event.event_type.value} - {event.message}")
    
    def _process_responses(self) -> None:
        """Process responses asynchronously"""
        while True:
            try:
                event = self.response_queue.get(timeout=1)
                
                # Trigger registered handlers
                if event.event_type in self.response_handlers:
                    for handler in self.response_handlers[event.event_type]:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error(f"Error in response handler: {e}")
                
                # Default console output
                self._log_event_to_console(event)
                
                self.response_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing response: {e}")
    
    def _log_event_to_console(self, event: RecognitionEvent) -> None:
        """Log event to console with appropriate formatting"""
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
        
        if event.event_type == ResponseType.ACCESS_GRANTED:
            logger.info_event('response_system', f"[{timestamp}] 🔓 {event.message}")
        elif event.event_type == ResponseType.ACCESS_DENIED:
            logger.warning(f"[{timestamp}] 🔒 {event.message}")
        elif event.event_type == ResponseType.UNKNOWN_PERSON:
            if event.alert_level.value >= AlertLevel.MEDIUM.value:
                logger.error(f"[{timestamp}] 🚨 {event.message}")
            else:
                logger.warning(f"[{timestamp}] ⚠️ {event.message}")
        else:
            logger.info(f"[{timestamp}] ℹ️ {event.message}")
    
    def _calculate_unknown_person_alert_level(self) -> AlertLevel:
        """Calculate alert level for unknown person detection based on recent history"""
        current_time = time.time()
        timeframe = self.alert_thresholds['unknown_person_timeframe']
        cutoff_time = current_time - timeframe
        
        # Count recent unknown person detections
        recent_unknown = [
            event for event in self.event_history
            if (event.event_type == ResponseType.UNKNOWN_PERSON and 
                event.timestamp >= cutoff_time)
        ]
        
        count = len(recent_unknown)
        threshold = self.alert_thresholds['unknown_person_count']
        
        if count >= threshold * 2:
            return AlertLevel.CRITICAL
        elif count >= threshold:
            return AlertLevel.HIGH
        elif count >= threshold // 2:
            return AlertLevel.MEDIUM
        else:
            return AlertLevel.LOW
    
    def get_recent_events(self, hours: int = 24) -> List[RecognitionEvent]:
        """Get recent recognition events within specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [event for event in self.event_history if event.timestamp >= cutoff_time]
    
    def get_event_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for recent events"""
        recent_events = self.get_recent_events(hours)
        
        if not recent_events:
            return {
                'total_events': 0,
                'timeframe_hours': hours,
                'event_types': {},
                'alert_levels': {},
                'access_granted': 0,
                'access_denied': 0,
                'unknown_persons': 0,
                'trusted_users': 0
            }
        
        stats = {
            'total_events': len(recent_events),
            'timeframe_hours': hours,
            'event_types': {},
            'alert_levels': {},
            'access_granted': 0,
            'access_denied': 0,
            'unknown_persons': 0,
            'trusted_users': 0
        }
        
        # Count by event type
        for event in recent_events:
            event_type = event.event_type.value
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
            
            alert_level = event.alert_level.value
            stats['alert_levels'][alert_level] = stats['alert_levels'].get(alert_level, 0) + 1
            
            if event.access_granted:
                stats['access_granted'] += 1
            elif event.event_type == ResponseType.ACCESS_DENIED:
                stats['access_denied'] += 1
            
            if event.event_type == ResponseType.UNKNOWN_PERSON:
                stats['unknown_persons'] += 1
            elif event.user_id:
                stats['trusted_users'] += 1
        
        return stats
    
    def print_event_summary(self, hours: int = 24) -> None:
        """Print a summary of recent events"""
        stats = self.get_event_statistics(hours)
        
        print(f"\n📊 Recognition Event Summary (Last {hours} hours)")
        print("=" * 60)
        print(f"Total Events: {stats['total_events']}")
        print(f"Access Granted: {stats['access_granted']}")
        print(f"Access Denied: {stats['access_denied']}")
        print(f"Unknown Persons: {stats['unknown_persons']}")
        print(f"Trusted Users: {stats['trusted_users']}")
        
        if stats['event_types']:
            print("\nEvent Types:")
            for event_type, count in stats['event_types'].items():
                print(f"  {event_type}: {count}")
        
        if stats['alert_levels']:
            print("\nAlert Levels:")
            for level, count in stats['alert_levels'].items():
                print(f"  Level {level}: {count}")

# Example usage and testing
if __name__ == "__main__":
    # Create response system
    response_system = ResponseSystem()
    
    # Example custom response handler
    def custom_alert_handler(event: RecognitionEvent):
        if event.alert_level.value >= AlertLevel.HIGH.value:
            print(f"🚨 CUSTOM ALERT: {event.message}")
    
    # Register handler
    response_system.register_response_handler(ResponseType.UNKNOWN_PERSON, custom_alert_handler)
    
    # Simulate some events
    print("🧪 Testing Recognition Response System...\n")
    
    # Trusted user with access granted
    trusted_event = response_system.generate_trusted_user_response(
        user_id="user_001",
        user_name="Alice",
        confidence=0.85,
        trust_level="HIGH",
        trust_score=0.82,
        access_granted=True
    )
    response_system.process_recognition_event(trusted_event)
    
    time.sleep(0.1)
    
    # Trusted user with access denied
    denied_event = response_system.generate_trusted_user_response(
        user_id="user_002",
        user_name="Bob",
        confidence=0.65,
        trust_level="LOW",
        trust_score=0.45,
        access_granted=False
    )
    response_system.process_recognition_event(denied_event)
    
    time.sleep(0.1)
    
    # Unknown person detection
    for i in range(4):
        unknown_event = response_system.generate_unknown_person_response(confidence=0.3 + i * 0.1)
        response_system.process_recognition_event(unknown_event)
        time.sleep(0.05)
    
    # Wait for processing
    time.sleep(1)
    
    # Print summary
    response_system.print_event_summary()