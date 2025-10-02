#!/usr/bin/env python3
"""
Test Gemini TTS using different approaches
"""

import os
import tempfile
import google.generativeai as genai

def test_gemini_ai_sdk_approach():
    """Test using Gemini AI SDK directly for TTS"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GOOGLE_GEMINI_API_KEY environment variable")
        return False
    
    try:
        # Configure Gemini AI
        genai.configure(api_key=api_key)
        
        # Try different model configurations
        tts_models = [
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-pro-preview-tts"
        ]
        
        for model_name in tts_models:
            print(f"\n🧪 Testing model: {model_name}")
            
            try:
                model = genai.GenerativeModel(model_name)
                
                # Test if the model supports TTS-specific configurations
                print(f"✅ Model '{model_name}' loaded successfully")
                
                # Try generating content with different approaches
                text = "Hello, this is a security guard speaking."
                
                # Approach 1: Simple text input
                try:
                    print("   🔄 Trying simple text input...")
                    response = model.generate_content(text)
                    print(f"   📝 Response type: {type(response)}")
                    print(f"   📋 Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                    
                    if hasattr(response, 'parts') and response.parts:
                        print(f"   📦 Found {len(response.parts)} parts")
                        for i, part in enumerate(response.parts):
                            print(f"      Part {i}: {type(part)}")
                            if hasattr(part, 'inline_data'):
                                print(f"         Has inline_data: {part.inline_data}")
                                if part.inline_data and hasattr(part.inline_data, 'mime_type'):
                                    print(f"         MIME type: {part.inline_data.mime_type}")
                
                except Exception as e:
                    print(f"   ❌ Simple approach failed: {e}")
                
                # Approach 2: TTS-style prompt
                try:
                    print("   🔄 Trying TTS-style prompt...")
                    tts_prompt = f"Convert the following text to speech as a professional security guard: {text}"
                    response = model.generate_content(tts_prompt)
                    print(f"   ✅ TTS-style prompt worked")
                    
                except Exception as e:
                    print(f"   ❌ TTS-style prompt failed: {e}")
                
            except Exception as e:
                print(f"❌ Model '{model_name}' failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_available_models():
    """List available models and their capabilities"""
    
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GOOGLE_GEMINI_API_KEY environment variable")
        return False
    
    try:
        genai.configure(api_key=api_key)
        
        print("📋 Available models:")
        models = list(genai.list_models())
        
        for model in models:
            if 'tts' in model.name.lower():
                print(f"🎤 {model.name}")
                print(f"   Methods: {model.supported_generation_methods}")
                print(f"   Description: {getattr(model, 'description', 'No description')}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini TTS - Different Approaches")
    print("=" * 60)
    
    print("\n1. Testing available models:")
    test_available_models()
    
    print("\n2. Testing Gemini AI SDK approach:")
    test_gemini_ai_sdk_approach()