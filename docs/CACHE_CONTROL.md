# Agent Cache Control

## Quick Start

Control caching for each agent type using environment variables in your `.env` file:

```bash
# Master control - disables ALL agent caching when FALSE
AGENT_CACHE_ENABLED=TRUE

# Individual agent cache controls (only apply when AGENT_CACHE_ENABLED=TRUE)
AGENT_CACHE_OCR=TRUE
AGENT_CACHE_GRADING=TRUE
AGENT_CACHE_MODERATION=TRUE
AGENT_CACHE_MARKING_SCHEME=TRUE
AGENT_CACHE_ANNOTATION=TRUE
AGENT_CACHE_ANALYTICS=TRUE
```

## Environment Variables

| Variable | Default | Controls |
|----------|---------|----------|
| `AGENT_CACHE_ENABLED` | `TRUE` | Master control for all agents |
| `AGENT_CACHE_OCR` | `TRUE` | OCR text extraction (`perform_ocr_with_ai`) |
| `AGENT_CACHE_GRADING` | `TRUE` | Answer grading (`grade_answer_with_ai`, `grade_answer_with_ocr_and_ai`) |
| `AGENT_CACHE_MODERATION` | `TRUE` | Grade moderation (`moderate_grades_with_ai`) |
| `AGENT_CACHE_MARKING_SCHEME` | `TRUE` | Marking scheme extraction/verification |
| `AGENT_CACHE_ANNOTATION` | `TRUE` | Bounding box extraction (`extract_annotations_with_ai`) |
| `AGENT_CACHE_ANALYTICS` | `TRUE` | Performance reports and insights |

## Common Use Cases

### Disable All Caching
```bash
AGENT_CACHE_ENABLED=FALSE
```
All agents will bypass cache and make fresh LLM calls.

### Disable Only OCR Caching
```bash
AGENT_CACHE_ENABLED=TRUE
AGENT_CACHE_OCR=FALSE
```
OCR will always make fresh calls, other agents use cache normally.

### Disable Grading and Moderation
```bash
AGENT_CACHE_ENABLED=TRUE
AGENT_CACHE_GRADING=FALSE
AGENT_CACHE_MODERATION=FALSE
```
Useful for testing grading logic changes while keeping other caches active.

### Force Fresh Marking Scheme Extraction
```bash
AGENT_CACHE_ENABLED=TRUE
AGENT_CACHE_MARKING_SCHEME=FALSE
```
Useful when you've updated the marking scheme document and want to re-extract.

### Production Mode (Default)
```bash
AGENT_CACHE_ENABLED=TRUE
# All individual controls default to TRUE
```
Maximum performance with full caching enabled.

## How It Works

1. **Master Check**: When an agent creates caching callbacks, it first checks `AGENT_CACHE_ENABLED`
2. **Individual Check**: If master is enabled, it checks the specific agent's cache variable
3. **Bypass**: If either check fails, the callbacks return immediately without cache operations
4. **Logging**: Cache status is logged at DEBUG level (set `AGENT_LOG_LEVEL=DEBUG` to see)

### Cache Check Flow

```
Agent Function Called
    ↓
Create Cache Callbacks
    ↓
is_cache_enabled(agent_type)
    ↓
Check AGENT_CACHE_ENABLED
    ↓ (if TRUE)
Check AGENT_CACHE_{TYPE}
    ↓
Return TRUE/FALSE
    ↓
Callbacks skip cache ops if FALSE
```

## Testing

Run the test script to verify cache control:

```bash
.venv/bin/python notebbooks/agents/test_cache_control.py
```

Expected output shows:
- ✓ Default behavior (all enabled)
- ✓ Master control disables all agents
- ✓ Individual agent controls work independently
- ✓ Case insensitivity (TRUE, true, True all work)

## Troubleshooting

### Cache not being disabled?
1. Check `.env` file exists in project root
2. Verify variable names are spelled correctly (case-sensitive)
3. Restart Python kernel/process after changing `.env`
4. Set `AGENT_LOG_LEVEL=DEBUG` to see cache status messages:
   ```
   [ocr_extractor] Caching disabled by AGENT_CACHE_OCR=FALSE
   ```

### Want to clear existing cache?
Disabling cache prevents new cache writes/reads but doesn't delete existing files:

```bash
# Clear all cache
rm -rf cache/

# Clear specific agent cache
rm -rf cache/ocr/
rm -rf cache/grade_answer/
rm -rf cache/grade_moderator/
rm -rf cache/marking_scheme_extraction/
rm -rf cache/annotation_extraction/
rm -rf cache/performance_report/
```

## Best Practices

### Development
- Disable caching for agents you're actively debugging
- Keep other agents cached for faster iteration
- Use `AGENT_LOG_LEVEL=DEBUG` to verify cache behavior

### Testing
- Disable specific agent caches to test changes
- Force fresh results to ensure you're seeing new behavior
- Re-enable after testing to speed up subsequent runs

### Production
- Enable all caching for maximum performance (default)
- Only disable if you need to force fresh results
- Monitor cache hit rates in logs with `AGENT_LOG_LEVEL=INFO`

## Implementation Details

### Code Changes

All callback factory functions in `caching_callback.py` now:
1. Call `is_cache_enabled(agent_type)` at creation time
2. Store the result in closure
3. Return early from `before_callback` if disabled (no cache lookup)
4. Return early from `after_callback` if disabled (no cache save)

### Affected Functions
- `create_ocr_cache_callbacks()`
- `create_grading_cache_callbacks()`
- `create_ocr_grading_cache_callbacks()`
- `create_moderation_cache_callbacks()`
- `create_marking_scheme_cache_callbacks()`
- `create_annotation_cache_callbacks()`
- `create_analytics_cache_callbacks()`
- `create_marking_scheme_verification_cache_callbacks()`
- `create_verification_searcher_cache_callbacks()`

### Backward Compatibility
- All variables default to `TRUE`
- Existing code works without any changes
- No breaking changes to agent APIs
- Cache behavior unchanged when variables not set

## Related Documentation

- `README.md` - Agent overview and usage
- `CACHING_REFACTOR.md` - Caching implementation details
- `LOG_LEVEL_QUICK_REF.md` - Log level configuration
