# Configuration Guide

Complete guide for configuring the AI Grading System.

## Quick Start

### 1. Setup Configuration Files

```bash
# Run setup script (creates .env from template if needed)
python3 setup_config.py

# Note: config.yaml already exists in the repository
```

### 2. Add API Key

Edit `.env` and add your Google Gemini API key:

```env
GOOGLE_GENAI_API_KEY=your-api-key-here
```

Get your API key from: https://aistudio.google.com/apikey

### 3. (Optional) Customize Settings

Edit `config.yaml` to customize logging, caching, or models:

```yaml
logging:
  level: INFO  # Change to DEBUG for more details

caching:
  enabled: true  # Set to false to disable all caching

models:
  grading: gemini-3-pro-preview  # Upgrade to pro model
```

### 4. Verify Configuration

```bash
python3 test_config.py
```

## Configuration Files

### `.env` - API Key (Sensitive)

Contains only the API key. **Never commit this file to version control.**

```env
GOOGLE_GENAI_API_KEY=your-api-key-here
```

### `config.yaml` - Application Settings (Safe to Share)

Contains all non-sensitive configuration. Safe to commit to version control.

```yaml
# Vertex AI Configuration
vertex_ai:
  use_vertexai: true  # Automatically sets GOOGLE_GENAI_USE_VERTEXAI env var

# Logging Configuration
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Caching Configuration
caching:
  enabled: true  # Master cache control
  agents:
    ocr: true
    grading: true
    moderation: true
    marking_scheme: true
    annotation: true
    analytics: true

# Model Configuration
models:
  ocr: gemini-2.5-flash
  grading: gemini-3-flash-preview
  moderation: gemini-3-pro-preview
  marking_scheme: gemini-3-flash-preview
  annotation: gemini-3-flash-preview
  analytics: gemini-3-flash-preview
  analytics_image: gemini-3-pro-image-preview
```

## Configuration Options

### Vertex AI

**Setting**: `vertex_ai.use_vertexai`  
**Values**: `true` or `false`  
**Default**: `true`

Controls whether to use Vertex AI or standard API. Automatically sets the `GOOGLE_GENAI_USE_VERTEXAI` environment variable.

### Logging Level

**Setting**: `logging.level`  
**Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Default**: `INFO`

- **DEBUG**: Most verbose, shows all operations including cache checks
- **INFO**: Standard logging, shows important operations and cache hits/misses
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors
- **CRITICAL**: Only critical errors

### Caching

**Master Control**: `caching.enabled`  
**Values**: `true` or `false`  
**Default**: `true`

When `false`, disables all agent caching regardless of individual settings.

**Individual Agents**: `caching.agents.<agent_type>`  
**Values**: `true` or `false`  
**Default**: `true`

Only applies when master caching is enabled. Available agents:
- `ocr`: Text extraction from images
- `grading`: Evaluating student answers
- `moderation`: Ensuring grading consistency
- `marking_scheme`: Extracting and verifying marking schemes
- `annotation`: Extracting bounding boxes from images
- `analytics`: Generating reports and insights

### Models

**Setting**: `models.<agent_type>`  
**Values**: Any valid Gemini model name  
**Defaults**: See config.yaml.template

Each agent can use a different model. Common models:
- `gemini-2.5-flash`: Fast, cost-effective
- `gemini-3-flash-preview`: Balanced performance
- `gemini-3-pro-preview`: Most capable
- `gemini-3-pro-image-preview`: For image generation

## Common Customizations

### Enable Debug Logging

```yaml
logging:
  level: DEBUG
```

### Disable All Caching

```yaml
caching:
  enabled: false
```

### Disable Specific Agent Cache

```yaml
caching:
  enabled: true
  agents:
    grading: false  # Disable only grading cache
```

### Use More Powerful Model

```yaml
models:
  grading: gemini-3-pro-preview  # Upgrade from flash to pro
```

### Disable Vertex AI

```yaml
vertex_ai:
  use_vertexai: false
```

## Using Configuration in Code

### Import Config

```python
from notebbooks.agents.config_loader import config

# Get any setting using dot notation
log_level = config.get('logging.level')
cache_enabled = config.cache_enabled
model = config.get_model('grading')

# Check if agent caching is enabled
if config.is_agent_cache_enabled('ocr'):
    # Use cache
    pass
```

### Using ModelConfig (Backward Compatible)

```python
from notebbooks.agents.model_config import ModelConfig

# Get model for specific agent
model = ModelConfig.get_model('grading')
```

## Environment Variables

The config loader automatically sets environment variables for compatibility:

| Config Setting | Environment Variable | Purpose |
|---------------|---------------------|---------|
| `vertex_ai.use_vertexai` | `GOOGLE_GENAI_USE_VERTEXAI` | Google library compatibility |

You can verify environment variables are set:

```python
import os
print(os.getenv('GOOGLE_GENAI_USE_VERTEXAI'))  # Should print 'TRUE' or 'FALSE'
```

## Troubleshooting

### Configuration file not found

**Error**: `Configuration file not found at config.yaml`

**Solution**:
```bash
python3 setup_config.py  # Creates missing files
```

### API key not found

**Error**: `Please set GOOGLE_GENAI_API_KEY in .env`

**Solution**:
1. Ensure `.env` file exists in project root
2. Add your API key: `GOOGLE_GENAI_API_KEY=your-key-here`
3. Get key from: https://aistudio.google.com/apikey

### Configuration changes not taking effect

**Solution**:
1. Restart Jupyter kernel or Python process
2. Check YAML syntax in `config.yaml`
3. Run `python3 test_config.py` to diagnose

### Invalid YAML syntax

**Error**: YAML parsing errors

**Solution**:
1. Check indentation (use spaces, not tabs)
2. Ensure colons have space after them: `key: value`
3. Validate YAML online: https://www.yamllint.com/

## Best Practices

1. **Never commit `.env`** - It's in .gitignore for security
2. **Commit `config.yaml`** - Safe to share, no sensitive data
3. **Use templates** - Copy from `.template` files for new setups
4. **Test changes** - Run `python3 test_config.py` after modifications
5. **Restart kernel** - After config changes in Jupyter notebooks
6. **Document custom settings** - Add comments in config.yaml

## Migration from Old System

If you're upgrading from an older version that used environment variables for all configuration:

### Old System (.env with many variables)
```env
GOOGLE_GENAI_API_KEY=key
GOOGLE_GENAI_USE_VERTEXAI=TRUE
AGENT_LOG_LEVEL=INFO
AGENT_CACHE_ENABLED=TRUE
AGENT_CACHE_OCR=TRUE
AGENT_CACHE_GRADING=TRUE
# ... many more lines
MODEL_OCR=gemini-2.5-flash
MODEL_GRADING=gemini-3-flash-preview
# ... etc
```

### New System (Separated)

**`.env`** (Only API key):
```env
GOOGLE_GENAI_API_KEY=key
```

**`config.yaml`** (All other settings):
```yaml
vertex_ai:
  use_vertexai: true

logging:
  level: INFO

caching:
  enabled: true
  agents:
    ocr: true
    grading: true
    moderation: true
    marking_scheme: true
    annotation: true
    analytics: true

models:
  ocr: gemini-2.5-flash
  grading: gemini-3-flash-preview
  moderation: gemini-3-pro-preview
  marking_scheme: gemini-3-flash-preview
  annotation: gemini-3-flash-preview
  analytics: gemini-3-flash-preview
  analytics_image: gemini-3-pro-image-preview
```

### Migration Steps

1. Backup current `.env`: `cp .env .env.backup`
2. Verify `config.yaml` exists with all settings
3. Update `.env` to only contain `GOOGLE_GENAI_API_KEY`
4. Verify: `python3 test_config.py`
5. Remove old environment variables from `.env`

## Related Documentation

- **Agent System**: [AGENTS_README.md](AGENTS_README.md)
- **Cache Control**: [CACHE_CONTROL.md](CACHE_CONTROL.md)
- **Log Levels**: [LOG_LEVEL_QUICK_REF.md](LOG_LEVEL_QUICK_REF.md)
- **Model Selection**: [MODEL_CONFIGURATION.md](MODEL_CONFIGURATION.md)
