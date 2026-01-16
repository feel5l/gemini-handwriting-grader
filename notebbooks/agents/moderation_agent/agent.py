"""Moderation agent for ensuring grading consistency and fairness."""

import json
from typing import List, Dict, Any
from google.genai import types
from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry
import grading_utils

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


# Define Moderation Agent
moderation_agent = Agent(
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
)


async def moderate_grades_with_ai(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    entries: List[Dict[str, Any]],
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Moderate grades using the moderation agent.
    
    Args:
        question_text: The question text
        marking_scheme_text: The marking scheme
        total_marks: Total marks available
        entries: List of student entries with marks
        max_retries: Maximum retry attempts
        
    Returns:
        List of moderation results with moderated marks
    """
    # Check cache
    cache_key = None
    try:
        cache_key = grading_utils.get_cache_key(
            "grade_moderator",
            model="gemini-3-pro-preview",
            question=question_text,
            scheme=marking_scheme_text,
            total_marks=total_marks,
            entries=entries
        )
        cached = grading_utils.get_from_cache(cache_key)
        if cached is not None:
            logger.info("Moderation cache hit")
            return cached
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")

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
        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        result = await run_agent_with_retry(
            agent=moderation_agent,
            user_content=content,
            app_name="grading_moderator",
            output_type=ModerationResponse,
            max_retries=max_retries,
            logger=logger
        )
        
        # Validate items length
        if len(result.items) != len(entries):
            logger.warning(
                f"Moderation item count mismatch: "
                f"got {len(result.items)}, expected {len(entries)}"
            )
            raise ValueError("Moderation item count mismatch")
        
        # Sanitize results
        results = []
        for item in result.items:
            item.moderated_mark = max(
                0.0,
                min(float(total_marks), item.moderated_mark)
            )
            results.append(item.model_dump())
        
        # Save to cache
        if cache_key:
            grading_utils.save_to_cache(cache_key, results)
            
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

