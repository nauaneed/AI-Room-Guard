#!/usr/bin/env python3
"""
Setup and test script for Milestone 1.
This script helps you get started with the AI Guard Agent.
"""

import sys
import os
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, but found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    print("\nChecking dependencies...")
    
    dependencies = [
        'pyaudio',
        'speechrecognition', 
        'opencv-python',
        'numpy'
    ]
    
    missing = []
    for dep in dependencies:
        # Convert package names for import
        import_name = dep.replace('-', '_').replace('opencv_python', 'cv2').replace('speechrecognition', 'speech_recognition')
        
        try:
            spec = importlib.util.find_spec(import_name)
            if spec is None:
                missing.append(dep)
                print(f"❌ {dep} not found")
            else:
                print(f"✓ {dep} is available")
        except ImportError:
            missing.append(dep)
            print(f"❌ {dep} not found")
    
    return missing

def install_dependencies():
    """Install missing dependencies"""
    print("\nWould you like to install the required dependencies? (y/n): ", end="")
    response = input().lower().strip()
    
    if response != 'y':
        print("Please install the dependencies manually using:")
        print("pip install -r requirements.txt")
        return False
    
    try:
        print("Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_hardware():
    """Test hardware components"""
    print("\nTesting hardware components...")
    
    # Test microphone
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        # Check for input devices
        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(info['name'])
        
        if input_devices:
            print(f"✓ Found {len(input_devices)} microphone(s)")
            print(f"  Default: {input_devices[0]}")
        else:
            print("❌ No microphones found")
            
        p.terminate()
        
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        return False
    
    # Test camera
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✓ Camera is working")
                print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
            else:
                print("❌ Camera found but cannot capture frames")
            cap.release()
        else:
            print("❌ No camera found or camera access denied")
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False
    
    return True

def run_quick_test():
    """Run a quick functionality test"""
    print("\nRunning quick functionality test...")
    
    # # Add src and root directories to path for relative imports
    # root_dir = os.path.dirname(__file__)
    # src_dir = os.path.join(root_dir, 'src')
    # sys.path.insert(0, src_dir)
    # sys.path.insert(0, root_dir)
    
    try:
        # Test imports
        from config.settings import GuardState, AudioConfig
        from audio.audio_recorder import AudioRecorder
        from video.camera_handler import CameraHandler
        from core.state_manager import StateManager
        
        print("✓ All modules import successfully")
        
        # Test basic functionality
        state_manager = StateManager()
        print(f"✓ State manager initialized: {state_manager.current_state.value}")
        
        # Test audio recorder initialization
        recorder = AudioRecorder()
        if recorder.initialize():
            print("✓ Audio recorder can be initialized")
            recorder.cleanup()
        else:
            print("❌ Audio recorder initialization failed")
            
        # Test camera initialization  
        camera = CameraHandler()
        if camera.initialize():
            print("✓ Camera can be initialized")
            camera.cleanup()
        else:
            print("❌ Camera initialization failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("AI GUARD AGENT - MILESTONE 1 SETUP")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\nMissing dependencies: {missing_deps}")
        if not install_dependencies():
            return 1
        
        # Re-check after installation
        missing_deps = check_dependencies()
        if missing_deps:
            print(f"❌ Still missing: {missing_deps}")
            return 1
    
    # Test hardware
    if not test_hardware():
        print("\n⚠️  Hardware issues detected. The system may not work properly.")
        print("Please ensure you have a working microphone and camera.")
    
    # Run quick test
    if not run_quick_test():
        print("\n❌ Setup test failed. Please check the error messages above.")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run the demo: python milestone_demos/milestone_1_demo.py")
    print("2. Run the full system: python main.py")
    print("3. Say 'Guard my room' to test activation")
    print("4. Say 'stop' to deactivate")
    print("\nFor detailed instructions, see README.md")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)