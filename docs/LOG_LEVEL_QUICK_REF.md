# Agent Log Level Quick Reference

## TL;DR

```yaml
# In config.yaml file
logging:
  level: INFO  # Default, recommended for most use cases
```

## Quick Setup

1. **Edit `config.yaml` file** in project root:
   ```yaml
   logging:
     level: INFO
   ```

2. **Restart your Python kernel/process**

3. **Done!** Logs will now use the specified level

## Log Levels at a Glance

| Level | When to Use | What You See |
|-------|-------------|--------------|
| **DEBUG** | Debugging issues | Everything: cache checks, events, detailed flow |
| **INFO** | Normal use (default) | Important operations, cache hits, completions |
| **WARNING** | Production/batch | Only warnings and errors |
| **ERROR** | Error investigation | Only failures |

## Common Scenarios

### 🔍 Debugging a Problem
```yaml
# In config.yaml
logging:
  level: DEBUG
```
See every operation, cache check, and event.

### ✅ Normal Operations
```yaml
# In config.yaml
logging:
  level: INFO
```
Balanced output showing important milestones.

### 🚀 Production/Batch Processing
```yaml
# In config.yaml
logging:
  level: WARNING
```
Minimal output, only see issues.

### 🔥 Only Show Failures
```yaml
# In config.yaml
logging:
  level: ERROR
```
Silent unless something breaks.

## Test It

```bash
# Test different levels
python notebbooks/agents/test_log_levels.py
```

## Output Examples

### DEBUG (Most Verbose)
```
2024-01-17 10:00:00 - DEBUG - ocr_extractor - [ocr_extractor] OCR before_callback - checking cache...
2024-01-17 10:00:00 - DEBUG - ocr_extractor - [ocr_extractor] OCR cache miss, proceeding with LLM call
2024-01-17 10:00:00 - DEBUG - ocr_extractor - Attempt 1/3 for ocr_extractor
2024-01-17 10:00:01 - DEBUG - ocr_extractor - Starting runner.run_async for ocr_extractor...
2024-01-17 10:00:02 - DEBUG - ocr_extractor - Event 1: StartTurnEvent
2024-01-17 10:00:03 - INFO - ocr_extractor - Runner completed: ocr_extractor (15 events, 3s)
```

### INFO (Balanced - Default)
```
2024-01-17 10:00:00 - INFO - ocr_extractor - [ocr_extractor] OCR cache hit
2024-01-17 10:00:03 - INFO - ocr_extractor - Runner completed: ocr_extractor (15 events, 3s)
2024-01-17 10:00:03 - INFO - ocr_extractor - [ocr_extractor] Saved OCR result to cache
```

### WARNING (Minimal)
```
2024-01-17 10:00:05 - WARNING - grading_expert - OCR returned empty or no text - assigning 0 marks
```

### ERROR (Failures Only)
```
2024-01-17 10:00:10 - ERROR - grading_expert - OCR+Grading failed with exception: Connection timeout
```

## Troubleshooting

### Not seeing logs?
- Check `config.yaml` file exists in project root
- Verify `logging.level` is set correctly
- Restart Python kernel/process
- Try `logging.level: DEBUG` to see everything

### Too many logs?
- Set `logging.level: WARNING` or `logging.level: ERROR`
- Default `INFO` should be reasonable for most cases

### Want different levels per agent?
- Currently not supported (all agents use same level)
- Feature request: per-agent configuration

## More Info

- Full guide: `notebbooks/agents/LOG_LEVEL_GUIDE.md`
- Implementation details: `docs/LOG_LEVEL_IMPLEMENTATION.md`
- Test script: `notebbooks/agents/test_log_levels.py`
