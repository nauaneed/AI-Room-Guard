#!/usr/bin/env python3
"""
Simple Hello World test for Gemini TTS
Based on the official Colab notebook example
"""

import os
import tempfile
from google.api_core.client_options import ClientOptions
from google.cloud import texttospeech_v1beta1 as texttospeech

# Optional IPython imports for Jupyter environments
try:
    from IPython.display import Audio, display
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

def test_gemini_tts_hello_world():
    """Test basic Gemini TTS functionality"""
    
    # Check for API key first
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GOOGLE_GEMINI_API_KEY environment variable")
        return False
    
    # Set up project information
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GEMINI_PROJECT_ID")
    if not PROJECT_ID:
        print("❌ Please set GOOGLE_CLOUD_PROJECT or GEMINI_PROJECT_ID environment variable")
        return False
    
    TTS_LOCATION = "global"
    
    print(f"🔑 API Key found: {api_key[:10]}...")
    print(f"📋 Using Project ID: {PROJECT_ID}")
    print(f"📍 Using Location: {TTS_LOCATION}")
    
    try:
        # Set authentication environment variables
        os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID
        
        # Create a temporary service account credentials JSON for API key auth
        import json
        import tempfile
        
        # Create minimal credentials structure
        creds_data = {
            "type": "service_account",
            "project_id": PROJECT_ID,
            "private_key_id": "1",
            "private_key": f"-----BEGIN PRIVATE KEY-----\n{api_key}\n-----END PRIVATE KEY-----\n",
            "client_email": f"gemini-tts@{PROJECT_ID}.iam.gserviceaccount.com",
            "client_id": "1",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as creds_file:
            json.dump(creds_data, creds_file)
            creds_path = creds_file.name
        
        # Set the credentials environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        # Set up the API endpoint and client
        API_ENDPOINT = (
            f"{TTS_LOCATION}-texttospeech.googleapis.com"
            if TTS_LOCATION != "global"
            else "texttospeech.googleapis.com"
        )
        
        print(f"🌐 API Endpoint: {API_ENDPOINT}")
        
        # Create the TTS client
        client = texttospeech.TextToSpeechClient(
            client_options=ClientOptions(api_endpoint=API_ENDPOINT)
        )
        
        print("✅ TTS Client created successfully")
        
        # Configure Gemini TTS settings
        MODEL = "gemini-2.5-flash-preview-tts"
        VOICE = "Fenrir"  # Authoritative male voice for security guard
        LANGUAGE_CODE = "en-US"
        
        # Test text and prompt
        TEXT = "Hello, this is a test of Gemini TTS. I am a security guard AI."
        PROMPT = "Speak as a professional security guard - authoritative, clear, and firm but polite"
        
        print(f"🎭 Model: {MODEL}")
        print(f"🗣️  Voice: {VOICE}")
        print(f"🌍 Language: {LANGUAGE_CODE}")
        print(f"📝 Text: {TEXT}")
        print(f"💭 Prompt: {PROMPT}")
        
        # Configure the voice
        voice = texttospeech.VoiceConfig(
            name=VOICE,
            model=MODEL,
            language_code=LANGUAGE_CODE
        )
        
        # Create synthesis input with prompt
        synthesis_input = texttospeech.SynthesisInput(
            text=TEXT,
            prompt=PROMPT
        )
        
        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        print("🔄 Generating speech...")
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        print("✅ Speech generated successfully!")
        
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(response.audio_content)
            audio_file_path = tmp_file.name
        
        print(f"💾 Audio saved to: {audio_file_path}")
        
        # Try to play the audio (if in Jupyter/Colab environment)
        if IPYTHON_AVAILABLE:
            try:
                display(Audio(response.audio_content))
                print("🔊 Audio displayed (if in Jupyter environment)")
            except:
                print("📱 Not in Jupyter environment - audio saved to file")
        else:
            print("📱 IPython not available - audio saved to file")
        
        # Clean up temporary credentials file
        try:
            os.unlink(creds_path)
            print("🧹 Cleaned up temporary credentials file")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Clean up temporary credentials file on error
        try:
            os.unlink(creds_path)
        except:
            pass
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini TTS Hello World")
    print("=" * 50)
    
    success = test_gemini_tts_hello_world()
    
    if success:
        print("🎉 Gemini TTS test successful!")
    else:
        print("💥 Gemini TTS test failed!")