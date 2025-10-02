#!/usr/bin/env python3
"""
Gemini TTS test using proper Google Cloud authentication
Following the official Colab notebook pattern
"""

import os
import tempfile
import subprocess
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth

def setup_authentication():
    """Set up authentication for Google Cloud TTS"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    project_id = os.environ.get("GEMINI_PROJECT_ID")
    
    if not api_key or not project_id:
        print("❌ Missing GOOGLE_GEMINI_API_KEY or GEMINI_PROJECT_ID")
        return None, None
    
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"📋 Project ID: {project_id}")
    
    # Set the project ID in environment
    os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
    
    # Method 1: Try creating a simple credentials object
    try:
        # Create a minimal credentials setup
        from google.oauth2 import service_account
        
        # Try to use API key as a token (this may not work but worth trying)
        print("🔧 Attempting to create credentials...")
        
        # Actually, let's try the direct approach from Colab
        # In Colab, they use service account or user credentials
        
        # Let's try using the google.auth.default() with some environment setup
        credentials, current_project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        print(f"✅ Credentials obtained for project: {current_project}")
        return credentials, project_id
        
    except Exception as e:
        print(f"❌ Authentication setup failed: {e}")
        
        # Try alternative: create a temporary service account-like structure
        print("🔄 Trying alternative authentication...")
        
        # This is a workaround - create minimal credential structure
        try:
            import json
            temp_creds = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": "dummy",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDummy\n-----END PRIVATE KEY-----\n",
                "client_email": f"dummy@{project_id}.iam.gserviceaccount.com",
                "client_id": "dummy",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
            
            # Write temporary service account file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(temp_creds, f)
                temp_file = f.name
            
            # Set environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file
            
            # Try again
            credentials, current_project = google.auth.default()
            print(f"✅ Alternative credentials created for: {current_project}")
            return credentials, project_id
            
        except Exception as e2:
            print(f"❌ Alternative authentication also failed: {e2}")
            return None, None

def test_gemini_tts_with_auth():
    """Test Gemini TTS with proper authentication"""
    
    print("🔐 Setting up authentication...")
    credentials, project_id = setup_authentication()
    
    if not credentials:
        print("❌ Could not set up authentication")
        print("\n💡 To fix this, you need to:")
        print("   1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install")
        print("   2. Run: gcloud auth application-default login")
        print("   3. Or set up a service account JSON file")
        return False
    
    try:
        print("🏗️  Creating TTS client...")
        
        # Create client with credentials
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        
        print("🗣️  Testing synthesis...")
        
        # Create synthesis input
        synthesis_input = texttospeech.SynthesisInput(text="Hello world! This is Gemini TTS speaking.")
        
        # Try Gemini voice configuration
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="gemini-2.5-flash-preview-tts"  # Try the Gemini TTS model
        )
        
        # Audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        print("🎙️  Synthesizing speech with Gemini TTS...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save the audio
        output_file = "/tmp/gemini_tts_hello.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"✅ Success! Audio saved to: {output_file}")
        
        # Get file size
        file_size = os.path.getsize(output_file)
        print(f"📊 Audio file size: {file_size} bytes")
        
        # Try to play it
        try:
            result = subprocess.run(["which", "mpg123"], capture_output=True, text=True)
            if result.returncode == 0:
                subprocess.run(["mpg123", output_file], check=False)
                print("🔊 Audio played with mpg123")
            else:
                result2 = subprocess.run(["which", "ffplay"], capture_output=True, text=True)
                if result2.returncode == 0:
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", output_file], check=False)
                    print("🔊 Audio played with ffplay")
                else:
                    print("🔇 No audio player found (mpg123 or ffplay)")
        except Exception as e:
            print(f"🔇 Could not play audio: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS synthesis failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Try with standard voice as fallback
        try:
            print("🔄 Trying with standard voice...")
            
            standard_voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Standard-A"
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=standard_voice,
                audio_config=audio_config
            )
            
            output_file = "/tmp/standard_tts_hello.mp3"
            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            
            print(f"✅ Standard TTS works! Audio saved to: {output_file}")
            print("❌ But Gemini TTS model is not available")
            return False
            
        except Exception as e2:
            print(f"❌ Even standard TTS failed: {e2}")
            return False

if __name__ == "__main__":
    print("🚀 Testing Gemini TTS with Authentication")
    print("=" * 60)
    success = test_gemini_tts_with_auth()
    print("=" * 60)
    if success:
        print("✅ Gemini TTS test completed successfully!")
    else:
        print("❌ Gemini TTS test failed!")
        print("\n🔧 Troubleshooting tips:")
        print("   • Check if you have proper Google Cloud credentials")
        print("   • Verify the Gemini TTS model name is correct")
        print("   • Ensure your project has TTS API enabled")