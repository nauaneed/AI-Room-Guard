#!/usr/bin/env python3
"""
Simple Gemini TTS test using correct API endpoint
Focusing on the working generateContent approach
"""

import os
import json
import base64
import requests
import tempfile
import subprocess
import time

def test_gemini_audio_generation():
    """Test Gemini audio generation with minimal request"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Use the working endpoint from previous test
    model = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Minimal request for audio generation
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Hello! This is a test of Gemini TTS."
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"]
        }
    }
    
    print(f"🌐 Making request to: {url}")
    print(f"📝 Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response keys: {list(result.keys())}")
            
            # Parse the response for audio content
            if 'candidates' in result:
                for i, candidate in enumerate(result['candidates']):
                    print(f"  📄 Candidate {i}:")
                    
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for j, part in enumerate(candidate['content']['parts']):
                            print(f"    🧩 Part {j}: {list(part.keys())}")
                            
                            if 'inlineData' in part:
                                inline_data = part['inlineData']
                                mime_type = inline_data.get('mimeType', 'unknown')
                                data_b64 = inline_data.get('data', '')
                                
                                print(f"    🎵 Found audio: {mime_type}")
                                print(f"    📊 Data length: {len(data_b64)} chars")
                                
                                if data_b64:
                                    # Decode and save audio
                                    try:
                                        audio_data = base64.b64decode(data_b64)
                                        
                                        # Determine file extension from MIME type
                                        ext = "mp3"
                                        if "wav" in mime_type.lower():
                                            ext = "wav"
                                        elif "ogg" in mime_type.lower():
                                            ext = "ogg"
                                        
                                        filename = f"/tmp/gemini_tts_success.{ext}"
                                        with open(filename, 'wb') as f:
                                            f.write(audio_data)
                                        
                                        print(f"    ✅ Audio saved: {filename}")
                                        print(f"    � Audio size: {len(audio_data)} bytes")
                                        
                                        # Try to play
                                        try:
                                            for player in ["mpg123", "ffplay", "aplay"]:
                                                result_check = subprocess.run(["which", player], capture_output=True)
                                                if result_check.returncode == 0:
                                                    if player == "ffplay":
                                                        subprocess.run([player, "-nodisp", "-autoexit", filename], 
                                                                     check=False, capture_output=True, timeout=10)
                                                    elif player == "aplay" and ext == "wav":
                                                        subprocess.run([player, filename], 
                                                                     check=False, capture_output=True, timeout=10)
                                                    elif player == "mpg123" and ext == "mp3":
                                                        subprocess.run([player, filename], 
                                                                     check=False, capture_output=True, timeout=10)
                                                    else:
                                                        continue
                                                    print(f"    🔊 Played with {player}")
                                                    break
                                            else:
                                                print("    🔇 No compatible audio player found")
                                        except Exception as e:
                                            print(f"    🔇 Playback error: {e}")
                                        
                                        return True
                                        
                                    except Exception as e:
                                        print(f"    ❌ Failed to decode audio: {e}")
            
            print("❌ No audio content found in response")
            return False
            
        elif response.status_code == 429:
            error_data = response.json()
            if 'error' in error_data and 'details' in error_data['error']:
                for detail in error_data['error']['details']:
                    if detail.get('@type') == 'type.googleapis.com/google.rpc.RetryInfo':
                        retry_delay = detail.get('retryDelay', '60s')
                        print(f"⏰ Quota exceeded. Retry after: {retry_delay}")
                        
                        # Extract seconds from delay string
                        if 's' in retry_delay:
                            delay_seconds = float(retry_delay.replace('s', ''))
                            if delay_seconds <= 60:  # Only wait if reasonable
                                print(f"⏳ Waiting {delay_seconds} seconds...")
                                time.sleep(delay_seconds + 1)
                                
                                # Retry once
                                print("🔄 Retrying request...")
                                return test_gemini_audio_generation()
            
            print(f"❌ Quota exceeded: {response.text}")
            return False
            
        else:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_quota_status():
    """Check current quota status"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        return
    
    print("� Checking quota status...")
    
    # Try a simple list models request to check API status
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        response = requests.get(url)
        print(f"� Models API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'models' in result:
                tts_models = [m for m in result['models'] if 'tts' in m.get('name', '').lower()]
                print(f"🎤 Available TTS models: {len(tts_models)}")
                for model in tts_models[:3]:  # Show first 3
                    print(f"  • {model.get('name', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Quota check failed: {e}")

if __name__ == "__main__":
    print("🚀 Gemini TTS Simple Test")
    print("=" * 40)
    
    # Check quota first
    check_quota_status()
    
    print("\n" + "=" * 40)
    
    # Test audio generation
    success = test_gemini_audio_generation()
    
    print("=" * 40)
    if success:
        print("✅ Gemini TTS working!")
        print("🎉 Ready to integrate into AI Guard Agent")
    else:
        print("❌ Gemini TTS test failed")
        print("💡 Try again later if quota exceeded")