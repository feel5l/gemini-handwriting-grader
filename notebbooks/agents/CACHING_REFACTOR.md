# Caching Refactor - Using before_model_callback and after_model_callback Pattern

## Overview

The caching implementation has been refactored to use Google ADK's `before_model_callback` and `after_model_callback` pattern, inspired by the official Google ADK examples. This approach provides cleaner separation of concerns and more efficient caching.

## Key Changes

### Before (Manual Caching)
- Cache checks were manually implemented in each agent function
- Cache keys generated and checked before agent execution
- Cache saves performed manually after successful responses
- Duplicated caching logic across multiple agents

### After (Callback-Based Caching)
- Caching logic encapsulated in callback functions
- Cache checks happen automatically via `before_model_callback`
- Cache saves happen automatically via `after_model_callback`
- LLM calls are skipped entirely on cache hits (more efficient)
- Reusable callback factories for different agent types

## Architecture

### Callback Functions
Located in `notebbooks/agents/caching_callback.py`

**Key Features:**
- `before_model_callback`: Checks cache before LLM call, returns cached response to skip call
- `after_model_callback`: Saves response to cache after successful LLM call
- Factory functions return tuple of (before_callback, after_callback)
- Cache keys generated from operation parameters (not LLM request)

**Callback Factories:**
- `create_ocr_cache_callbacks()` - For OCR operations
- `create_grading_cache_callbacks()` - For text grading
- `create_ocr_grading_cache_callbacks()` - For OCR+grading sequential operations

### Updated Agents

**OCR Agent** (`ocr_agent/agent.py`):
- Agent instance now created dynamically with callback
- Callback configured with prompt and image hash
- Cache hits skip OCR processing entirely

**Grading Agent** (`grading_agent/agent.py`):
- Both `grade_answer_with_ai()` and `grade_answer_with_ocr_and_ai()` updated
- Agents created with appropriate caching callbacks
- Sequential agent caching supported

**Common Utilities** (`common.py`):
- `run_agent_with_retry()` remains unchanged - no cache parameters needed
- Caching is fully handled by callbacks attached to agents

## Benefits

1. **Efficiency**: LLM calls are skipped entirely on cache hits (not just response reuse)
2. **Automatic**: Cache saving happens automatically in `after_model_callback`
3. **Cleaner Code**: Caching logic completely separated from business logic
4. **Reusability**: Callback factories work for any agent type
5. **Maintainability**: Easier to modify caching behavior in one place
6. **Consistency**: Same caching pattern across all agents

## Usage Example

```python
from agents.grading_agent.agent import grade_answer_with_ai

# Caching is completely automatic - just call the function
result = await grade_answer_with_ai(
    question_text="What is 2+2?",
    submitted_answer="4",
    marking_scheme_text="Correct answer: 4",
    total_marks=5.0
)
# First call: LLM is invoked, result automatically cached via after_model_callback
# Second call: Cache hit via before_model_callback, LLM call skipped entirely
```

## How It Works

1. **Cache Hit Flow:**
   - `before_model_callback` checks cache
   - If found, returns `LlmResponse` with cached data
   - LLM call is skipped entirely
   - `after_model_callback` is NOT called

2. **Cache Miss Flow:**
   - `before_model_callback` checks cache, returns `None`
   - LLM call proceeds normally
   - `after_model_callback` receives response
   - Response is automatically saved to cache

## Backward Compatibility

All existing function signatures remain unchanged. The refactoring is internal and transparent to notebook code.

## Cache Key Generation

Cache keys are generated from operation parameters (not LLM request content):
- **OCR**: model, prompt, image_hash
- **Grading**: model, question, answer, scheme, marks
- **OCR+Grading**: model, question, scheme, marks, image_hash

Keys are SHA256 hashes ensuring uniqueness and consistency.

## Agents Using Callback-Based Caching

✅ **All agents now use callback-based caching:**
- `ocr_agent` - OCR text extraction
- `grading_agent` - Answer grading (both text and OCR+grading)
- `moderation_agent` - Grade moderation
- `marking_scheme_agent` - Marking scheme extraction
- `annotation_agent` - Bounding box extraction
- `analytics_agent` - Performance reports (student reports use callbacks)

**Note:** Some analytics agents (class overview and question insights) still use manual caching due to their complex sequential workflows with tool calls and image generation. These will be migrated in a future update.
