"""Grading agent for evaluating student answers."""

from typing import Optional
from google.genai import types
from google.adk.agents import Agent, SequentialAgent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry
from ..caching_callback import (
    create_grading_cache_callbacks,
    create_ocr_grading_cache_callbacks
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


# Define static Grading Agent (for backward compatibility)
grading_agent = Agent(
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
        max_output_tokens=8192,
        response_mime_type="application/json",
    ),
)


# Define static OCR Agent (for backward compatibility)
ocr_agent = Agent(
    model="gemini-3-flash-preview",
    name="ocr_extractor",
    description="Agent for extracting text from images.",
    instruction=(
        "You are an expert OCR assistant. "
        "Extract text from images exactly as requested."
    ),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,
        top_p=0.5,
        max_output_tokens=4096,
    ),
)


# Define static Sequential Agent for OCR + Grading (for backward compatibility)
ocr_grading_agent = SequentialAgent(
    name="ocr_and_grading",
    description=(
        "Sequential agent that first extracts text from an image (OCR) "
        "and then grades it."
    ),
    sub_agents=[ocr_agent, grading_agent],
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
            max_output_tokens=8192,
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
    
    Args:
        question_text: The question text
        marking_scheme_text: The marking scheme
        total_marks: Total marks available
        image_data: Raw image bytes
        max_retries: Maximum retry attempts
        
    Returns:
        GradingResult with mark and reasoning
    """
    # Create caching callbacks
    before_callback, after_callback = create_ocr_grading_cache_callbacks(
        question_text=question_text,
        marking_scheme_text=marking_scheme_text,
        total_marks=total_marks,
        image_data=image_data,
        model="gemini-3-flash-preview"
    )
    
    # Create OCR agent
    ocr_agent_instance = Agent(
        model="gemini-3-flash-preview",
        name="ocr_extractor",
        description="Agent for extracting text from images.",
        instruction=(
            "You are an expert OCR assistant. "
            "Extract text from images exactly as requested."
        ),
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.5,
            max_output_tokens=4096,
        ),
    )
    
    # Create grading agent
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
            "Ensure you populate the 'extracted_text' field with the student's "
            "answer you evaluated."
        ),
        output_schema=GradingResult,
        output_key="output",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            top_p=0.3,
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
    )
    
    # Create Sequential Agent with caching callbacks
    ocr_grading_agent_cached = SequentialAgent(
        name="ocr_and_grading",
        description=(
            "Sequential agent that first extracts text from an image (OCR) "
            "and then grades it."
        ),
        sub_agents=[ocr_agent_instance, grading_agent_instance],
        before_model_callback=before_callback,
        after_model_callback=after_callback
    )

    prompt = f"""<CONTEXT_FOR_GRADING>
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
                types.Part(text=prompt)
            ]
        )
        
        result = await run_agent_with_retry(
            agent=ocr_grading_agent_cached,
            user_content=content,
            app_name="ocr_and_grading",
            output_type=GradingResult,
            max_retries=max_retries,
            logger=logger
        )
        
        # Sanitize results
        result.similarity_score = max(0.0, min(1.0, result.similarity_score))
        result.mark = max(0.0, min(float(total_marks), result.mark))
        
        return result

    except Exception as e:
        logger.error(f"OCR+Grading failed: {e}")
        return GradingResult(
            extracted_text="",
            similarity_score=0,
            mark=0,
            reasoning=f"Error: OCR+Grading failed - {str(e)}"
        )

