"""
Response Generator Module
Handles intelligent dialogue generation with escalation context
"""

import time
from typing import Dict, Any, Optional
from .escalation_manager import escalation_manager, EscalationLevel
import sys
import os

# Add LLM module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from llm import dialogue_generator

class ResponseGenerator:
    """Generates contextual responses using LLM and escalation context"""
    
    def __init__(self):
        """Initialize response generator"""
        self.llm = dialogue_generator
        self.escalation = escalation_manager
        self.response_cache = {}  # Cache responses to avoid repetition
        self.conversation_memory = []  # Track conversation flow
        
        # Response variation settings
        self.max_cached_responses = 50
        self.variation_threshold = 3  # Generate new response after 3 similar requests
        
        print("✅ Response generator initialized")
    
    def generate_response(self, 
                         context: Optional[Dict[str, Any]] = None,
                         force_new: bool = False) -> str:
        """
        Generate an intelligent response based on current escalation context
        
        Args:
            context: Additional context information
            force_new: Force generation of new response (ignore cache)
            
        Returns:
            Generated response string
        """
        # Get current escalation context
        escalation_context = self.escalation.get_escalation_context()
        
        if not escalation_context:
            return "Hello, may I help you?"
        
        # Build comprehensive prompt context
        prompt_context = self._build_prompt_context(escalation_context, context)
        
        # Check cache for similar responses (unless forcing new)
        if not force_new:
            cached_response = self._get_cached_response(prompt_context)
            if cached_response:
                return cached_response
        
        # Generate new response using LLM
        response = self._generate_new_response(prompt_context)
        
        # Cache the response
        self._cache_response(prompt_context, response)
        
        # Add to conversation memory
        self._add_to_memory(prompt_context, response)
        
        return response
    
    def _build_prompt_context(self, 
                             escalation_context: Dict[str, Any],
                             additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build comprehensive context for prompt generation"""
        
        level_info = escalation_context.get('level_info', {})
        current_level = escalation_context.get('current_level', 1)
        
        # Base context from escalation
        context = {
            'escalation_level': current_level,
            'tone': level_info.get('tone', 'professional'),
            'max_words': level_info.get('max_response_words', 20),
            'urgency': level_info.get('urgency', 'low'),
            'conversation_duration': escalation_context.get('conversation_duration', 0),
            'escalation_count': escalation_context.get('escalation_count', 0),
            'should_escalate_soon': escalation_context.get('should_escalate_soon', False)
        }
        
        # Add conversation history context
        if self.conversation_memory:
            recent_responses = [entry['response'] for entry in self.conversation_memory[-3:]]
            context['recent_responses'] = recent_responses
        
        # Add additional context if provided
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _generate_new_response(self, context: Dict[str, Any]) -> str:
        """Generate a new response using LLM"""
        
        # Build the situation description
        situation = self._build_situation_description(context)
        
        # Generate response using dialogue_generator
        try:
            response = self.llm.generate_response(
                prompt=situation,
                escalation_level=context['escalation_level'],
                context=context
            )
            
            # Clean and validate response
            response = self._clean_response(response, context)
            
            return response
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return self._get_fallback_response(context['escalation_level'])
    
    def _build_situation_description(self, context: Dict[str, Any]) -> str:
        """Build situation description for LLM prompt"""
        
        level = context['escalation_level']
        duration = context['conversation_duration']
        escalation_count = context['escalation_count']
        
        # Base situation
        situation = "An unrecognized person has been detected in a private residential room."
        
        # Add timing context
        if duration > 30:
            situation += f" The person has been present for {duration:.0f} seconds."
        
        # Add escalation context
        if escalation_count > 0:
            situation += f" This is escalation attempt #{escalation_count + 1}."
        
        # Add urgency context
        if context.get('should_escalate_soon'):
            situation += " The situation requires immediate response."
        
        # Add recent conversation context
        if context.get('recent_responses'):
            situation += " Previous attempts to communicate have been made."
        
        return situation
    
    def _clean_response(self, response: str, context: Dict[str, Any]) -> str:
        """Clean and validate the generated response"""
        
        # Remove extra whitespace and quotes
        response = response.strip().strip('"\'')
        
        # Ensure it ends with appropriate punctuation
        if not response.endswith(('.', '!', '?')):
            urgency = context.get('urgency', 'low')
            if urgency in ['high', 'critical']:
                response += '!'
            else:
                response += '.'
        
        # Check word count limit
        max_words = context.get('max_words', 30)
        words = response.split()
        if len(words) > max_words:
            # Truncate and add appropriate ending
            response = ' '.join(words[:max_words])
            if not response.endswith(('.', '!', '?')):
                response += '.'
        
        return response
    
    def _get_cached_response(self, context: Dict[str, Any]) -> Optional[str]:
        """Check cache for similar response"""
        
        # Create cache key based on level and key context elements
        cache_key = f"level_{context['escalation_level']}_urgency_{context.get('urgency', 'low')}"
        
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            
            # Check if we've used this response too recently
            if cached_data['usage_count'] < self.variation_threshold:
                cached_data['usage_count'] += 1
                cached_data['last_used'] = time.time()
                return cached_data['response']
        
        return None
    
    def _cache_response(self, context: Dict[str, Any], response: str) -> None:
        """Cache the generated response"""
        
        cache_key = f"level_{context['escalation_level']}_urgency_{context.get('urgency', 'low')}"
        
        self.response_cache[cache_key] = {
            'response': response,
            'context': context.copy(),
            'created_time': time.time(),
            'last_used': time.time(),
            'usage_count': 1
        }
        
        # Clean old cache entries if needed
        if len(self.response_cache) > self.max_cached_responses:
            self._clean_cache()
    
    def _clean_cache(self) -> None:
        """Clean old cache entries"""
        # Remove least recently used entries
        sorted_cache = sorted(
            self.response_cache.items(),
            key=lambda x: x[1]['last_used']
        )
        
        # Keep only the most recent entries
        entries_to_keep = self.max_cached_responses // 2
        
        self.response_cache = dict(sorted_cache[-entries_to_keep:])
        print(f"🧹 Cleaned response cache, kept {entries_to_keep} entries")
    
    def _add_to_memory(self, context: Dict[str, Any], response: str) -> None:
        """Add interaction to conversation memory"""
        
        memory_entry = {
            'timestamp': time.time(),
            'escalation_level': context['escalation_level'],
            'context': context.copy(),
            'response': response
        }
        
        self.conversation_memory.append(memory_entry)
        
        # Keep only recent memory (last 20 interactions)
        if len(self.conversation_memory) > 20:
            self.conversation_memory = self.conversation_memory[-20:]
    
    def _get_fallback_response(self, escalation_level: int) -> str:
        """Get fallback response when LLM fails"""
        fallback_responses = {
            1: "Hello, I don't recognize you. Could you please identify yourself?",
            2: "Please state your business here or leave the premises immediately.",
            3: "You are trespassing on private property. Leave now or security will be contacted.",
            4: "INTRUDER ALERT! You must leave immediately. Security has been notified!"
        }
        return fallback_responses.get(escalation_level, fallback_responses[1])
    
    def generate_response_for_situation(self, 
                                      situation: str,
                                      escalation_level: Optional[int] = None) -> str:
        """Generate response for a specific situation"""
        
        if escalation_level is None:
            escalation_level = self.escalation.get_current_level().value
        
        context = {
            'escalation_level': escalation_level,
            'situation': situation,
            'custom_prompt': True
        }
        
        return self.llm.generate_response(
            prompt=situation,
            escalation_level=escalation_level,
            context=context
        )
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation so far"""
        
        if not self.conversation_memory:
            return {'total_responses': 0}
        
        levels_used = [entry['escalation_level'] for entry in self.conversation_memory]
        
        return {
            'total_responses': len(self.conversation_memory),
            'levels_used': list(set(levels_used)),
            'max_level_reached': max(levels_used),
            'conversation_start': self.conversation_memory[0]['timestamp'],
            'last_response': self.conversation_memory[-1]['timestamp'],
            'duration': self.conversation_memory[-1]['timestamp'] - self.conversation_memory[0]['timestamp']
        }
    
    def clear_memory(self) -> None:
        """Clear conversation memory and cache"""
        self.conversation_memory.clear()
        self.response_cache.clear()
        print("🧹 Response generator memory cleared")
    
    def is_available(self) -> bool:
        """Check if response generation is available"""
        return self.llm.is_available() or True  # Always available with fallbacks


# Global response generator instance
response_generator = ResponseGenerator()