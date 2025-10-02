"""
LLM Configuration Module
Handles configuration and setup for Large Language Model integration
"""

import os
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

class LLMConfig:
    """Configuration manager for LLM integration"""
    
    def __init__(self):
        """Initialize LLM configuration"""
        # Load environment variables
        load_dotenv()
        
        # Configuration settings
        self.api_key: Optional[str] = None
        self.model_name: str = "gemini-2.5-flash"  # Fast text generation
        self.tts_model_name: str = "gemini-2.5-flash-preview-tts"  # Audio generation
        self.temperature: float = 0.7  # Creativity level (0.0-1.0)
        self.max_tokens: int = 150  # Response length limit
        self.timeout_seconds: int = 10  # API timeout
        
        # Guard agent personality settings
        self.agent_name: str = "Guardian AI"
        self.agent_personality: str = "professional, authoritative, but polite"
        
        # Initialize the LLM
        self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize the LLM with API key"""
        try:
            # Get API key from environment variable
            self.api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
            
            if not self.api_key:
                # For development, try alternative names
                self.api_key = os.getenv('GEMINI_API_KEY')
                
            if not self.api_key:
                print("⚠️  Warning: No Gemini API key found.")
                print("   Please set GOOGLE_GEMINI_API_KEY environment variable")
                print("   Get your free API key at: https://makersuite.google.com/app/apikey")
                return
            
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            print("✅ Gemini LLM configured successfully")
            
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
            self.api_key = None
    
    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return self.api_key is not None
    
    def get_model_instance(self):
        """Get configured Gemini model instance for text generation"""
        if not self.is_configured():
            raise RuntimeError("LLM not properly configured. Check API key.")
        
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to create model instance: {e}")
    
    def get_tts_model_instance(self):
        """Get configured Gemini TTS model instance for audio generation"""
        if not self.is_configured():
            raise RuntimeError("LLM not properly configured. Check API key.")
        
        try:
            model = genai.GenerativeModel(
                model_name=self.tts_model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                )
            )
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to create TTS model instance: {e}")
    
    def update_personality(self, personality: str) -> None:
        """Update agent personality"""
        self.agent_personality = personality
    
    def update_temperature(self, temperature: float) -> None:
        """Update response creativity (0.0-1.0)"""
        if 0.0 <= temperature <= 1.0:
            self.temperature = temperature
        else:
            raise ValueError("Temperature must be between 0.0 and 1.0")


# Global configuration instance
llm_config = LLMConfig()