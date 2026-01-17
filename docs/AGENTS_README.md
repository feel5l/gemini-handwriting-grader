# AI Grading Agents

This directory contains all ADK (Agent Development Kit) agents used in the AI handwriting grading system.

## Structure

Each agent follows the "one folder, one agent" pattern:

```
agents/
├── __init__.py                 # Main package exports
├── common.py                   # Shared utilities
├── ocr_agent/                  # OCR text extraction
│   ├── __init__.py
│   └── agent.py
├── grading_agent/              # Answer grading
│   ├── __init__.py
│   └── agent.py
├── moderation_agent/           # Grade moderation
│   ├── __init__.py
│   └── agent.py
├── annotation_agent/           # Bounding box extraction
│   ├── __init__.py
│   └── agent.py
├── marking_scheme_agent/       # Marking scheme extraction
│   ├── __init__.py
│   └── agent.py
└── analytics_agent/            # Performance analytics
    ├── __init__.py
    └── agent.py
```

## Agents

### 1. OCR Agent
**Purpose:** Extract text from images using OCR

**Functions:**
- `perform_ocr_with_ai(prompt, image_path, image_data, max_retries)`

**Usage:**
```python
from notebbooks.agents.ocr_agent import perform_ocr_with_ai

text = await perform_ocr_with_ai(
    prompt="Extract the handwritten text",
    image_path="answer.jpg"
)
```

**Note:** Agents are created dynamically with callback-based caching for optimal performance.

### 2. Grading Agent
**Purpose:** Grade student answers against marking schemes

**Functions:**
- `grade_answer_with_ai(question_text, submitted_answer, marking_scheme_text, total_marks, max_retries)`
- `grade_answer_with_ocr_and_ai(question_text, marking_scheme_text, total_marks, image_data, max_retries)`

**Usage:**
```python
from notebbooks.agents.grading_agent import grade_answer_with_ai

result = await grade_answer_with_ai(
    question_text="What is photosynthesis?",
    submitted_answer="Process where plants make food",
    marking_scheme_text="- Definition (2 marks)\n- Process (3 marks)",
    total_marks=5
)
```

**Note:** Agents are created dynamically with callback-based caching for optimal performance.

### 3. Moderation Agent
**Purpose:** Ensure grading consistency across students

**Functions:**
- `moderate_grades_with_ai(question_text, marking_scheme_text, total_marks, entries, max_retries)`

**Usage:**
```python
from notebbooks.agents.moderation_agent import moderate_grades_with_ai

results = await moderate_grades_with_ai(
    question_text="Question text",
    marking_scheme_text="Marking scheme",
    total_marks=10,
    entries=[{"answer": "...", "mark": 7}, ...]
)
```

### 4. Annotation Agent
**Purpose:** Extract bounding boxes for question cells from exam images

**Functions:**
- `extract_annotations_with_ai(image_path, max_retries)`

**Usage:**
```python
from notebbooks.agents.annotation_agent import extract_annotations_with_ai

response = await extract_annotations_with_ai(
    image_path="exam_sheet.jpg"
)
boxes = response.boxes
```

### 5. Marking Scheme Agent
**Purpose:** Extract and verify marking schemes from documents

**Functions:**
- `extract_marking_scheme_with_ai(markdown_content, max_retries)`
- `verify_marking_scheme_with_ai(questions_data, max_retries)`

**Usage:**
```python
from notebbooks.agents.marking_scheme_agent import extract_marking_scheme_with_ai

questions, guide = await extract_marking_scheme_with_ai(
    markdown_content="# Marking Scheme\n..."
)
```

### 6. Analytics Agent
**Purpose:** Generate performance reports and insights

**Functions:**
- `generate_student_report_with_ai(student_id, student_name, student_class, total_score, question_details, max_retries)`
- `generate_class_overview_with_ai(summary_payload, sample_reports, max_retries)`
- `generate_question_insights_with_ai(question_data_payload, max_retries)`

**Usage:**
```python
from notebbooks.agents.analytics_agent import generate_student_report_with_ai

report = await generate_student_report_with_ai(
    student_id="12345",
    student_name="John Doe",
    student_class="10A",
    total_score=85,
    question_details="Q1: 8/10\nQ2: 7/10..."
)
```

## Common Utilities

The `common.py` module provides shared utilities:

- `setup_agent_environment(file_path)` - Initialize agent environment
- `run_agent_with_retry(agent, user_content, app_name, output_type, max_retries, logger, output_key)` - Execute agent with retry logic

## Features

### Cache Control
Control caching behavior for each agent type individually:

```yaml
# In config.yaml
caching:
  enabled: true  # Master control for all agents
  agents:
    ocr: true              # Control OCR caching
    grading: true          # Control grading caching
    moderation: true       # Control moderation caching
    marking_scheme: true   # Control marking scheme caching
    annotation: true       # Control annotation caching
    analytics: true        # Control analytics caching
```

Set to `false` to disable caching for specific agents - useful for debugging, testing, or forcing fresh results.

**Full guide:** `CACHE_CONTROL.md`

### Log Level Configuration
Control logging verbosity in `config.yaml`:

```yaml
# In config.yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Quick Reference:**
- **DEBUG**: Most verbose - shows all operations, cache checks, event processing
- **INFO**: Default - shows important operations, cache hits, completions
- **WARNING**: Minimal - shows only warnings and errors
- **ERROR**: Failures only

**Documentation:**
- Quick reference: `LOG_LEVEL_QUICK_REF.md`
- Full review: `../../docs/LOG_LEVEL_REVIEW_COMPLETE.md`
- Test script: `test_log_levels.py`

### Dynamic Agent Creation
All agents are created dynamically with callback-based caching:
- Agents are instantiated on-demand with specific configurations
- Caching callbacks are attached at creation time
- No static agent instances - cleaner and more flexible

### Type Safety
All functions have complete type hints:
```python
async def process_data(
    text: str,
    options: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Process data with optional configuration."""
```

### Caching
All agents implement consistent caching:
- Automatic cache key generation
- Cache hit/miss logging
- Configurable cache directory

### Error Handling
Standardized error handling with:
- Retry logic with exponential backoff
- Comprehensive logging
- Graceful fallbacks

### Documentation
Every function includes:
- Comprehensive docstrings
- Parameter descriptions
- Return value documentation
- Usage examples

## Development

### Adding a New Agent

1. Create a new directory: `agents/new_agent/`
2. Create `__init__.py` with exports
3. Create `agent.py` following the pattern:

```python
"""New agent for specific purpose."""

from typing import Optional
from google.genai import types
from google.adk.agents import Agent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry
import grading_utils

logger = setup_agent_environment(__file__)

class ResponseModel(BaseModel):
    """Response model."""
    result: str = Field(description="Result description")

new_agent = Agent(
    model="gemini-3-flash-preview",
    name="new_agent",
    description="Agent description",
    instruction="Agent instructions",
    output_schema=ResponseModel,
    output_key="output",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
    ),
)

async def process_with_ai(
    input_data: str,
    max_retries: int = 3
) -> ResponseModel:
    """
    Process data using the agent.
    
    Args:
        input_data: Input data
        max_retries: Maximum retry attempts
        
    Returns:
        Processed result
    """
    # Implementation
    pass
```

4. Update `agents/__init__.py` to include new agent
5. Add documentation to this README

### Testing

Run diagnostics on all agents:
```bash
# Check for errors
python -m pylint notebbooks/agents/

# Verify imports
python -c "from notebbooks.agents import *"
```

## Documentation

For detailed information, see:
- `README.md` (this file) - Agent overview and usage
- `CACHE_CONTROL.md` - Cache control configuration guide
- `CACHING_REFACTOR.md` - Caching implementation details
- `LOG_LEVEL_QUICK_REF.md` - Log level configuration
- `../../docs/COMPLETE_AGENT_REFACTORING.md` - Complete refactoring documentation
- `../../docs/LOG_LEVEL_REVIEW_COMPLETE.md` - Log level implementation review

## Requirements

- Python 3.8+
- google-genai
- google-adk
- pydantic
- PIL (for image processing in analytics agent)

## License

See project root for license information.
