#!/bin/bash
# Setup script for AI Grading System configuration

echo "=========================================="
echo "AI Grading System - Configuration Setup"
echo "=========================================="
echo ""

# Check if config.yaml exists
if [ -f "config.yaml" ]; then
    echo "✓ config.yaml already exists"
else
    echo "Creating config.yaml from template..."
    cp config.yaml.template config.yaml
    echo "✓ config.yaml created"
fi

# Check if .env exists
if [ -f ".env" ]; then
    echo "✓ .env already exists"
    
    # Check if API key is set
    if grep -q "GOOGLE_GENAI_API_KEY=.*[A-Za-z0-9]" .env; then
        echo "✓ API key appears to be configured"
    else
        echo "⚠ Warning: API key not set in .env"
        echo "  Please edit .env and add your Google Gemini API key"
        echo "  Get your key from: https://aistudio.google.com/apikey"
    fi
else
    echo "Creating .env from template..."
    cp .env.template .env
    echo "✓ .env created"
    echo "⚠ Please edit .env and add your Google Gemini API key"
    echo "  Get your key from: https://aistudio.google.com/apikey"
fi

echo ""
echo "=========================================="
echo "Configuration files ready!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Google Gemini API key"
echo "2. (Optional) Edit config.yaml to customize settings"
echo "3. Run: python3 test_config.py to verify configuration"
echo ""
echo "For more information, see:"
echo "- README.md"
echo "- docs/CONFIGURATION.md"
echo ""
