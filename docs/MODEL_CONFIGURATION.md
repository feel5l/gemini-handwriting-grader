# Model Configuration Guide

This document explains how to configure AI models used across the grading system.

## Overview

All AI models are centrally configured through `config.yaml` and the `ModelConfig` class. This makes it easy to:
- Switch models for testing or cost optimization
- Use different models for different agent types
- Update models without changing code

## Configuration Location

Models are configured in `config.yaml` file in the project root.

## Available Model Settings

### Configuration in config.yaml

Edit `config.yaml` to configure models:

```yaml
# Model Configuration
models:
  # OCR Agent - Text extraction from images
  ocr: gemini-2.5-flash
  
  # Grading Agent - Evaluating student answers
  grading: gemini-3-flash-preview
  
  # Moderation Agent - Ensuring grading consistency
  moderation: gemini-3-pro-preview
  
  # Marking Scheme Agent - Extracting and verifying marking schemes
  marking_scheme: gemini-3-flash-preview
  
  # Annotation Agent - Extracting bounding boxes from images
  annotation: gemini-3-flash-preview
  
  # Analytics Agent - Generating reports and insights
  analytics: gemini-3-flash-preview
  
  # Analytics Image Agent - Generating infographic images
  analytics_image: gemini-3-pro-image-preview
```

### Default Models

These are the default models configured in `config.yaml`:

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

```yaml
# In config.yaml
models:
  ocr: gemini-2.0-flash
  grading: gemini-2.0-flash
  moderation: gemini-2.0-pro
  marking_scheme: gemini-2.0-flash
  annotation: gemini-2.0-flash
  analytics: gemini-2.0-flash
  analytics_image: gemini-2.0-pro-image
```

### Use Faster Models for Testing

```yaml
# In config.yaml - use flash models for speed
models:
  moderation: gemini-3-flash-preview  # Instead of pro
```

### Use Higher Quality Models for Production

```yaml
# In config.yaml - use pro models for quality
models:
  grading: gemini-3-pro-preview
  analytics: gemini-3-pro-preview
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
