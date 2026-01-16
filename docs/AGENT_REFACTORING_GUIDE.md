# Agent Refactoring Guide

## Overview

This document outlines the standardized structure and coding conventions for all ADK agents in the grading system.

## Directory Structure

```
notebbooks/agents/
├── __init__.py                 # Main agents package
├── common.py                   # Shared utilities
├── ocr_agent/
│   ├── __init__.py            # Module exports
│   └── agent.py               # Agent implementation
├── grading_agent/
│   ├── __init__.py
│   └── agent.py
├── moderation_agent/
│   ├── __init__.py
│   └── agent.py
├── annotation_agent/
│   ├── __init__.py
│   └── agent.py
├── marking_scheme_agent/
│   ├── __init__.py
│   └── agent.py
└── analytics_agent/
    ├── __init__.py
    └── agent.py
```

## Coding Standards

### 1. File Structure

Each `agent.py` file should follow this structure:

```python
"""Module docstring describing the agent's purpose."""

# Standard library imports
import os
import time
import hashlib
from typing import Optional, List, Dict

# Third-party imports
from google.genai import types
from google.adk.agents import Agent, SequentialAgent
from pydantic import BaseModel, Field

# Local imports
from ..common import setup_agent_environment, run_agent_with_retry
import grading_utils

# Setup
logger = setup_agent_environment(__file__)

# Pydantic Models
class ResponseModel(BaseModel):
    """Model docstring."""
    field: str = Field(description="Field description")

# Agent Definition
agent_name = Agent(
    model="gemini-3-flash-preview",
    name="agent_name",
    description="Brief description",
    instruction="Detailed instructions",
    output_schema=ResponseModel,
    output_key="output",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,
        top_p=0.5,
        max_output_tokens=8192,
        response_mime_type="application/json",
    ),
)

# Public Functions
async def process_with_ai(
    input_data: str,
    max_retries: int = 3
) -> ResponseModel:
    """
    Process data using the agent.
    
    Args:
        input_data: Input data description
        max_retries: Maximum retry attempts
        
    Returns:
        Processed result
    """
    # Implementation
    pass
```

### 2. Import Organization

Always organize imports in this order:

1. Standard library imports
2. Third-party imports (google, pydantic, etc.)
3. Local imports (..common, grading_utils)

Use absolute imports for clarity.

### 3. Naming Conventions

- **Agent instances**: `{purpose}_agent` (e.g., `ocr_agent`, `grading_agent`)
- **Public functions**: `{action}_with_ai` (e.g., `perform_ocr_with_ai`, `grade_answer_with_ai`)
- **Pydantic models**: `{Purpose}Response` or `{Purpose}Result` (e.g., `GradingResult`, `ModerationResponse`)
- **Private functions**: Prefix with `_` (e.g., `_validate_input`)

### 4. Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int = 5) -> bool:
    """
    Brief description of function.
    
    Longer description if needed, explaining the purpose
    and behavior in more detail.
    
    Args:
        param1: Description of param1
        param2: Description of param2 with default
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When validation fails
    """
```

### 5. Type Hints

Always use type hints for:
- Function parameters
- Return values
- Class attributes (via Pydantic Field)

```python
from typing import Optional, List, Dict, Tuple

async def process_data(
    text: str,
    options: Optional[Dict[str, any]] = None
) -> List[str]:
    """Process data with optional configuration."""
    pass
```

### 6. Caching Pattern

Use consistent caching pattern:

```python
# Check cache
cache_key = None
try:
    cache_key = grading_utils.get_cache_key(
        "operation_type",
        model="gemini-3-flash-preview",
        param1=value1,
        param2=value2
    )
    cached = grading_utils.get_from_cache(cache_key)
    if cached:
        logger.info("Cache hit")
        return process_cached_result(cached)
except Exception as e:
    logger.warning(f"Cache lookup failed: {e}")

# ... perform operation ...

# Save to cache
if cache_key:
    grading_utils.save_to_cache(cache_key, result)
```

### 7. Error Handling

Use consistent error handling:

```python
try:
    result = await run_agent_with_retry(
        agent=my_agent,
        user_content=content,
        app_name="my_agent",
        output_type=MyResponse,
        max_retries=max_retries,
        logger=logger
    )
    return result
except Exception as e:
    logger.error(f"Operation failed: {e}")
    # Return fallback or raise
    return fallback_result()
```

### 8. Logging

Use consistent logging levels:

- `logger.info()`: Normal operations, cache hits, success messages
- `logger.warning()`: Recoverable issues, cache misses, retries
- `logger.error()`: Failures, exceptions, critical issues

```python
logger.info(f"Processing {count} items")
logger.warning(f"Retry attempt {attempt}/{max_retries}")
logger.error(f"Failed to process: {error}")
```

### 9. Configuration

Agent configuration should be explicit and documented:

```python
agent = Agent(
    model="gemini-3-flash-preview",  # Model selection
    name="agent_name",                # Unique identifier
    description="Brief purpose",      # What it does
    instruction="Detailed prompt",    # How it behaves
    output_schema=ResponseModel,      # Expected output
    output_key="output",              # State key
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,              # Deterministic
        top_p=0.5,                    # Token sampling
        max_output_tokens=8192,       # Response limit
        response_mime_type="application/json",  # Format
    ),
)
```

### 10. Module Exports

Each `__init__.py` should explicitly export public API:

```python
"""Module docstring."""

from .agent import agent_name, public_function

__all__ = ['agent_name', 'public_function']
```

## Common Patterns

### Sequential Agents

For multi-step workflows:

```python
sequential_agent = SequentialAgent(
    name="workflow_name",
    description="Multi-step workflow description",
    sub_agents=[step1_agent, step2_agent, step3_agent]
)
```

### Tool Integration

For agents that use tools:

```python
def my_tool(param: str) -> str:
    """Tool function docstring."""
    # Implementation
    return result

agent_with_tools = Agent(
    # ... other config ...
    tools=[my_tool],
    # ... rest of config ...
)
```

### Image Processing

For agents that process images:

```python
content = types.Content(
    role="user",
    parts=[
        types.Part(
            inline_data=types.Blob(
                mime_type="image/jpeg",
                data=image_data
            )
        ),
        types.Part(text=prompt)
    ]
)
```

## Testing Checklist

Before committing agent code:

- [ ] All imports are organized correctly
- [ ] Type hints are present for all functions
- [ ] Docstrings follow Google style
- [ ] Caching is implemented consistently
- [ ] Error handling includes logging
- [ ] Module exports are defined in `__init__.py`
- [ ] Agent configuration is documented
- [ ] Function names follow conventions
- [ ] Code passes linting (pylint)

## Migration Guide

To refactor an existing agent:

1. **Update imports**: Organize into standard/third-party/local groups
2. **Add type hints**: Add to all function signatures
3. **Standardize docstrings**: Convert to Google style
4. **Refactor caching**: Use consistent pattern
5. **Update error handling**: Add proper logging
6. **Create `__init__.py`**: Export public API
7. **Update agent config**: Add inline comments
8. **Test**: Verify functionality unchanged

## Example: Complete Agent Module

See `notebbooks/agents/ocr_agent/` for a fully refactored example following all conventions.

## Questions?

For questions about agent refactoring, refer to:
- `notebbooks/agents/common.py` - Shared utilities
- `notebbooks/grading_utils.py` - Caching and utilities
- Google ADK documentation - Agent framework details
