#!/usr/bin/env python3
"""
Test Gemini TTS with proper audio handling and playback
"""

import os
import requests
import base64
import subprocess
import tempfile

def test_gemini_tts_with_playback():
    """Test Gemini TTS and play the audio properly"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found")
        return False
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Test with a simple, clear sentence
    test_text = "Hello! This is a test of Gemini TTS. Can you hear me clearly?"
    
    print(f"🗣️  Testing with text: '{test_text}'")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": test_text
            }]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"]
        }
    }
    
    try:
        print("📡 Making API request...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ API request successful!")
            
            # Extract audio data
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                candidate = response_data['candidates'][0]
                
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    
                    for i, part in enumerate(parts):
                        if 'inlineData' in part:
                            inline_data = part['inlineData']
                            print(f"🎵 Found audio data in part {i}")
                            print(f"📋 MIME type: {inline_data.get('mimeType', 'unknown')}")
                            
                            # Get the base64 data
                            audio_b64 = inline_data.get('data', '')
                            print(f"📊 Base64 data length: {len(audio_b64)}")
                            
                            if audio_b64:
                                try:
                                    # Decode base64 to bytes
                                    audio_bytes = base64.b64decode(audio_b64)
                                    print(f"📊 Decoded audio bytes: {len(audio_bytes)}")
                                    
                                    # Determine file extension from MIME type
                                    mime_type = inline_data.get('mimeType', '')
                                    if 'wav' in mime_type:
                                        ext = '.wav'
                                    elif 'mp3' in mime_type:
                                        ext = '.mp3'
                                    elif 'mpeg' in mime_type:
                                        ext = '.mp3'
                                    else:
                                        ext = '.wav'  # Default
                                    
                                    # Save to file
                                    audio_file = f"/tmp/gemini_tts_test{ext}"
                                    with open(audio_file, 'wb') as f:
                                        f.write(audio_bytes)
                                    
                                    print(f"💾 Audio saved to: {audio_file}")
                                    
                                    # Verify file
                                    file_info = subprocess.run(['file', audio_file], 
                                                             capture_output=True, text=True)
                                    print(f"📋 File type: {file_info.stdout.strip()}")
                                    
                                    # Try multiple audio players
                                    players = [
                                        ['ffplay', '-nodisp', '-autoexit'],
                                        ['mpv', '--no-video'],
                                        ['aplay'],
                                        ['paplay']
                                    ]
                                    
                                    played = False
                                    for player_cmd in players:
                                        try:
                                            # Check if player exists
                                            which_result = subprocess.run(['which', player_cmd[0]], 
                                                                        capture_output=True)
                                            if which_result.returncode == 0:
                                                print(f"🔊 Trying to play with {player_cmd[0]}...")
                                                
                                                # Play the audio
                                                play_result = subprocess.run(
                                                    player_cmd + [audio_file],
                                                    capture_output=True,
                                                    timeout=10
                                                )
                                                
                                                if play_result.returncode == 0:
                                                    print(f"✅ Successfully played with {player_cmd[0]}!")
                                                    played = True
                                                    break
                                                else:
                                                    print(f"❌ {player_cmd[0]} failed: {play_result.stderr.decode()}")
                                        
                                        except subprocess.TimeoutExpired:
                                            print(f"✅ {player_cmd[0]} is playing (timed out after 10s)")
                                            played = True
                                            break
                                        except Exception as e:
                                            print(f"❌ Error with {player_cmd[0]}: {e}")
                                    
                                    if not played:
                                        print("🔇 No audio player worked, but audio file was created successfully")
                                        print(f"🔗 Try playing manually: mpv {audio_file}")
                                    
                                    return True
                                    
                                except Exception as e:
                                    print(f"❌ Error decoding audio: {e}")
                                    return False
                        
                        elif 'text' in part:
                            print(f"📝 Text part: {part['text'][:100]}")
                
                print("❌ No audio data found in response")
                return False
            
            else:
                print("❌ No candidates in response")
                return False
        
        elif response.status_code == 429:
            print("⚠️  Rate limited - try again later")
            return False
        
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Gemini TTS Audio Test with Playback")
    print("=" * 50)
    
    success = test_gemini_tts_with_playback()
    
    print("=" * 50)
    if success:
        print("✅ Gemini TTS audio test completed!")
    else:
        print("❌ Gemini TTS audio test failed!")