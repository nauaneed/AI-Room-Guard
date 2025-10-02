#!/usr/bin/env python3
"""
AI Guard Agent - Milestone 2 Integration Demo
Demonstrates the complete system with face recognition integrated.
"""

import sys
import os
import time
import logging

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

from src.core.guard_agent import GuardAgent
from config.settings import GuardState

def setup_logging():
    """Setup logging for the demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/logs/integration_demo.log')
        ]
    )

def print_status(agent: GuardAgent):
    """Print comprehensive system status"""
    status = agent.get_status()
    
    print("\n" + "="*80)
    print("🤖 AI GUARD AGENT - INTEGRATED SYSTEM STATUS")
    print("="*80)
    print(f"State: {status['current_state']} | Runtime: {status['runtime']:.1f}s | Queue Sizes: A={status['audio_queue_size']} F={status['face_recognition_queue_size']}")
    print(f"Audio: {'🟢 Active' if status['audio_available'] else '🔴 Inactive'} | Camera: {'🟢 Active' if status['camera_available'] else '🔴 Inactive'} | Users: {status['enrolled_users']}")
    
    stats = status['stats']
    print(f"📊 Audio: {stats['commands_processed']} commands, {stats['activations']} activations")
    print(f"👁️  Vision: {stats['faces_detected']} faces, {stats['trusted_recognitions']} trusted, {stats['unknown_detections']} unknown")
    print("="*80)

def run_integration_test():
    """Run comprehensive integration test"""
    print("🚀 Starting AI Guard Agent Integration Test")
    print("="*60)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create guard agent
    agent = GuardAgent()
    
    try:
        print("🔧 Initializing guard agent...")
        if not agent.start():
            print("❌ Failed to start guard agent")
            return False
        
        print("✅ Guard agent started successfully!")
        print("\n📋 Test Phases:")
        print("1. Idle monitoring (10s)")
        print("2. Say 'guard my room' to activate")
        print("3. Face recognition in guard mode")
        print("4. Command 'stop guard' to deactivate")
        print("\nPress Ctrl+C to exit anytime")
        
        # Phase 1: Idle monitoring
        print("\n🔵 Phase 1: Idle Monitoring")
        start_time = time.time()
        while time.time() - start_time < 10:
            print_status(agent)
            time.sleep(2)
        
        # Phase 2: Wait for activation
        print("\n🟡 Phase 2: Waiting for Activation Command")
        print("💬 Say: 'guard my room' or 'start guard mode'")
        
        activation_timeout = 30  # 30 seconds to activate
        activation_start = time.time()
        
        while time.time() - activation_start < activation_timeout:
            status = agent.get_status()
            
            if status['current_state'] == GuardState.GUARD_ACTIVE.value:
                print("\n🔴 GUARD MODE ACTIVATED!")
                break
            
            print_status(agent)
            time.sleep(2)
        else:
            print("\n⏰ Activation timeout - continuing without activation")
        
        # Phase 3: Guard mode monitoring
        current_state = agent.get_status()['current_state']
        if current_state == GuardState.GUARD_ACTIVE.value:
            print("\n🔴 Phase 3: Guard Mode - Face Recognition Active")
            print("👤 Position yourself in front of the camera")
            print("🔍 System will detect and recognize faces")
            
            guard_start = time.time()
            guard_duration = 60  # Monitor for 1 minute
            
            while time.time() - guard_start < guard_duration:
                status = agent.get_status()
                
                # Check if still in guard mode
                if status['current_state'] != GuardState.GUARD_ACTIVE.value:
                    print(f"\n📋 State changed to: {status['current_state']}")
                    time.sleep(1)
                    continue
                
                print_status(agent)
                time.sleep(3)
            
            print("\n🟢 Guard monitoring phase completed")
        
        # Final status
        print("\n📊 Final System Status:")
        print_status(agent)
        
        print("\n✅ Integration test completed successfully!")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return True
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return False
    finally:
        print("\n🧹 Cleaning up...")
        agent.stop()
        agent.cleanup()
        print("✅ Cleanup completed")

def run_quick_demo():
    """Run a quick demo showing system capabilities"""
    print("🚀 Quick Demo - AI Guard Agent with Face Recognition")
    
    setup_logging()
    agent = GuardAgent()
    
    try:
        if not agent.start():
            print("❌ Failed to start agent")
            return False
        
        print("✅ System started - monitoring for 30 seconds...")
        
        start_time = time.time()
        while time.time() - start_time < 30:
            status = agent.get_status()
            
            # Compact status display
            state = status['current_state']
            runtime = status['runtime']
            stats = status['stats']
            
            print(f"\r[{runtime:6.1f}s] State: {state:15} | "
                  f"Faces: {stats['faces_detected']:3} | "
                  f"Trusted: {stats['trusted_recognitions']:2} | "
                  f"Unknown: {stats['unknown_detections']:2} | "
                  f"Users: {status['enrolled_users']}", end='')
            
            time.sleep(1)
        
        print("\n✅ Quick demo completed!")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted")
        return True
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return False
    finally:
        agent.stop()
        agent.cleanup()

def main():
    """Main demo function"""
    print("🤖 AI Guard Agent - Milestone 2 Integration")
    print("=" * 50)
    print("Choose demo mode:")
    print("1. Full Integration Test (comprehensive)")
    print("2. Quick Demo (30 seconds)")
    print("3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            return run_integration_test()
        elif choice == '2':
            return run_quick_demo()
        elif choice == '3':
            print("👋 Goodbye!")
            return True
        else:
            print("❌ Invalid choice")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return True

if __name__ == "__main__":
    main()