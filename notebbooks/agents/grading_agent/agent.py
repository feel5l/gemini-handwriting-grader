"""Grading agent for evaluating student answers."""

from typing import Optional
from google.genai import types
from google.adk.agents import Agent, SequentialAgent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry
from ..caching_callback import (
    create_grading_cache_callbacks,
    create_ocr_cache_callbacks
)

# Setup environment and logging
logger = setup_agent_environment(__file__)


# Pydantic Model
class GradingResult(BaseModel):
    """Pydantic model for grading results."""
    
    extracted_text: str = Field(
        description="The student's answer text as extracted/read"
    )
    similarity_score: float = Field(
        description="Similarity score from 0 to 1"
    )
    mark: float = Field(
        description="Actual mark awarded"
    )
    reasoning: str = Field(
        description="Brief explanation of the score"
    )



async def grade_answer_with_ai(
    question_text: str,
    submitted_answer: str,
    marking_scheme_text: str,
    total_marks: float,
    max_retries: int = 3
) -> GradingResult:
    """
    Grade a student's answer using the grading agent with callback-based caching.
    
    Args:
        question_text: The question text
        submitted_answer: Student's submitted answer
        marking_scheme_text: The marking scheme
        total_marks: Total marks available
        max_retries: Maximum retry attempts
        
    Returns:
        GradingResult with mark and reasoning
    """
    # Create caching callbacks
    before_callback, after_callback = create_grading_cache_callbacks(
        question_text=question_text,
        submitted_answer=submitted_answer,
        marking_scheme_text=marking_scheme_text,
        total_marks=total_marks,
        model="gemini-3-flash-preview"
    )
    
    # Create grading agent with caching callbacks
    grading_agent_cached = Agent(
        model="gemini-3-flash-preview",
        name="grading_expert",
        description="Expert grader for evaluating student answers.",
        instruction=(
            "You are an expert grader. Evaluate the student's answer based on "
            "the provided question, marking scheme, and total marks.\n\n"
            "If this is part of a sequential process (e.g., following OCR), "
            "the student's answer will be the input provided to you. "
            "The Question, Marking Scheme, and Total Marks will be found in "
            "the conversation history (context).\n\n"
            "Ensure you populate the 'extracted_text' field with the student's "
            "answer you evaluated."
        ),
        output_schema=GradingResult,
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
    
    prompt = f"""<QUESTION>
{question_text}
</QUESTION>

<MARKING_SCHEME>
{marking_scheme_text}
</MARKING_SCHEME>

<TOTAL_MARKS>
{total_marks}
</TOTAL_MARKS>

<STUDENT_ANSWER>
{submitted_answer}
</STUDENT_ANSWER>

Provide:
1. extracted_text: The student answer provided above
2. reasoning: Brief explanation of the scoring
3. similarity_score: Score from 0 to 1
4. mark: Actual mark to award (0 to {total_marks})"""

    try:
        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        result = await run_agent_with_retry(
            agent=grading_agent_cached,
            user_content=content,
            app_name="grading_expert",
            output_type=GradingResult,
            max_retries=max_retries,
            logger=logger
        )
        
        # Sanitize results
        result.similarity_score = max(0.0, min(1.0, result.similarity_score))
        result.mark = max(0.0, min(float(total_marks), result.mark))
        
        return result
            
    except Exception as e:
        logger.error(f"Grading failed: {e}")
        return GradingResult(
            extracted_text=submitted_answer,
            similarity_score=0,
            mark=0,
            reasoning=f"Error: Grading failed - {str(e)}"
        )


async def grade_answer_with_ocr_and_ai(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    image_data: bytes,
    max_retries: int = 3
) -> GradingResult:
    """
    Grade a student's answer by first performing OCR then grading with callback-based caching.
    
    Each sub-agent has its own caching callbacks for independent cache management.
    
    Args:
        question_text: The question text
        marking_scheme_text: The marking scheme
        total_marks: Total marks available
        image_data: Raw image bytes
        max_retries: Maximum retry attempts
        
    Returns:
        GradingResult with mark and reasoning
    """
    import hashlib
    
    logger.info("=" * 80)
    logger.info("Starting grade_answer_with_ocr_and_ai")
    logger.info(f"Image size: {len(image_data)} bytes")
    logger.info(f"Total marks: {total_marks}")
    logger.info(f"Question length: {len(question_text)} chars")
    logger.info(f"Marking scheme length: {len(marking_scheme_text)} chars")
    
    # Build the actual prompt that will be sent
    ocr_prompt = f"""<CONTEXT_FOR_GRADING>
<QUESTION>
{question_text}
</QUESTION>
<MARKING_SCHEME>
{marking_scheme_text}
</MARKING_SCHEME>
<TOTAL_MARKS>
{total_marks}
</TOTAL_MARKS>
</CONTEXT_FOR_GRADING>

Please extract the handwritten text from the provided image. 
(Note: The context above is for the subsequent grading step, 
please focus on extracting the text in the image)."""
    
    logger.info("Creating OCR caching callbacks...")
    # Create OCR caching callbacks using the actual prompt
    before_callback_ocr, after_callback_ocr = create_ocr_cache_callbacks(
        prompt=ocr_prompt,
        image_data=image_data,
        model="gemini-3-flash-preview"
    )
    logger.info("OCR caching callbacks created")
    
    # Create grading caching callbacks (for grading agent)
    # Note: We use a placeholder for submitted_answer since OCR will provide it
    image_hash = hashlib.sha256(image_data).hexdigest()
    logger.info(f"Image hash: {image_hash[:16]}")
    
    logger.info("Creating grading caching callbacks...")
    before_callback_grading, after_callback_grading = create_grading_cache_callbacks(
        question_text=question_text,
        submitted_answer=f"[OCR_OUTPUT_{image_hash[:16]}]",  # Unique placeholder
        marking_scheme_text=marking_scheme_text,
        total_marks=total_marks,
        model="gemini-3-flash-preview"
    )
    logger.info("Grading caching callbacks created")
    
    logger.info("Creating OCR agent instance...")
    # Create OCR agent with caching
    ocr_agent_instance = Agent(
        model="gemini-2.5-flash",
        name="ocr_extractor",
        description="Agent for extracting text from images.",
        instruction=(
            "You are an expert OCR assistant. "
            "Extract text from images exactly as requested. "
            "If the image is blank, empty, or contains no readable text, "
            "respond with an empty string or 'No text found'."
        ),
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.5,
            max_output_tokens=10480,
        ),
        before_model_callback=before_callback_ocr,
        after_model_callback=after_callback_ocr
    )
    logger.info("OCR agent instance created")
    
    logger.info("Creating grading agent instance...")
    # Create grading agent with caching
    grading_agent_instance = Agent(
        model="gemini-3-flash-preview",
        name="grading_expert",
        description="Expert grader for evaluating student answers.",
        instruction=(
            "You are an expert grader. Evaluate the student's answer based on "
            "the provided question, marking scheme, and total marks.\n\n"
            "If this is part of a sequential process (e.g., following OCR), "
            "the student's answer will be the input provided to you. "
            "The Question, Marking Scheme, and Total Marks will be found in "
            "the conversation history (context).\n\n"
            "IMPORTANT: If the student's answer is empty, blank, or contains no meaningful text "
            "(e.g., 'No text found', 'Image is blank'), award 0 marks with reasoning "
            "'No answer provided' and set extracted_text to an empty string.\n\n"
            "Ensure you populate the 'extracted_text' field with the student's "
            "answer you evaluated."
        ),
        output_schema=GradingResult,
        output_key="output",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.3,
            max_output_tokens=65535,
            response_mime_type="application/json",
        ),
        before_model_callback=before_callback_grading,
        after_model_callback=after_callback_grading
    )
    logger.info("Grading agent instance created")
    
    logger.info("Creating sequential agent...")
    # Create Sequential Agent with both cached agents
    ocr_grading_agent = SequentialAgent(
        name="ocr_and_grading",
        description=(
            "Sequential agent that first extracts text from an image (OCR) "
            "and then grades it."
        ),
        sub_agents=[ocr_agent_instance, grading_agent_instance]
    )
    logger.info("Sequential agent created")

    try:
        logger.info("Preparing content for sequential agent...")
        content = types.Content(
            role="user",
            parts=[
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=image_data
                    )
                ),
                types.Part(text=ocr_prompt)  # Use the same prompt we cached with
            ]
        )
        logger.info("Content prepared, starting sequential agent execution...")
        
        result = await run_agent_with_retry(
            agent=ocr_grading_agent,
            user_content=content,
            app_name="ocr_and_grading",
            output_type=GradingResult,
            max_retries=max_retries,
            logger=logger
        )
        
        logger.info("Sequential agent completed successfully")
        logger.info(f"Extracted text length: {len(result.extracted_text) if result.extracted_text else 0}")
        logger.info(f"Mark awarded: {result.mark}/{total_marks}")
        logger.info(f"Similarity score: {result.similarity_score}")
        
        # Handle empty OCR results explicitly
        if not result.extracted_text or result.extracted_text.strip() in ["", "No text found", "Image is blank"]:
            logger.warning("OCR returned empty or no text - assigning 0 marks")
            result.extracted_text = ""
            result.similarity_score = 0.0
            result.mark = 0.0
            result.reasoning = "No answer provided (blank or unreadable image)"
        
        # Sanitize results
        result.similarity_score = max(0.0, min(1.0, result.similarity_score))
        result.mark = max(0.0, min(float(total_marks), result.mark))
        
        logger.info(f"Final result - Mark: {result.mark}, Reasoning: {result.reasoning[:100]}")
        logger.info("=" * 80)
        return result

    except Exception as e:
        logger.error(f"OCR+Grading failed with exception: {e}", exc_info=True)
        logger.info("=" * 80)
        return GradingResult(
            extracted_text="",
            similarity_score=0,
            mark=0,
            reasoning=f"Error: OCR+Grading failed - {str(e)}"
        )

