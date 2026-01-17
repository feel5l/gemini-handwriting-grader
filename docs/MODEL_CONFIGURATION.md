# Model Configuration Guide

This document explains how to configure AI models used across the grading system.

## Overview

All AI models are now centrally configured through environment variables and the `ModelConfig` class. This makes it easy to:
- Switch models for testing or cost optimization
- Use different models for different agent types
- Update models without changing code

## Configuration Location

Models are configured in two places:

1. **Environment Variables** (`.env` file) - Runtime configuration
2. **ModelConfig Class** (`notebbooks/agents/model_config.py`) - Default values and access

## Available Model Settings

### Environment Variables

Add these to your `.env` file to override default models:

```bash
# OCR Agent - Text extraction from images
MODEL_OCR=gemini-2.5-flash

# Grading Agent - Evaluating student answers
MODEL_GRADING=gemini-3-flash-preview

# Moderation Agent - Ensuring grading consistency
MODEL_MODERATION=gemini-3-pro-preview

# Marking Scheme Agent - Extracting and verifying marking schemes
MODEL_MARKING_SCHEME=gemini-3-flash-preview

# Annotation Agent - Extracting bounding boxes from images
MODEL_ANNOTATION=gemini-3-flash-preview

# Analytics Agent - Generating reports and insights
MODEL_ANALYTICS=gemini-3-flash-preview

# Analytics Image Agent - Generating infographic images
MODEL_ANALYTICS_IMAGE=gemini-3-pro-image-preview
```

### Default Models

If environment variables are not set, these defaults are used:

| Agent Type | Default Model | Purpose |
|------------|---------------|---------|
| OCR | `gemini-2.5-flash` | Fast, accurate text extraction |
| Grading | `gemini-3-flash-preview` | Balanced speed and quality |
| Moderation | `gemini-3-pro-preview` | Higher quality for consistency checks |
| Marking Scheme | `gemini-3-flash-preview` | Document analysis and verification |
| Annotation | `gemini-3-flash-preview` | Bounding box detection |
| Analytics | `gemini-3-flash-preview` | Report generation |
| Analytics Image | `gemini-3-pro-image-preview` | Infographic generation |

## Usage Examples

### Change All Models to a Specific Version

```bash
# In .env file
MODEL_OCR=gemini-2.0-flash
MODEL_GRADING=gemini-2.0-flash
MODEL_MODERATION=gemini-2.0-pro
MODEL_MARKING_SCHEME=gemini-2.0-flash
MODEL_ANNOTATION=gemini-2.0-flash
MODEL_ANALYTICS=gemini-2.0-flash
MODEL_ANALYTICS_IMAGE=gemini-2.0-pro-image
```

### Use Faster Models for Testing

```bash
# In .env file - use flash models for speed
MODEL_MODERATION=gemini-3-flash-preview  # Instead of pro
```

### Use Higher Quality Models for Production

```bash
# In .env file - use pro models for quality
MODEL_GRADING=gemini-3-pro-preview
MODEL_ANALYTICS=gemini-3-pro-preview
```

## Programmatic Access

You can also access model configuration in code:

```python
from notebbooks.agents import ModelConfig

# Get specific model
ocr_model = ModelConfig.OCR_MODEL
grading_model = ModelConfig.GRADING_MODEL

# Get model by agent type
model = ModelConfig.get_model("ocr")
```

## Model Selection Guidelines

### When to Use Flash Models
- Development and testing
- High-volume processing
- Cost-sensitive operations
- Tasks with clear, structured inputs

### When to Use Pro Models
- Production grading
- Complex reasoning tasks
- Quality-critical operations
- Moderation and consistency checks

### When to Use Image Models
- Infographic generation
- Visual content creation
- Multi-modal outputs

## Cache Implications

**Important:** Changing models will invalidate existing cache entries because the model name is part of the cache key. This is intentional to ensure consistency.

If you change a model:
1. Existing cached results will not be used
2. New results will be cached with the new model name
3. You can clear the cache if needed: `rm -rf cache/`

## Troubleshooting

### Model Not Found Error
- Ensure the model name is correct and available in your region
- Check Google AI Studio for available models
- Verify your API key has access to the model

### Unexpected Results After Model Change
- Clear the cache to ensure fresh results
- Check model capabilities match your use case
- Review model documentation for differences

## Best Practices

1. **Document Changes**: Note model changes in your deployment logs
2. **Test First**: Test model changes in development before production
3. **Monitor Costs**: Different models have different pricing
4. **Track Quality**: Compare results when changing models
5. **Use Defaults**: Default models are optimized for each task

## Related Documentation

- [Caching System](CACHE_CONTROL.md)
- [Agent Architecture](AGENTS_README.md)
- [Environment Setup](../README.md)
