"""
User Database Management for Face Recognition

This module handles trusted user storage, face encoding management,
and provides a persistent database for user information including names,
face encodings, and access permissions.
"""

import json
import logging
import numpy as np
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import uuid
from datetime import datetime, timezone
from src.utils.smart_logger import SmartLogger

@dataclass
class UserProfile:
    """Represents a trusted user profile"""
    user_id: str
    name: str
    face_encodings: List[np.ndarray]
    enrollment_date: str
    last_seen: Optional[str] = None
    trust_level: float = 1.0
    photos_used: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.photos_used is None:
            self.photos_used = []
        if self.metadata is None:
            self.metadata = {}

class TrustedUserDatabase:
    """Manages database of trusted users and their face encodings"""
    
    def __init__(self, database_dir: str = "data/trusted_users"):
        """
        Initialize user database
        
        Args:
            database_dir: Directory to store user data
        """
        self.logger = SmartLogger(__name__)
        self.database_dir = database_dir
        self.users_file = os.path.join(database_dir, "users.json")
        self.encodings_file = os.path.join(database_dir, "face_encodings.pkl")
        
        # Ensure database directory exists
        os.makedirs(database_dir, exist_ok=True)
        
        # Load existing data
        self.users = self._load_users()
        self.face_encodings = self._load_face_encodings()
        
        self.logger.system_event(f"User database initialized with {len(self.users)} users")
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load user profiles from JSON file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    self.logger.debug(f"Loaded {len(users_data)} user profiles")
                    return users_data
            else:
                self.logger.info("No existing user database found, starting fresh")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading user database: {e}")
            return {}
    
    def _save_users(self) -> bool:
        """Save user profiles to JSON file"""
        try:
            # Create backup of existing file
            if os.path.exists(self.users_file):
                backup_file = f"{self.users_file}.backup"
                os.rename(self.users_file, backup_file)
            
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2, default=str)
            
            self.logger.debug("User database saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving user database: {e}")
            return False
    
    def _load_face_encodings(self) -> Dict[str, List[np.ndarray]]:
        """Load face encodings from pickle file"""
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    encodings_data = pickle.load(f)
                    self.logger.debug(f"Loaded face encodings for {len(encodings_data)} users")
                    return encodings_data
            else:
                self.logger.info("No existing face encodings found, starting fresh")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading face encodings: {e}")
            return {}
    
    def _save_face_encodings(self) -> bool:
        """Save face encodings to pickle file"""
        try:
            # Create backup of existing file
            if os.path.exists(self.encodings_file):
                backup_file = f"{self.encodings_file}.backup"
                os.rename(self.encodings_file, backup_file)
            
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.face_encodings, f)
            
            self.logger.debug("Face encodings saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving face encodings: {e}")
            return False
    
    def add_user(self, name: str, face_encodings: List[np.ndarray], photos_used: List[str] = None, user_id: str = None) -> str:
        """
        Add a new trusted user to the database
        
        Args:
            name: User's name
            face_encodings: List of face encodings for the user
            photos_used: List of photo filenames used for enrollment
            user_id: Optional custom user ID (auto-generated if None)
            
        Returns:
            User ID of the added user
        """
        try:
            # Generate user ID if not provided
            if user_id is None:
                user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            # Check if user already exists
            if user_id in self.users:
                raise ValueError(f"User ID '{user_id}' already exists")
            
            # Validate inputs
            if not name.strip():
                raise ValueError("User name cannot be empty")
            
            if not face_encodings:
                raise ValueError("At least one face encoding is required")
            
            # Create user profile
            current_time = datetime.now(timezone.utc).isoformat()
            
            user_data = {
                'user_id': user_id,
                'name': name.strip(),
                'enrollment_date': current_time,
                'last_seen': None,
                'trust_level': 1.0,
                'photos_used': photos_used or [],
                'metadata': {
                    'num_encodings': len(face_encodings),
                    'enrollment_version': '1.0'
                }
            }
            
            # Store user profile and encodings
            self.users[user_id] = user_data
            self.face_encodings[user_id] = face_encodings
            
            # Save to persistent storage
            if self._save_users() and self._save_face_encodings():
                self.logger.info(f"Added new user: {name} (ID: {user_id}) with {len(face_encodings)} encodings")
                return user_id
            else:
                # Rollback on save failure
                del self.users[user_id]
                del self.face_encodings[user_id]
                raise RuntimeError("Failed to save user data")
            
        except Exception as e:
            self.logger.error(f"Error adding user '{name}': {e}")
            raise
    
    def remove_user(self, user_id: str) -> bool:
        """
        Remove a user from the database
        
        Args:
            user_id: ID of user to remove
            
        Returns:
            True if user was removed, False otherwise
        """
        try:
            if user_id not in self.users:
                self.logger.warning(f"User ID '{user_id}' not found")
                return False
            
            user_name = self.users[user_id].get('name', 'Unknown')
            
            # Remove from memory
            del self.users[user_id]
            if user_id in self.face_encodings:
                del self.face_encodings[user_id]
            
            # Save changes
            if self._save_users() and self._save_face_encodings():
                self.logger.info(f"Removed user: {user_name} (ID: {user_id})")
                return True
            else:
                self.logger.error(f"Failed to save changes after removing user {user_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error removing user '{user_id}': {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID
        
        Args:
            user_id: User ID to lookup
            
        Returns:
            User profile dictionary or None if not found
        """
        return self.users.get(user_id)
    
    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by name
        
        Args:
            name: User name to lookup
            
        Returns:
            User profile dictionary or None if not found
        """
        for user_data in self.users.values():
            if user_data['name'].lower() == name.lower():
                return user_data
        return None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """
        Get list of all user profiles
        
        Returns:
            List of user profile dictionaries
        """
        return list(self.users.values())
    
    def get_all_encodings(self) -> Tuple[List[np.ndarray], List[str]]:
        """
        Get all face encodings and corresponding user IDs
        
        Returns:
            Tuple of (face_encodings_list, user_ids_list)
        """
        all_encodings = []
        all_user_ids = []
        
        for user_id, encodings in self.face_encodings.items():
            for encoding in encodings:
                all_encodings.append(encoding)
                all_user_ids.append(user_id)
        
        return all_encodings, all_user_ids
    
    def update_last_seen(self, user_id: str) -> bool:
        """
        Update the last seen timestamp for a user
        
        Args:
            user_id: User ID to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if user_id not in self.users:
                return False
            
            current_time = datetime.now(timezone.utc).isoformat()
            self.users[user_id]['last_seen'] = current_time
            
            return self._save_users()
            
        except Exception as e:
            self.logger.error(f"Error updating last seen for user '{user_id}': {e}")
            return False
    
    def update_trust_level(self, user_id: str, trust_level: float) -> bool:
        """
        Update trust level for a user
        
        Args:
            user_id: User ID to update
            trust_level: New trust level (0.0 to 1.0)
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if user_id not in self.users:
                return False
            
            trust_level = max(0.0, min(1.0, trust_level))  # Clamp to valid range
            self.users[user_id]['trust_level'] = trust_level
            
            return self._save_users()
            
        except Exception as e:
            self.logger.error(f"Error updating trust level for user '{user_id}': {e}")
            return False
    
    def add_face_encoding(self, user_id: str, face_encoding: np.ndarray) -> bool:
        """
        Add an additional face encoding for an existing user
        
        Args:
            user_id: User ID to add encoding for
            face_encoding: New face encoding to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if user_id not in self.users:
                self.logger.error(f"User ID '{user_id}' not found")
                return False
            
            if user_id not in self.face_encodings:
                self.face_encodings[user_id] = []
            
            self.face_encodings[user_id].append(face_encoding)
            
            # Update metadata
            self.users[user_id]['metadata']['num_encodings'] = len(self.face_encodings[user_id])
            
            if self._save_users() and self._save_face_encodings():
                self.logger.info(f"Added face encoding for user {user_id}")
                return True
            else:
                # Rollback on save failure
                self.face_encodings[user_id].pop()
                return False
            
        except Exception as e:
            self.logger.error(f"Error adding face encoding for user '{user_id}': {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with database statistics
        """
        total_users = len(self.users)
        total_encodings = sum(len(encodings) for encodings in self.face_encodings.values())
        
        recent_users = []
        for user_data in self.users.values():
            if user_data.get('last_seen'):
                recent_users.append(user_data)
        
        stats = {
            'total_users': total_users,
            'total_encodings': total_encodings,
            'average_encodings_per_user': total_encodings / max(1, total_users),
            'users_with_recent_activity': len(recent_users),
            'database_directory': self.database_dir,
            'files_exist': {
                'users.json': os.path.exists(self.users_file),
                'face_encodings.pkl': os.path.exists(self.encodings_file)
            }
        }
        
        return stats

# Test function for this module
def test_user_database():
    """Test user database functionality"""
    print("🗃️ Testing User Database...")
    
    # Create test database
    test_db_dir = "test_user_db"
    db = TrustedUserDatabase(test_db_dir)
    
    try:
        # Test adding users
        print("1. Testing user addition...")
        
        # Create dummy face encodings
        dummy_encoding1 = np.random.rand(128)
        dummy_encoding2 = np.random.rand(128)
        
        user_id1 = db.add_user("Alice", [dummy_encoding1], ["alice1.jpg"])
        user_id2 = db.add_user("Bob", [dummy_encoding2], ["bob1.jpg"])
        
        print(f"   ✓ Added users: {user_id1}, {user_id2}")
        
        # Test retrieving users
        print("2. Testing user retrieval...")
        alice = db.get_user(user_id1)
        bob_by_name = db.get_user_by_name("Bob")
        
        print(f"   ✓ Retrieved Alice: {alice['name'] if alice else 'Not found'}")
        print(f"   ✓ Retrieved Bob by name: {bob_by_name['name'] if bob_by_name else 'Not found'}")
        
        # Test listing users
        print("3. Testing user listing...")
        all_users = db.list_users()
        print(f"   ✓ Total users: {len(all_users)}")
        
        # Test getting all encodings
        print("4. Testing encoding retrieval...")
        encodings, user_ids = db.get_all_encodings()
        print(f"   ✓ Total encodings: {len(encodings)}")
        
        # Test updating user info
        print("5. Testing user updates...")
        db.update_last_seen(user_id1)
        db.update_trust_level(user_id2, 0.8)
        print("   ✓ Updated user information")
        
        # Test database stats
        print("6. Testing database statistics...")
        stats = db.get_database_stats()
        print(f"   ✓ Database stats: {stats}")
        
        # Test user removal
        print("7. Testing user removal...")
        removed = db.remove_user(user_id2)
        print(f"   ✓ User removal: {'Success' if removed else 'Failed'}")
        
        print("✅ User database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ User database test failed: {e}")
        return False
    finally:
        # Cleanup test database
        import shutil
        if os.path.exists(test_db_dir):
            shutil.rmtree(test_db_dir)
            print("🧹 Cleaned up test database")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_user_database()