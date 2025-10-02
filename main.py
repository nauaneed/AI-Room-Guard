#!/usr/bin/env python3
"""
Main entry point for the AI Guard Agent.
Milestone 1: Speech activation and basic input handling.
"""

import sys
import os
import signal
import time

from src.utils.logger import setup_logging
from src.core.guard_agent import GuardAgent

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print("\nReceived interrupt signal. Shutting down...")
    global agent
    if agent:
        agent.cleanup()
    sys.exit(0)

def main():
    """Main function"""
    global agent
    
    # Setup logging
    logger = setup_logging(log_level="INFO", console_output=True)
    logger.info("Starting AI Guard Agent - Milestone 1")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and initialize agent
    agent = GuardAgent()
    
    try:
        print("=" * 60)
        print("AI GUARD AGENT - MILESTONE 1")
        print("=" * 60)
        print("Features:")
        print("- Voice activation with 'Guard my room' or 'activate surveillance'")
        print("- Camera activates only when guard mode is ON")
        print("- Real-time audio and video processing")
        print("- State management system")
        print("- Deactivation with 'stop surveillance' or 'stop' command")
        print()
        print("Starting system...")
        print("🎤 Audio: Ready for voice commands")
        print("📹 Camera: Will start when you say 'Guard my room'")
        print("Say 'Guard my room' or 'activate surveillance' to activate guard mode")
        print("Say 'stop surveillance' or 'stop' to deactivate")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        
        # Start the agent
        if not agent.start():
            logger.error("Failed to start Guard Agent")
            return 1
        
        # Main loop - display status and handle user input
        try:
            last_status_time = 0
            while True:
                current_time = time.time()
                
                # Display status every 10 seconds
                if current_time - last_status_time >= 10:
                    status = agent.get_status()
                    print(f"\n[{time.strftime('%H:%M:%S')}] Status:")
                    print(f"  State: {status['current_state']}")
                    print(f"  Runtime: {status['runtime']:.1f}s")
                    print(f"  Commands processed: {status['stats']['commands_processed']}")
                    print(f"  Activations: {status['stats']['activations']}")
                    print(f"  Audio queue: {status['audio_queue_size']} items")
                    
                    if status['current_state'] == 'guard_active':
                        print("  🔴 GUARD MODE ACTIVE - Room is being monitored")
                        print("  📹 Camera: ON")
                    else:
                        print("  📹 Camera: OFF (activates when guard mode starts)")
                    
                    last_status_time = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        
    except Exception as e:
        logger.error(f"Error running Guard Agent: {e}")
        return 1
    
    finally:
        print("Cleaning up...")
        agent.cleanup()
        logger.info("AI Guard Agent stopped")
    
    return 0

if __name__ == "__main__":
    agent = None
    exit_code = main()
    sys.exit(exit_code)