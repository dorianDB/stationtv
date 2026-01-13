"""
Station TV - Core Transcription Module
Module principal de transcription audio basé sur Whisper (OpenAI)
"""

from .transcription import WhisperTranscriber
from .models import ModelManager
from .affinity import CPUAffinityManager

__all__ = ['WhisperTranscriber', 'ModelManager', 'CPUAffinityManager']
