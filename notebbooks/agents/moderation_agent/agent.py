"""Moderation agent for ensuring grading consistency and fairness."""

import json
from typing import List, Dict, Any
from google.genai import types
from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry

# Setup environment and logging
logger = setup_agent_environment(__file__)


# Pydantic Models
class ModerationItem(BaseModel):
    """Individual moderation result for a single student."""
    
    moderated_mark: float = Field(description="Final moderated mark")
    flag: bool = Field(description="True if adjusted or needs review")
    note: str = Field(description="Short reason for moderation")


class ModerationResponse(BaseModel):
    """Response containing all moderation items."""
    
    items: List[ModerationItem] = Field(
        description="List of moderation items"
    )


async def moderate_grades_with_ai(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    entries: List[Dict[str, Any]],
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Moderate grades using the moderation agent with ADK callback-based caching.
    
    Args:
        question_text: The question text
        marking_scheme_text: The marking scheme
        total_marks: Total marks available
        entries: List of student entries with marks
        max_retries: Maximum retry attempts
        
    Returns:
        List of moderation results with moderated marks
    """
    logger.debug(f"Starting moderation for {len(entries)} entries...")
    
    # Import callback creator
    from ..caching_callback import create_moderation_cache_callbacks
    
    # Create caching callbacks
    logger.debug("Creating moderation cache callbacks...")
    before_callback, after_callback = create_moderation_cache_callbacks(
        question_text=question_text,
        marking_scheme_text=marking_scheme_text,
        total_marks=total_marks,
        entries=entries,
        model="gemini-3-pro-preview"
    )
    
    # Create moderation agent with caching callbacks
    logger.debug("Creating moderation agent with caching...")
    moderation_agent_cached = Agent(
        model="gemini-3-pro-preview",
        name="grading_moderator",
        description="Agent to moderate grading results for consistency.",
        instruction=(
            "You are a grading moderator ensuring fairness and consistency. "
            "Review the student responses and marks."
        ),
        output_schema=ModerationResponse,
        output_key="output",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.3,
            max_output_tokens=65535,
            response_mime_type="application/json",
        ),
        before_model_callback=before_callback,
        after_model_callback=after_callback
    )

    entries_json = json.dumps(entries, ensure_ascii=False)
    
    prompt = f"""Question: {question_text}
Marking scheme: {marking_scheme_text}
Total marks: {total_marks}

Review {len(entries)} student responses and ensure similar answers receive similar marks.

Return JSON with "items" array of {len(entries)} objects:
- "moderated_mark": number (0 to {total_marks})
- "flag": boolean (true if adjusted or needs review)
- "note": string (max 120 chars, reference peers by row number)

Responses:
{entries_json}"""

    try:
        logger.debug("Preparing content for moderation agent...")
        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        logger.info("Running moderation agent (this may take a while)...")
        result = await run_agent_with_retry(
            agent=moderation_agent_cached,
            user_content=content,
            app_name="grading_moderator",
            output_type=ModerationResponse,
            max_retries=max_retries,
            logger=logger
        )
        
        logger.info(f"Moderation completed: {len(result.items)} items processed")
        
        # Validate items length
        if len(result.items) != len(entries):
            logger.warning(
                f"Moderation item count mismatch: "
                f"got {len(result.items)}, expected {len(entries)}"
            )
            raise ValueError("Moderation item count mismatch")
        
        # Sanitize results
        logger.debug("Sanitizing moderation results...")
        results = []
        for item in result.items:
            item.moderated_mark = max(
                0.0,
                min(float(total_marks), item.moderated_mark)
            )
            results.append(item.model_dump())
        
        logger.debug(f"Moderation completed successfully for {len(results)} entries")
        return results
            
    except Exception as e:
        logger.error(f"Moderation failed: {e}")
        # Fallback: return original marks
        return [
            {
                "moderated_mark": float(e.get("mark", 0)),
                "flag": False,
                "note": "moderation_error"
            }
            for e in entries
        ]

