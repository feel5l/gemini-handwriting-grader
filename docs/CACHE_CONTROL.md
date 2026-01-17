# Agent Cache Control

## Quick Start

Control caching for each agent type using `config.yaml`:

```yaml
# Master control - disables ALL agent caching when false
caching:
  enabled: true
  
  # Individual agent cache controls (only apply when enabled=true)
  agents:
    ocr: true
    grading: true
    moderation: true
    marking_scheme: true
    annotation: true
    analytics: true
```

## Configuration Options

| Setting | Default | Controls |
|---------|---------|----------|
| `caching.enabled` | `true` | Master control for all agents |
| `caching.agents.ocr` | `true` | OCR text extraction (`perform_ocr_with_ai`) |
| `caching.agents.grading` | `true` | Answer grading (`grade_answer_with_ai`, `grade_answer_with_ocr_and_ai`) |
| `caching.agents.moderation` | `true` | Grade moderation (`moderate_grades_with_ai`) |
| `caching.agents.marking_scheme` | `true` | Marking scheme extraction/verification |
| `caching.agents.annotation` | `true` | Bounding box extraction (`extract_annotations_with_ai`) |
| `caching.agents.analytics` | `true` | Performance reports and insights |

## Common Use Cases

### Disable All Caching
```yaml
caching:
  enabled: false
```
All agents will bypass cache and make fresh LLM calls.

### Disable Only OCR Caching
```yaml
caching:
  enabled: true
  agents:
    ocr: false
```
OCR will always make fresh calls, other agents use cache normally.

### Disable Grading and Moderation
```yaml
caching:
  enabled: true
  agents:
    grading: false
    moderation: false
```
Useful for testing grading logic changes while keeping other caches active.

### Force Fresh Marking Scheme Extraction
```yaml
caching:
  enabled: true
  agents:
    marking_scheme: false
```
Useful when you've updated the marking scheme document and want to re-extract.

### Production Mode (Default)
```yaml
caching:
  enabled: true
  agents:
    ocr: true
    grading: true
    moderation: true
    marking_scheme: true
    annotation: true
    analytics: true
```
Maximum performance with full caching enabled.

## How It Works

1. **Master Check**: When an agent creates caching callbacks, it first checks `caching.enabled` in config.yaml
2. **Individual Check**: If master is enabled, it checks the specific agent's cache setting
3. **Bypass**: If either check fails, the callbacks return immediately without cache operations
4. **Logging**: Cache status is logged at DEBUG level (set `logging.level: DEBUG` in config.yaml to see)

### Cache Check Flow

```
Agent Function Called
    ↓
Create Cache Callbacks
    ↓
is_cache_enabled(agent_type)
    ↓
Check caching.enabled
    ↓ (if true)
Check caching.agents.{type}
    ↓
Return true/false
    ↓
Callbacks skip cache ops if false
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
1. Check `config.yaml` file exists in project root
2. Verify YAML syntax is correct (use spaces, not tabs)
3. Restart Python kernel/process after changing config.yaml
4. Set `logging.level: DEBUG` in config.yaml to see cache status messages:
   ```
   [ocr_extractor] Caching disabled by config.yaml
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
- Use `logging.level: DEBUG` in config.yaml to verify cache behavior

### Testing
- Disable specific agent caches to test changes
- Force fresh results to ensure you're seeing new behavior
- Re-enable after testing to speed up subsequent runs

### Production
- Enable all caching for maximum performance (default)
- Only disable if you need to force fresh results
- Monitor cache hit rates in logs with `logging.level: INFO`

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
