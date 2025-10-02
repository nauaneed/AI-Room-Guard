"""
Trust Level Management System

This module implements sophisticated trust evaluation for face recognition,
including confidence-based decisions, temporal trust tracking, and trust decay mechanisms.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from src.utils.smart_logger import SmartLogger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = SmartLogger(__name__)

class TrustLevel(Enum):
    """Trust level categories"""
    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    MAXIMUM = 4

@dataclass
class TrustRecord:
    """Individual trust measurement record"""
    timestamp: float
    confidence: float
    trust_level: TrustLevel
    context: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'confidence': self.confidence,
            'trust_level': self.trust_level.value,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TrustRecord':
        """Create from dictionary"""
        return cls(
            timestamp=data['timestamp'],
            confidence=data['confidence'],
            trust_level=TrustLevel(data['trust_level']),
            context=data.get('context', '')
        )

@dataclass
class TrustProfile:
    """Complete trust profile for a user"""
    user_id: str
    name: str
    base_trust_level: TrustLevel
    current_trust_score: float
    trust_history: List[TrustRecord]
    last_updated: float
    total_interactions: int
    successful_recognitions: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'base_trust_level': self.base_trust_level.value,
            'current_trust_score': self.current_trust_score,
            'trust_history': [record.to_dict() for record in self.trust_history],
            'last_updated': self.last_updated,
            'total_interactions': self.total_interactions,
            'successful_recognitions': self.successful_recognitions
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TrustProfile':
        """Create from dictionary"""
        return cls(
            user_id=data['user_id'],
            name=data['name'],
            base_trust_level=TrustLevel(data['base_trust_level']),
            current_trust_score=data['current_trust_score'],
            trust_history=[TrustRecord.from_dict(record) for record in data['trust_history']],
            last_updated=data['last_updated'],
            total_interactions=data['total_interactions'],
            successful_recognitions=data['successful_recognitions']
        )

class TrustManager:
    """
    Advanced trust level management system for face recognition.
    
    Features:
    - Multi-level trust evaluation
    - Confidence-based decision making
    - Temporal trust tracking
    - Trust decay mechanisms
    - Historical analysis
    """
    
    def __init__(self, trust_file: str = "data/trust_profiles.json"):
        self.trust_file = trust_file
        self.trust_profiles: Dict[str, TrustProfile] = {}
        
        # Trust configuration
        self.config = {
            # Confidence thresholds for different trust levels
            'confidence_thresholds': {
                TrustLevel.LOW: 0.4,      # Lowered from 0.5 to allow enrolled users
                TrustLevel.MEDIUM: 0.65,
                TrustLevel.HIGH: 0.8,
                TrustLevel.MAXIMUM: 0.9
            },
            
            # Trust score calculation weights
            'weights': {
                'current_confidence': 0.4,
                'historical_average': 0.3,
                'consistency_bonus': 0.2,
                'recency_factor': 0.1
            },
            
            # Trust decay parameters
            'decay': {
                'enabled': True,
                'daily_decay_rate': 0.02,  # 2% per day
                'minimum_score': 0.3,
                'max_days_without_interaction': 30
            },
            
            # Historical analysis
            'history': {
                'max_records': 100,
                'analysis_window_days': 7,
                'min_interactions_for_stable_trust': 5
            }
        }
        
        self.load_trust_profiles()
        logger.info("Trust Manager initialized")
    
    def load_trust_profiles(self) -> None:
        """Load trust profiles from file"""
        try:
            with open(self.trust_file, 'r') as f:
                data = json.load(f)
                self.trust_profiles = {
                    user_id: TrustProfile.from_dict(profile_data)
                    for user_id, profile_data in data.items()
                }
            logger.info(f"Loaded {len(self.trust_profiles)} trust profiles")
        except FileNotFoundError:
            logger.info("No existing trust profiles found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading trust profiles: {e}")
    
    def save_trust_profiles(self) -> None:
        """Save trust profiles to file"""
        try:
            # Create directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(self.trust_file), exist_ok=True)
            
            data = {
                user_id: profile.to_dict()
                for user_id, profile in self.trust_profiles.items()
            }
            
            with open(self.trust_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.periodic_status(f"Saved {len(self.trust_profiles)} trust profiles", "trust_save")
        except Exception as e:
            logger.error(f"Error saving trust profiles: {e}")
    
    def create_trust_profile(self, user_id: str, name: str, 
                           initial_trust_level: TrustLevel = TrustLevel.MEDIUM) -> TrustProfile:
        """Create a new trust profile for a user"""
        profile = TrustProfile(
            user_id=user_id,
            name=name,
            base_trust_level=initial_trust_level,
            current_trust_score=self._trust_level_to_score(initial_trust_level),
            trust_history=[],
            last_updated=time.time(),
            total_interactions=0,
            successful_recognitions=0
        )
        
        self.trust_profiles[user_id] = profile
        self.save_trust_profiles()
        logger.info(f"Created trust profile for user: {name} ({user_id})")
        return profile
    
    def record_recognition_event(self, user_id: str, confidence: float, 
                               context: str = "") -> TrustLevel:
        """
        Record a face recognition event and update trust levels
        
        Args:
            user_id: User identifier
            confidence: Recognition confidence (0.0-1.0)
            context: Optional context information
            
        Returns:
            Current trust level after update
        """
        if user_id not in self.trust_profiles:
            logger.warning(f"No trust profile found for user: {user_id}")
            return TrustLevel.UNKNOWN
        
        profile = self.trust_profiles[user_id]
        current_time = time.time()
        
        # Determine trust level based on confidence
        trust_level = self._confidence_to_trust_level(confidence)
        
        # Create trust record
        record = TrustRecord(
            timestamp=current_time,
            confidence=confidence,
            trust_level=trust_level,
            context=context
        )
        
        # Update profile
        profile.trust_history.append(record)
        profile.total_interactions += 1
        if confidence >= self.config['confidence_thresholds'][TrustLevel.MEDIUM]:
            profile.successful_recognitions += 1
        profile.last_updated = current_time
        
        # Limit history size
        max_records = self.config['history']['max_records']
        if len(profile.trust_history) > max_records:
            profile.trust_history = profile.trust_history[-max_records:]
        
        # Recalculate trust score
        profile.current_trust_score = self._calculate_trust_score(profile)
        
        # Save changes
        self.save_trust_profiles()
        
        current_trust_level = self._score_to_trust_level(profile.current_trust_score)
        logger.trust_change_event(profile.name, profile.current_trust_score - 0.05, profile.current_trust_score, f"confidence={confidence:.3f}")
        
        return current_trust_level
    
    def get_current_trust_level(self, user_id: str) -> TrustLevel:
        """Get current trust level for a user"""
        if user_id not in self.trust_profiles:
            return TrustLevel.UNKNOWN
        
        profile = self.trust_profiles[user_id]
        
        # Apply trust decay if enabled
        if self.config['decay']['enabled']:
            self._apply_trust_decay(profile)
        
        return self._score_to_trust_level(profile.current_trust_score)
    
    def should_grant_access(self, user_id: str, required_trust_level: TrustLevel = TrustLevel.MEDIUM) -> bool:
        """
        Determine if user should be granted access based on trust level
        
        Args:
            user_id: User identifier
            required_trust_level: Minimum required trust level
            
        Returns:
            True if access should be granted
        """
        current_trust = self.get_current_trust_level(user_id)
        return current_trust.value >= required_trust_level.value
    
    def get_trust_summary(self, user_id: str) -> Optional[Dict]:
        """Get comprehensive trust summary for a user"""
        if user_id not in self.trust_profiles:
            return None
        
        profile = self.trust_profiles[user_id]
        current_trust = self.get_current_trust_level(user_id)
        
        # Calculate statistics
        success_rate = (profile.successful_recognitions / profile.total_interactions 
                       if profile.total_interactions > 0 else 0.0)
        
        recent_history = self._get_recent_history(profile, days=7)
        recent_avg_confidence = (sum(r.confidence for r in recent_history) / len(recent_history)
                                if recent_history else 0.0)
        
        return {
            'user_id': user_id,
            'name': profile.name,
            'current_trust_level': current_trust.name,
            'current_trust_score': profile.current_trust_score,
            'base_trust_level': profile.base_trust_level.name,
            'total_interactions': profile.total_interactions,
            'successful_recognitions': profile.successful_recognitions,
            'success_rate': success_rate,
            'recent_avg_confidence': recent_avg_confidence,
            'last_seen': datetime.fromtimestamp(profile.last_updated).isoformat(),
            'days_since_last_interaction': (time.time() - profile.last_updated) / 86400
        }
    
    def get_all_users_summary(self) -> List[Dict]:
        """Get trust summary for all users"""
        return [self.get_trust_summary(user_id) for user_id in self.trust_profiles.keys()]
    
    def _confidence_to_trust_level(self, confidence: float) -> TrustLevel:
        """Convert confidence score to trust level"""
        thresholds = self.config['confidence_thresholds']
        
        if confidence >= thresholds[TrustLevel.MAXIMUM]:
            return TrustLevel.MAXIMUM
        elif confidence >= thresholds[TrustLevel.HIGH]:
            return TrustLevel.HIGH
        elif confidence >= thresholds[TrustLevel.MEDIUM]:
            return TrustLevel.MEDIUM
        elif confidence >= thresholds[TrustLevel.LOW]:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNKNOWN
    
    def _trust_level_to_score(self, trust_level: TrustLevel) -> float:
        """Convert trust level to numerical score"""
        mapping = {
            TrustLevel.UNKNOWN: 0.0,
            TrustLevel.LOW: 0.25,
            TrustLevel.MEDIUM: 0.5,
            TrustLevel.HIGH: 0.75,
            TrustLevel.MAXIMUM: 1.0
        }
        return mapping.get(trust_level, 0.0)
    
    def _score_to_trust_level(self, score: float) -> TrustLevel:
        """Convert numerical score to trust level"""
        if score >= 0.9:
            return TrustLevel.MAXIMUM
        elif score >= 0.75:
            return TrustLevel.HIGH
        elif score >= 0.5:
            return TrustLevel.MEDIUM
        elif score >= 0.25:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNKNOWN
    
    def _calculate_trust_score(self, profile: TrustProfile) -> float:
        """Calculate comprehensive trust score for a profile"""
        if not profile.trust_history:
            return self._trust_level_to_score(profile.base_trust_level)
        
        weights = self.config['weights']
        
        # Current confidence (most recent recognition)
        current_confidence = profile.trust_history[-1].confidence
        
        # Historical average confidence
        historical_avg = sum(r.confidence for r in profile.trust_history) / len(profile.trust_history)
        
        # Consistency bonus (based on standard deviation)
        confidences = [r.confidence for r in profile.trust_history]
        if len(confidences) > 1:
            mean_conf = sum(confidences) / len(confidences)
            variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
            std_dev = variance ** 0.5
            consistency_bonus = max(0, 1 - (std_dev * 2))  # Lower std_dev = higher bonus
        else:
            consistency_bonus = 1.0
        
        # Recency factor (more recent interactions weighted higher)
        recent_history = self._get_recent_history(profile, days=7)
        if recent_history:
            recent_avg = sum(r.confidence for r in recent_history) / len(recent_history)
            recency_factor = recent_avg
        else:
            recency_factor = historical_avg
        
        # Calculate weighted score
        score = (
            weights['current_confidence'] * current_confidence +
            weights['historical_average'] * historical_avg +
            weights['consistency_bonus'] * consistency_bonus +
            weights['recency_factor'] * recency_factor
        )
        
        return max(0.0, min(1.0, score))  # Clamp to [0, 1]
    
    def _apply_trust_decay(self, profile: TrustProfile) -> None:
        """Apply trust decay based on time since last interaction"""
        if not self.config['decay']['enabled']:
            return
        
        current_time = time.time()
        days_since_last = (current_time - profile.last_updated) / 86400
        
        if days_since_last > 0:
            decay_rate = self.config['decay']['daily_decay_rate']
            decay_factor = (1 - decay_rate) ** days_since_last
            
            # Apply decay to current score
            decayed_score = profile.current_trust_score * decay_factor
            
            # Ensure minimum score
            min_score = self.config['decay']['minimum_score']
            profile.current_trust_score = max(decayed_score, min_score)
            
            # If too much time has passed, reset to base level
            max_days = self.config['decay']['max_days_without_interaction']
            if days_since_last > max_days:
                profile.current_trust_score = self._trust_level_to_score(profile.base_trust_level)
    
    def _get_recent_history(self, profile: TrustProfile, days: int) -> List[TrustRecord]:
        """Get trust records from recent time window"""
        cutoff_time = time.time() - (days * 86400)
        return [record for record in profile.trust_history if record.timestamp >= cutoff_time]

# Example usage and testing
if __name__ == "__main__":
    # Create trust manager
    trust_manager = TrustManager()
    
    # Create a test user
    user_id = "test_user_001"
    profile = trust_manager.create_trust_profile(user_id, "Test User", TrustLevel.MEDIUM)
    
    # Simulate some recognition events
    test_confidences = [0.85, 0.78, 0.92, 0.67, 0.88, 0.75, 0.91]
    
    for i, confidence in enumerate(test_confidences):
        trust_level = trust_manager.record_recognition_event(
            user_id, confidence, f"Test recognition {i+1}"
        )
        print(f"Recognition {i+1}: confidence={confidence:.3f}, trust_level={trust_level.name}")
    
    # Get trust summary
    summary = trust_manager.get_trust_summary(user_id)
    print("\nTrust Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test access decision
    access_granted = trust_manager.should_grant_access(user_id, TrustLevel.HIGH)
    print(f"\nAccess granted (HIGH required): {access_granted}")