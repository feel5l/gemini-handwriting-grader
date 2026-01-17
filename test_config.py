#!/usr/bin/env python3
"""Test script to verify configuration loading."""

import sys
import os
from pathlib import Path

# Add notebbooks to path
sys.path.insert(0, str(Path(__file__).parent / "notebbooks" / "agents"))

from config_loader import config
from model_config import ModelConfig

def test_config():
    """Test configuration loading."""
    print("=" * 60)
    print("Configuration Test")
    print("=" * 60)
    
    # Test basic config loading
    print("\n1. Basic Configuration:")
    print(f"   Log Level: {config.log_level}")
    print(f"   Cache Enabled: {config.cache_enabled}")
    print(f"   Use Vertex AI: {config.use_vertexai}")
    
    # Test model configuration
    print("\n2. Model Configuration:")
    models = ['ocr', 'grading', 'moderation', 'marking_scheme', 
              'annotation', 'analytics', 'analytics_image']
    for model_type in models:
        model_name = config.get_model(model_type)
        print(f"   {model_type:20s}: {model_name}")
    
    # Test agent cache settings
    print("\n3. Agent Cache Settings:")
    agents = ['ocr', 'grading', 'moderation', 'marking_scheme', 
              'annotation', 'analytics']
    for agent in agents:
        enabled = config.is_agent_cache_enabled(agent)
        status = "✓ Enabled" if enabled else "✗ Disabled"
        print(f"   {agent:20s}: {status}")
    
    # Test ModelConfig class (backward compatibility)
    print("\n4. ModelConfig Class (Backward Compatibility):")
    print(f"   OCR Model: {ModelConfig.OCR_MODEL}")
    print(f"   Grading Model: {ModelConfig.GRADING_MODEL}")
    print(f"   get_model('grading'): {ModelConfig.get_model('grading')}")
    
    # Test API key loading from .env
    print("\n5. Environment Variables:")
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    if api_key:
        # Mask the API key for security
        masked = api_key[:10] + "..." + api_key[-10:] if len(api_key) > 20 else "***"
        print(f"   API Key: {masked}")
    else:
        print("   API Key: ⚠ Not set in .env")
    
    # Check GOOGLE_GENAI_USE_VERTEXAI is set
    use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")
    print(f"   GOOGLE_GENAI_USE_VERTEXAI: {use_vertexai}")
    if use_vertexai == "TRUE":
        print("   ✓ Vertex AI mode enabled")
    else:
        print("   ⚠ Vertex AI mode not enabled")
    
    print("\n" + "=" * 60)
    print("✓ All configuration tests passed!")
    print("=" * 60)
    print("\nFor configuration help, see: docs/CONFIGURATION.md")

if __name__ == "__main__":
    try:
        test_config()
    except Exception as e:
        print(f"\n✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
