#!/usr/bin/env python3
"""
Gemini TTS using direct HTTP API
Following the n8n approach with direct API calls
"""

import os
import json
import base64
import requests
import tempfile
import subprocess

def test_gemini_tts_direct_api():
    """Test Gemini TTS using direct HTTP API calls"""
    
    # Get API key
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Try different Gemini TTS models
    models = [
        "gemini-2.5-pro-preview-tts",
        "gemini-2.5-flash-preview-tts"
    ]
    
    for model in models:
        print(f"\n🎤 Testing model: {model}")
        
        # API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateSpeech?key={api_key}"
        
        # Headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Test different configurations
        configs = [
            {
                "name": "Basic Text",
                "data": {
                    "text": "Hello world! This is Gemini TTS speaking using direct API calls.",
                    "audioConfig": {
                        "speakingRate": 1.0,
                        "voice": {
                            "name": "en-US-Standard-B"
                        }
                    }
                }
            },
            {
                "name": "Custom Voice",
                "data": {
                    "text": "This is a test with a different voice configuration.",
                    "audioConfig": {
                        "speakingRate": 1.2,
                        "voice": {
                            "name": "en-US-Wavenet-D"
                        }
                    }
                }
            },
            {
                "name": "Gemini Voice",
                "data": {
                    "text": "Testing with Gemini-specific voice parameters.",
                    "audioConfig": {
                        "speakingRate": 1.0,
                        "voice": {
                            "name": "Aoede"  # Gemini TTS voice
                        }
                    }
                }
            }
        ]
        
        for config in configs:
            print(f"  🧪 Testing: {config['name']}")
            
            try:
                # Make the API request
                response = requests.post(url, headers=headers, json=config['data'])
                
                print(f"    📡 Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Parse response
                    result = response.json()
                    
                    if 'audioContent' in result:
                        # Decode base64 audio
                        audio_data = base64.b64decode(result['audioContent'])
                        
                        # Save audio file
                        filename = f"/tmp/{model}_{config['name'].replace(' ', '_').lower()}.mp3"
                        with open(filename, 'wb') as f:
                            f.write(audio_data)
                        
                        print(f"    ✅ Success! Audio saved: {filename}")
                        print(f"    📊 Audio size: {len(audio_data)} bytes")
                        
                        # Try to play the audio
                        try:
                            for player in ["mpg123", "ffplay"]:
                                result_check = subprocess.run(["which", player], capture_output=True)
                                if result_check.returncode == 0:
                                    if player == "ffplay":
                                        subprocess.run([player, "-nodisp", "-autoexit", filename], 
                                                     check=False, capture_output=True)
                                    else:
                                        subprocess.run([player, filename], 
                                                     check=False, capture_output=True)
                                    print(f"    🔊 Played with {player}")
                                    break
                            else:
                                print("    🔇 No audio player available")
                        except Exception as e:
                            print(f"    ❌ Playback error: {e}")
                        
                        return True  # Success! We got working audio
                        
                    else:
                        print(f"    ❌ No audioContent in response: {result}")
                        
                else:
                    print(f"    ❌ API Error: {response.text}")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {e}")
    
    return False

def test_gemini_speech_with_prompt():
    """Test Gemini TTS with prompt-based generation"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found")
        return False
    
    print("\n🎭 Testing prompt-based speech generation...")
    
    # Try the generateContent endpoint with audio response modality
    model = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Request with AUDIO response modality
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Say 'Hello world, this is Gemini TTS!' in a cheerful, friendly voice."
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"]
        }
    }
    
    try:
        print(f"🌐 Making request to: {url}")
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received: {list(result.keys())}")
            
            # Look for audio content
            if 'candidates' in result:
                for i, candidate in enumerate(result['candidates']):
                    print(f"  📄 Candidate {i}: {list(candidate.keys())}")
                    
                    if 'content' in candidate:
                        content = candidate['content']
                        if 'parts' in content:
                            for j, part in enumerate(content['parts']):
                                print(f"    🧩 Part {j}: {list(part.keys())}")
                                
                                if 'inlineData' in part:
                                    inline_data = part['inlineData']
                                    if 'data' in inline_data:
                                        # Decode audio
                                        audio_data = base64.b64decode(inline_data['data'])
                                        
                                        # Save audio
                                        filename = f"/tmp/gemini_prompt_audio.mp3"
                                        with open(filename, 'wb') as f:
                                            f.write(audio_data)
                                        
                                        print(f"    ✅ Audio saved: {filename}")
                                        print(f"    📊 Size: {len(audio_data)} bytes")
                                        print(f"    🎵 MIME: {inline_data.get('mimeType', 'unknown')}")
                                        
                                        return True
            
            print(f"❌ No audio content found in response")
            
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 Gemini TTS Direct HTTP API Test")
    print("=" * 50)
    
    # Test 1: Direct speech synthesis
    success1 = test_gemini_tts_direct_api()
    
    # Test 2: Prompt-based generation
    success2 = test_gemini_speech_with_prompt()
    
    print("=" * 50)
    if success1 or success2:
        print("✅ Gemini TTS working with direct API!")
        print("🔧 Ready to integrate into AI Guard Agent")
    else:
        print("❌ Both API approaches failed")
        print("🔍 Check API key and model availability")