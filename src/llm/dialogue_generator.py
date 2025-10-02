"""
Dialogue Generator Module
Handles intelligent dialogue generation using LLM
"""

from typing import Optional, Dict, Any
import time
import google.generativeai as genai
from .llm_config import llm_config

class DialogueGenerator:
    """Generates intelligent dialogue responses using LLM"""
    
    def __init__(self):
        """Initialize dialogue generator"""
        self.config = llm_config
        self.model = None
        self.conversation_history = []
        self.last_response_time = 0.0
        
        # Initialize model if configured
        if self.config.is_configured():
            try:
                self.model = self.config.get_model_instance()
                print("✅ Dialogue generator initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize dialogue generator: {e}")
                self.model = None
        else:
            print("⚠️  Dialogue generator initialized without LLM (API key missing)")
    
    def is_available(self) -> bool:
        """Check if dialogue generation is available"""
        return self.model is not None
    
    def generate_response(self, 
                         prompt: str, 
                         escalation_level: int = 1,
                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response based on prompt and escalation level
        
        Args:
            prompt: The base prompt or situation description
            escalation_level: Escalation level (1-4)
            context: Additional context information
            
        Returns:
            Generated response string
        """
        if not self.is_available():
            return self._get_fallback_response(escalation_level)
        
        try:
            # Build the complete prompt
            full_prompt = self._build_prompt(prompt, escalation_level, context)
            
            # Track response time
            start_time = time.time()
            
            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            # Record response time
            self.last_response_time = time.time() - start_time
            
            # Extract and clean the response text
            response_text = response.text.strip()
            
            # Add to conversation history
            self.conversation_history.append({
                'prompt': prompt,
                'escalation_level': escalation_level,
                'response': response_text,
                'timestamp': time.time()
            })
            
            return response_text
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return self._get_fallback_response(escalation_level)
    
    def _build_prompt(self, 
                     base_prompt: str, 
                     escalation_level: int,
                     context: Optional[Dict[str, Any]] = None) -> str:
        """Build complete prompt with personality and escalation context"""
        
        # Define escalation personalities
        escalation_personalities = {
            1: "polite and curious, asking for identification in a friendly manner",
            2: "more firm and authoritative, requesting the person to identify themselves or leave",
            3: "stern and warning, making it clear this is trespassing and they must leave",
            4: "urgent and alarming, indicating security has been notified"
        }
        
        # Base system prompt
        system_prompt = f"""You are {self.config.agent_name}, an AI security guard for a residential room. 
Your personality is {self.config.agent_personality}.

Current situation: An unrecognized person has been detected in the room.
Escalation level: {escalation_level}/4

Your response style should be: {escalation_personalities.get(escalation_level, 'professional')}

Guidelines:
- Keep responses under 20 words for Level 1-2, under 30 words for Level 3-4
- Be direct and clear
- Maintain authority while being appropriate for the escalation level
- Do not make threats of violence
- Focus on requesting identification or asking them to leave

Context: {base_prompt}"""

        # Add conversation context if available
        if context:
            system_prompt += f"\nAdditional context: {context}"
        
        return system_prompt
    
    def _get_fallback_response(self, escalation_level: int) -> str:
        """Get fallback response when LLM is unavailable"""
        fallback_responses = {
            1: "Hello, I don't recognize you. Could you please identify yourself?",
            2: "Please state your business here or leave the premises immediately.",
            3: "You are trespassing on private property. Leave now or security will be contacted.",
            4: "INTRUDER ALERT! You must leave immediately. Security has been notified!"
        }
        return fallback_responses.get(escalation_level, fallback_responses[1])
    
    def get_conversation_history(self) -> list:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def get_last_response_time(self) -> float:
        """Get last response generation time in seconds"""
        return self.last_response_time
    
    def test_connection(self) -> bool:
        """Test LLM connection with a simple query"""
        if not self.is_available():
            return False
        
        try:
            test_response = self.generate_response("Say hello", escalation_level=1)
            return len(test_response) > 0
        except Exception as e:
            print(f"❌ LLM connection test failed: {e}")
            return False


# Global dialogue generator instance
dialogue_generator = DialogueGenerator()