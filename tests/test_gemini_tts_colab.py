#!/usr/bin/env python3
"""
Gemini TTS test following exact Colab notebook pattern
Based on: https://colab.research.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/audio/speech/getting-started/get_started_with_gemini_tts_voices.ipynb
"""

import os
import subprocess
import tempfile
from google.api_core.client_options import ClientOptions
from google.cloud import texttospeech_v1beta1 as texttospeech

# Optional IPython imports for Jupyter environments
try:
    from IPython.display import Audio, display
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

def setup_gcloud_auth():
    """Set up gcloud authentication if not already done"""
    
    project_id = os.environ.get("GEMINI_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("❌ Please set GEMINI_PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable")
        return False, None
    
    print(f"📋 Using Project ID: {project_id}")
    
    # Check if gcloud is available
    try:
        result = subprocess.run(["which", "gcloud"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ gcloud CLI not found. Please install it:")
            print("   curl https://sdk.cloud.google.com | bash")
            print("   exec -l $SHELL")
            return False, None
            
        print("✅ gcloud CLI found")
        
        # Set project
        print(f"🔧 Setting gcloud project to {project_id}...")
        subprocess.run(["gcloud", "config", "set", "project", project_id], check=True)
        
        # Check authentication status
        try:
            result = subprocess.run(
                ["gcloud", "auth", "application-default", "print-access-token"], 
                capture_output=True, text=True, check=True
            )
            print("✅ Authentication already configured")
            return True, project_id
            
        except subprocess.CalledProcessError:
            print("🔐 Setting up authentication...")
            print("Running: gcloud auth application-default login")
            
            # Run the auth command interactively
            subprocess.run(["gcloud", "auth", "application-default", "login"], check=True)
            
            # Also set quota project
            subprocess.run([
                "gcloud", "auth", "application-default", "set-quota-project", project_id
            ], check=True)
            
            print("✅ Authentication setup complete")
            return True, project_id
            
    except Exception as e:
        print(f"❌ Error setting up gcloud auth: {e}")
        return False, None

def test_gemini_tts_colab_style():
    """Test Gemini TTS following the exact Colab notebook pattern"""
    
    print("🔐 Setting up authentication...")
    auth_success, project_id = setup_gcloud_auth()
    
    if not auth_success:
        return False
    
    try:
        # Following the exact Colab pattern
        TTS_LOCATION = "global"
        
        # Set constants (from Colab notebook)
        API_ENDPOINT = (
            f"{TTS_LOCATION}-texttospeech.googleapis.com"
            if TTS_LOCATION != "global"
            else "texttospeech.googleapis.com"
        )
        
        print(f"🌐 API Endpoint: {API_ENDPOINT}")
        
        # Initialize client (exact Colab pattern)
        client = texttospeech.TextToSpeechClient(
            client_options=ClientOptions(api_endpoint=API_ENDPOINT)
        )
        
        print("✅ TTS Client initialized")
        
        # Test synthesis using exact Colab parameters
        MODEL = "gemini-2.5-flash-preview-tts"
        VOICE = "Aoede"  # High-definition voice from Colab
        LANGUAGE_CODE = "en-us"
        
        print(f"🎤 Using model: {MODEL}")
        print(f"🗣️  Using voice: {VOICE}")
        print(f"🌍 Language: {LANGUAGE_CODE}")
        
        # Test 1: Basic synthesis
        print("\n🧪 Test 1: Basic synthesis...")
        
        TEXT = "Hello world! This is Gemini TTS speaking with high definition voice quality."
        
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=TEXT),
            voice=texttospeech.VoiceSelectionParams(
                language_code=LANGUAGE_CODE,
                name=VOICE,
                model=MODEL
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
        )
        
        # Save basic audio
        basic_file = "/tmp/gemini_tts_basic.mp3"
        with open(basic_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ Basic synthesis successful! Saved to: {basic_file}")
        print(f"📊 Audio size: {len(response.audio_content)} bytes")
        
        # Test 2: With prompt (exact Colab pattern)
        print("\n🧪 Test 2: Synthesis with emotion prompt...")
        
        PROMPT = "You are having a conversation with a friend. Say the following in a happy and casual way"
        TEXT_WITH_EMOTION = "hahaha, i did NOT expect that. can you believe it!"
        
        response_with_prompt = client.synthesize_speech(
            input=texttospeech.SynthesisInput(
                text=TEXT_WITH_EMOTION,
                prompt=PROMPT
            ),
            voice=texttospeech.VoiceSelectionParams(
                language_code=LANGUAGE_CODE,
                name=VOICE,
                model=MODEL
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
        )
        
        # Save prompt-based audio
        prompt_file = "/tmp/gemini_tts_prompt.mp3"
        with open(prompt_file, "wb") as out:
            out.write(response_with_prompt.audio_content)
        
        print(f"✅ Prompt-based synthesis successful! Saved to: {prompt_file}")
        print(f"📊 Audio size: {len(response_with_prompt.audio_content)} bytes")
        
        # Test 3: Speed modification
        print("\n🧪 Test 3: Speed modification...")
        
        SPEED_PROMPT = "Say the following very fast but still be intelligible"
        SPEED_TEXT = "Availability and terms may vary. Check our website or your local store for complete details."
        
        response_fast = client.synthesize_speech(
            input=texttospeech.SynthesisInput(
                text=SPEED_TEXT,
                prompt=SPEED_PROMPT
            ),
            voice=texttospeech.VoiceSelectionParams(
                language_code=LANGUAGE_CODE,
                name=VOICE,
                model=MODEL
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
        )
        
        # Save speed-modified audio
        speed_file = "/tmp/gemini_tts_fast.mp3"
        with open(speed_file, "wb") as out:
            out.write(response_fast.audio_content)
        
        print(f"✅ Speed-modified synthesis successful! Saved to: {speed_file}")
        print(f"📊 Audio size: {len(response_fast.audio_content)} bytes")
        
        # Try to play the audio files
        print("\n🔊 Playing audio files...")
        for audio_file, description in [
            (basic_file, "Basic synthesis"),
            (prompt_file, "Emotion prompt"),
            (speed_file, "Fast speech")
        ]:
            print(f"🎵 {description}: {audio_file}")
            try:
                # Try different audio players
                for player in ["mpg123", "ffplay"]:
                    result = subprocess.run(["which", player], capture_output=True)
                    if result.returncode == 0:
                        if player == "ffplay":
                            subprocess.run([player, "-nodisp", "-autoexit", audio_file], 
                                         check=False, capture_output=True)
                        else:
                            subprocess.run([player, audio_file], 
                                         check=False, capture_output=True)
                        print(f"   ✅ Played with {player}")
                        break
                else:
                    print("   🔇 No audio player available")
                    
            except Exception as e:
                print(f"   ❌ Playback error: {e}")
        
        print("\n🎉 All Gemini TTS tests completed successfully!")
        print("📝 Summary:")
        print(f"   • Basic synthesis: {basic_file}")
        print(f"   • Emotion prompt: {prompt_file}")
        print(f"   • Speed control: {speed_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini TTS test failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Additional debugging
        import traceback
        print("🐛 Full traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("🚀 Gemini TTS Test - Colab Notebook Style")
    print("=" * 60)
    print("📖 Following: get_started_with_gemini_tts_voices.ipynb")
    print("=" * 60)
    
    success = test_gemini_tts_colab_style()
    
    print("=" * 60)
    if success:
        print("✅ Gemini TTS working perfectly!")
        print("🔧 Ready to integrate into main AI Guard Agent system")
    else:
        print("❌ Gemini TTS test failed!")
        print("\n🔧 Next steps:")
        print("   1. Ensure gcloud CLI is installed")
        print("   2. Run: gcloud auth application-default login")
        print("   3. Verify project has Text-to-Speech API enabled")
        print("   4. Check quota and billing settings")