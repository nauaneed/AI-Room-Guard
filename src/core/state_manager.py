"""
State management for the AI Guard Agent
"""

import logging
import time
import threading
from enum import Enum
from typing import Optional, Dict, Any, Callable
from src.utils.smart_logger import SmartLogger

import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional, Dict, Any
from config.settings import GuardState

class StateManager:
    """Manages system states and state transitions"""
    
    def __init__(self, initial_state: GuardState = GuardState.IDLE):
        """Initialize state manager with given initial state"""
        self.logger = SmartLogger(__name__)
        self._state_lock = threading.RLock()  # Add missing lock
        self._current_state = initial_state
        self._previous_state = None
        self._state_start_time = time.time()
        self._state_history = []
        self._listeners = []
        self._state_changed_callbacks = []  # Add missing callbacks list
        
        # Valid state transitions  
        self._valid_transitions = {
            GuardState.IDLE: [GuardState.LISTENING, GuardState.GUARD_ACTIVE],
            GuardState.LISTENING: [GuardState.IDLE, GuardState.GUARD_ACTIVE],
            GuardState.GUARD_ACTIVE: [GuardState.IDLE, GuardState.LISTENING],
        }
        
        # Validation
        if not isinstance(initial_state, GuardState):
            raise ValueError(f"Invalid state type: {type(initial_state)}")
        
        # State-specific attributes
        self._guard_start_time = None
        self._total_guard_time = 0.0
        self._escalation_data = {}
        
        # Log initialization
        self.logger.system_event(f"State manager initialized with state: {self._current_state.value}")
    
    @property
    def current_state(self) -> GuardState:
        """Get current state"""
        with self._state_lock:
            return self._current_state
    
    @property
    def previous_state(self) -> Optional[GuardState]:
        """Get previous state"""
        with self._state_lock:
            return self._previous_state
    
    def change_state(self, new_state: GuardState, context: Dict[str, Any] = None) -> bool:
        """
        Change to a new state if transition is valid.
        
        Args:
            new_state: The state to transition to
            context: Optional context information about the state change
            
        Returns:
            True if state change was successful, False otherwise
        """
        if context is None:
            context = {}
        
        with self._state_lock:
            # Check if transition is valid
            if not self._is_valid_transition(self._current_state, new_state):
                self.logger.warning(
                    f"Invalid state transition: {self._current_state.value} -> {new_state.value}"
                )
                return False
            
            # Record state change
            old_state = self._current_state
            state_duration = time.time() - self._state_start_time
            
            self._previous_state = self._current_state
            self._current_state = new_state
            self._state_start_time = time.time()
            
            # Add to history
            self._state_history.append({
                'from_state': old_state,
                'to_state': new_state,
                'timestamp': time.time(),
                'duration': state_duration,
                'context': context
            })
            
            # Keep only last 100 state changes
            if len(self._state_history) > 100:
                self._state_history = self._state_history[-100:]
            
            self.logger.state_change(old_state.value, new_state.value, f"duration: {state_duration:.2f}s")
        
        # Notify callbacks (outside of lock to prevent deadlocks)
        self._notify_state_changed(old_state, new_state, context)
        return True
    
    def _is_valid_transition(self, from_state: GuardState, to_state: GuardState) -> bool:
        """Check if state transition is valid"""
        if from_state == to_state:
            return True  # Allow staying in same state
        
        return to_state in self._valid_transitions.get(from_state, [])
    
    def add_state_changed_callback(self, callback: Callable[[GuardState, GuardState, Dict[str, Any]], None]):
        """Add callback to be called when state changes"""
        self._state_changed_callbacks.append(callback)
        self.logger.debug(f"Added state change callback: {callback.__name__}")
    
    def remove_state_changed_callback(self, callback: Callable):
        """Remove state change callback"""
        if callback in self._state_changed_callbacks:
            self._state_changed_callbacks.remove(callback)
            self.logger.debug(f"Removed state change callback: {callback.__name__}")
    
    def _notify_state_changed(self, old_state: GuardState, new_state: GuardState, context: Dict[str, Any]):
        """Notify all callbacks of state change"""
        for callback in self._state_changed_callbacks:
            try:
                callback(old_state, new_state, context)
            except Exception as e:
                self.logger.error(f"Error in state change callback {callback.__name__}: {e}")
    
    def is_in_state(self, state: GuardState) -> bool:
        """Check if currently in specified state"""
        return self.current_state == state
    
    def get_state_duration(self) -> float:
        """Get how long the system has been in current state (seconds)"""
        with self._state_lock:
            return time.time() - self._state_start_time
    
    def get_state_history(self, limit: int = 10) -> list:
        """Get recent state change history"""
        with self._state_lock:
            return self._state_history[-limit:].copy()
    
    def get_state_stats(self) -> Dict[str, Any]:
        """Get statistics about state usage"""
        with self._state_lock:
            current_duration = time.time() - self._state_start_time  # Calculate duration directly to avoid deadlock
            
            if not self._state_history:
                return {
                    'current_state': self._current_state.value,
                    'current_duration': current_duration,
                    'total_transitions': 0,
                    'state_counts': {},
                    'average_durations': {}
                }
            
            # Count state occurrences and durations
            state_counts = {}
            state_durations = {}
            
            for entry in self._state_history:
                state = entry['to_state']
                duration = entry['duration']
                
                if state not in state_counts:
                    state_counts[state] = 0
                    state_durations[state] = []
                
                state_counts[state] += 1
                state_durations[state].append(duration)
            
            # Calculate average durations
            average_durations = {}
            for state, durations in state_durations.items():
                average_durations[state.value] = sum(durations) / len(durations)
            
            return {
                'current_state': self._current_state.value,
                'current_duration': current_duration,
                'total_transitions': len(self._state_history),
                'state_counts': {state.value: count for state, count in state_counts.items()},
                'average_durations': average_durations
            }
    
    def reset(self):
        """Reset state manager to initial state"""
        with self._state_lock:
            old_state = self._current_state
            self._current_state = GuardState.IDLE
            self._previous_state = None
            self._state_history.clear()
            self._state_start_time = time.time()
            
        self.logger.system_event("State manager reset to IDLE")
        self._notify_state_changed(old_state, GuardState.IDLE, {'reason': 'reset'})

# Test function for this module
def test_state_manager():
    """Test state manager functionality"""
    
    def on_state_changed(old_state, new_state, context):
        print(f"State changed: {old_state.value} -> {new_state.value} (context: {context})")
    
    # Initialize state manager
    state_manager = StateManager()
    state_manager.add_state_changed_callback(on_state_changed)
    
    print(f"Initial state: {state_manager.current_state.value}")
    
    # Test valid transitions
    print("\nTesting valid transitions...")
    transitions = [
        (GuardState.LISTENING, {'reason': 'audio detected'}),
        (GuardState.PROCESSING, {'reason': 'processing command'}),
        (GuardState.GUARD_ACTIVE, {'reason': 'activation command recognized'}),
        (GuardState.IDLE, {'reason': 'deactivation'})
    ]
    
    for new_state, context in transitions:
        success = state_manager.change_state(new_state, context)
        print(f"Transition to {new_state.value}: {'SUCCESS' if success else 'FAILED'}")
        time.sleep(1)  # Brief pause between transitions
    
    # Test invalid transition
    print("\nTesting invalid transition...")
    success = state_manager.change_state(GuardState.GUARD_ACTIVE, {'reason': 'invalid'})
    print(f"Invalid transition: {'SUCCESS' if success else 'FAILED (expected)'}")
    
    # Show statistics
    print("\nState statistics:")
    stats = state_manager.get_state_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show history
    print("\nState history:")
    history = state_manager.get_state_history()
    for entry in history:
        print(f"  {entry['from_state'].value} -> {entry['to_state'].value} "
              f"({entry['duration']:.2f}s) - {entry['context']}")
    
    return True

if __name__ == "__main__":
    # Run test when module is executed directly
    logging.basicConfig(level=logging.INFO)
    test_state_manager()