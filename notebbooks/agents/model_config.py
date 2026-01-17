"""Centralized model configuration for all agents."""

try:
    # Try relative import first (when used as a package)
    from .config_loader import config
except ImportError:
    # Fall back to absolute import (when used standalone)
    from config_loader import config


class ModelConfig:
    """Configuration for AI models used across agents."""
    
    # Load models from config.yaml
    OCR_MODEL = config.get_model("ocr")
    GRADING_MODEL = config.get_model("grading")
    MODERATION_MODEL = config.get_model("moderation")
    MARKING_SCHEME_MODEL = config.get_model("marking_scheme")
    ANNOTATION_MODEL = config.get_model("annotation")
    ANALYTICS_MODEL = config.get_model("analytics")
    ANALYTICS_IMAGE_MODEL = config.get_model("analytics_image")
    
    @classmethod
    def get_model(cls, agent_type: str) -> str:
        """
        Get model name for a specific agent type.
        
        Args:
            agent_type: Type of agent (ocr, grading, moderation, etc.)
            
        Returns:
            Model name string
        """
        return config.get_model(agent_type)
