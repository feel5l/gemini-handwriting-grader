#!/usr/bin/env python3
"""Setup script for AI Grading System configuration."""

import os
import shutil
from pathlib import Path


def main():
    """Setup configuration files."""
    print("=" * 60)
    print("AI Grading System - Configuration Setup")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent
    
    # Setup config.yaml
    config_file = project_root / "config.yaml"
    config_template = project_root / "config.yaml.template"
    
    if config_file.exists():
        print("✓ config.yaml already exists")
    else:
        if config_template.exists():
            shutil.copy(config_template, config_file)
            print("✓ config.yaml created from template")
        else:
            print("✗ Error: config.yaml.template not found")
            return 1
    
    # Setup .env
    env_file = project_root / ".env"
    env_template = project_root / ".env.template"
    
    if env_file.exists():
        print("✓ .env already exists")
        
        # Check if API key is set
        with open(env_file, 'r') as f:
            content = f.read()
            if "GOOGLE_GENAI_API_KEY=" in content:
                # Check if there's a value after the =
                for line in content.split('\n'):
                    if line.startswith("GOOGLE_GENAI_API_KEY="):
                        value = line.split('=', 1)[1].strip()
                        if value and value != "your-api-key-here":
                            print("✓ API key appears to be configured")
                        else:
                            print("⚠ Warning: API key not set in .env")
                            print("  Please edit .env and add your Google Gemini API key")
                            print("  Get your key from: https://aistudio.google.com/apikey")
                        break
    else:
        if env_template.exists():
            shutil.copy(env_template, env_file)
            print("✓ .env created from template")
            print("⚠ Please edit .env and add your Google Gemini API key")
            print("  Get your key from: https://aistudio.google.com/apikey")
        else:
            print("✗ Error: .env.template not found")
            return 1
    
    print()
    print("=" * 60)
    print("Configuration files ready!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Edit .env and add your Google Gemini API key")
    print("2. (Optional) Edit config.yaml to customize settings")
    print("3. Run: python3 test_config.py to verify configuration")
    print()
    print("For more information, see:")
    print("- README.md")
    print("- docs/CONFIGURATION.md")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())
