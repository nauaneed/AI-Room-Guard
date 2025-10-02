"""
LLM Module
Large Language Model integration for intelligent dialogue generation
"""

from .llm_config import LLMConfig, llm_config
from .dialogue_generator import DialogueGenerator, dialogue_generator

__all__ = [
    'LLMConfig',
    'llm_config', 
    'DialogueGenerator',
    'dialogue_generator'
]