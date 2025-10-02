"""
Initialize trust profiles for existing users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.trust_manager import TrustManager, TrustLevel
from src.core.user_database import TrustedUserDatabase

def initialize_trust_profiles():
    """Initialize trust profiles for existing users in the database"""
    print("Initializing trust profiles for existing users...")
    
    # Initialize components
    trust_manager = TrustManager()
    user_database = TrustedUserDatabase()
    
    # Get all users from database
    all_users = user_database.list_users()
    
    if not all_users:
        print("No users found in database")
        return
    
    print(f"Found {len(all_users)} users in database")
    
    for user in all_users:
        user_id = user['user_id']
        name = user['name']
        
        # Check if trust profile already exists
        existing_summary = trust_manager.get_trust_summary(user_id)
        
        if existing_summary is None:
            # Create new trust profile with HIGH initial trust level for enrolled users
            trust_profile = trust_manager.create_trust_profile(
                user_id=user_id,
                name=name,
                initial_trust_level=TrustLevel.HIGH
            )
            print(f"✅ Created trust profile for: {name} (ID: {user_id})")
        else:
            print(f"⚠️  Trust profile already exists for: {name} (ID: {user_id})")
    
    # Display all trust profiles
    print("\n📊 Current Trust Profiles:")
    all_summaries = trust_manager.get_all_users_summary()
    
    for summary in all_summaries:
        print(f"\n👤 {summary['name']} ({summary['user_id']})")
        print(f"   Trust Level: {summary['current_trust_level']}")
        print(f"   Trust Score: {summary['current_trust_score']:.3f}")
        print(f"   Total Interactions: {summary['total_interactions']}")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        print(f"   Last Seen: {summary['last_seen']}")

if __name__ == "__main__":
    initialize_trust_profiles()