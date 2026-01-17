"""Configuration loader for AI Grading System.

This module loads configuration from config.yaml and .env files.
API keys are stored in .env, while other settings are in config.yaml.

The config loader automatically sets environment variables for compatibility:
- GOOGLE_GENAI_USE_VERTEXAI: Set based on vertex_ai.use_vertexai config
"""

import os
import yaml
from typing import Any, Dict
from pathlib import Path


class Config:
    """Configuration manager for the AI Grading System."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    _loaded = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration loader."""
        if not self._loaded:
            self._load_config()
            self._loaded = True
    
    def _find_project_root(self) -> Path:
        """Find the project root directory by looking for config.yaml."""
        current = Path(__file__).resolve()
        
        # Try going up from current file location
        for parent in [current.parent] + list(current.parents):
            config_file = parent / "config.yaml"
            if config_file.exists():
                return parent
        
        # Fallback: assume we're in notebbooks/agents/
        return current.parent.parent.parent
    
    def _load_config(self):
        """Load configuration from config.yaml file."""
        project_root = self._find_project_root()
        config_path = project_root / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {config_path}. "
                "Please ensure config.yaml exists in the project root."
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}
        
        # Set environment variables for compatibility with Google GenAI library
        self._set_environment_variables()
    
    def _set_environment_variables(self):
        """Set environment variables based on config for library compatibility."""
        # Set GOOGLE_GENAI_USE_VERTEXAI for Google GenAI library
        # This environment variable is checked by some Google libraries
        if self.use_vertexai:
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
        else:
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'logging.level')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config = Config()
            >>> config.get('logging.level')
            'INFO'
            >>> config.get('models.ocr')
            'gemini-2.5-flash'
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    # Convenience properties for commonly used settings
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('logging.level', 'INFO').upper()
    
    @property
    def cache_enabled(self) -> bool:
        """Check if caching is globally enabled."""
        return self.get('caching.enabled', True)
    
    def is_agent_cache_enabled(self, agent_type: str) -> bool:
        """
        Check if caching is enabled for a specific agent.
        
        Args:
            agent_type: Agent type (ocr, grading, moderation, etc.)
            
        Returns:
            True if caching is enabled for this agent
        """
        if not self.cache_enabled:
            return False
        return self.get(f'caching.agents.{agent_type}', True)
    
    def get_model(self, agent_type: str) -> str:
        """
        Get model name for a specific agent type.
        
        Args:
            agent_type: Agent type (ocr, grading, moderation, etc.)
            
        Returns:
            Model name string
        """
        return self.get(f'models.{agent_type}', 'gemini-3-flash-preview')
    
    @property
    def use_vertexai(self) -> bool:
        """Check if Vertex AI should be used."""
        return self.get('vertex_ai.use_vertexai', True)


# Global config instance
config = Config()
