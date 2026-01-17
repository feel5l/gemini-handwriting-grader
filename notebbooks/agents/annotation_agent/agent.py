"""Annotation agent for extracting bounding boxes from exam images."""

from typing import List
from google.genai import types
from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry
from ..model_config import ModelConfig

# Setup environment and logging
logger = setup_agent_environment(__file__)


# Pydantic models
class BoundingBox(BaseModel):
    """Represents a single bounding box annotation."""
    
    x: int = Field(description="X coordinate of the top-left corner")
    y: int = Field(description="Y coordinate of the top-left corner")
    width: int = Field(description="Width of the bounding box")
    height: int = Field(description="Height of the bounding box")
    label: str = Field(description="Question number (e.g., '1', '2', '3')")


class BoundingBoxResponse(BaseModel):
    """Wrapper class for list of bounding boxes."""
    
    boxes: List[BoundingBox] = Field(
        description="List of bounding boxes for question cells"
    )


# Static instruction for annotation extraction (reusable)
ANNOTATION_INSTRUCTION = """Extract the coordinates of bounding boxes for each question/answer cell from the table in the image.

Instructions:
- Identify all table cells that contain question numbers (like "1", "2", "3", "4", "5", etc.)
- Question IDs may appear in formats such as "Q1", "Q2", "q.1", "q.2" (case-insensitive); capture the full alphanumeric label (without the trailing period)
- Question numbers are typically located in the top-left corner or top area of each cell
- Each bounding box should cover the entire cell area where a student would write their answer
- Include cells with sub-questions (like 22a, 22b, 22c, etc.) as separate bounding boxes
- Do NOT include cells that only contain "XXXXXXX" or are marked as non-answer areas
- Bounding boxes may be adjacent but should not overlap
- For merged cells spanning multiple rows/columns, create one bounding box covering the entire merged area
- Also identify and mark special fields: NAME, ID, CLASS (student information fields)
- Do NOT draw a bounding box if the question label is not placed inside a clear table cell/answer cell

For each bounding box, provide:
- x: X coordinate of the top-left corner of the cell
- y: Y coordinate of the top-left corner of the cell
- width: Width of the entire cell (including answer space)
- height: Height of the entire cell (including answer space)
- label: The question number or field name (e.g., "1", "2", "3", "Q1", "q.1", "NAME", "ID", "CLASS")

Important: 
- Extract the question number text exactly as shown (including letters like "a", "b", "c" for sub-questions)
- Do not include the period after the question number in the label
- Focus on cells where students write answers, not header cells or instruction text
- Ensure NAME, ID, and CLASS fields are properly identified for student information"""



async def extract_annotations_with_ai(
    image_path: str,
    max_retries: int = 3
) -> BoundingBoxResponse:
    """
    Extract annotations using AI with ADK callback-based caching.
    
    Args:
        image_path: Path to the image file
        max_retries: Maximum retry attempts
        
    Returns:
        BoundingBoxResponse with list of bounding boxes
    """
    # Read image data
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except Exception as e:
        logger.error(f"Failed to read image file {image_path}: {e}")
        return BoundingBoxResponse(boxes=[])

    # Import callback creator
    from ..caching_callback import create_annotation_cache_callbacks
    
    # Create caching callbacks
    before_callback, after_callback = create_annotation_cache_callbacks(
        image_data=image_data,
        model=ModelConfig.ANNOTATION_MODEL
    )
    
    # Create annotation agent with caching callbacks
    annotation_agent_cached = Agent(
        model=ModelConfig.ANNOTATION_MODEL,
        name="annotation_extractor",
        description="Agent for extracting bounding boxes from exam images.",
        instruction=ANNOTATION_INSTRUCTION,
        output_schema=BoundingBoxResponse,
        output_key="output",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.5,
            max_output_tokens=65535,
            response_mime_type="application/json",
        ),
        before_model_callback=before_callback,
        after_model_callback=after_callback
    )

    try:
        content = types.Content(
            role="user",
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=image_data
                    )
                ),
                types.Part(text="Extract bounding boxes from this image.")
            ]
        )

        result = await run_agent_with_retry(
            agent=annotation_agent_cached,
            user_content=content,
            app_name="annotation_extractor",
            output_type=BoundingBoxResponse,
            max_retries=max_retries,
            logger=logger
        )
        
        logger.info(
            f"Successfully extracted {len(result.boxes)} boxes"
        )

        return result

    except Exception as e:
        logger.error(f"All extraction attempts failed for {image_path}: {e}")
        # Return empty response to allow partial success in batch processing
        return BoundingBoxResponse(boxes=[])

