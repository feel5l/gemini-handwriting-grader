"""Centralized model configuration for all agents."""

import os


class ModelConfig:
    """Configuration for AI models used across agents."""
    
    # Default models for each agent type
    OCR_MODEL = os.getenv("MODEL_OCR", "gemini-2.5-flash")
    GRADING_MODEL = os.getenv("MODEL_GRADING", "gemini-3-flash-preview")
    MODERATION_MODEL = os.getenv("MODEL_MODERATION", "gemini-3-pro-preview")
    MARKING_SCHEME_MODEL = os.getenv("MODEL_MARKING_SCHEME", "gemini-3-flash-preview")
    ANNOTATION_MODEL = os.getenv("MODEL_ANNOTATION", "gemini-3-flash-preview")
    ANALYTICS_MODEL = os.getenv("MODEL_ANALYTICS", "gemini-3-flash-preview")
    ANALYTICS_IMAGE_MODEL = os.getenv("MODEL_ANALYTICS_IMAGE", "gemini-3-pro-image-preview")
    
    @classmethod
    def get_model(cls, agent_type: str) -> str:
        """
        Get model name for a specific agent type.
        
        Args:
            agent_type: Type of agent (ocr, grading, moderation, etc.)
            
        Returns:
            Model name string
        """
        model_map = {
            "ocr": cls.OCR_MODEL,
            "grading": cls.GRADING_MODEL,
            "moderation": cls.MODERATION_MODEL,
            "marking_scheme": cls.MARKING_SCHEME_MODEL,
            "annotation": cls.ANNOTATION_MODEL,
            "analytics": cls.ANALYTICS_MODEL,
            "analytics_image": cls.ANALYTICS_IMAGE_MODEL,
        }
        return model_map.get(agent_type.lower(), cls.GRADING_MODEL)
