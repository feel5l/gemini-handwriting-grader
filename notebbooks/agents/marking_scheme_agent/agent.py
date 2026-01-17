"""Marking scheme agent for extracting and verifying marking schemes."""

from typing import List, Tuple, Dict, Any
from google.genai import types
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.google_search_tool import GoogleSearchTool
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry
from ..caching_callback import (
    create_marking_scheme_cache_callbacks,
    create_marking_scheme_verification_cache_callbacks,
    create_verification_searcher_cache_callbacks
)

# Setup environment and logging
logger = setup_agent_environment(__file__)


# Pydantic models for extraction
class Question(BaseModel):
    """Question model with marking scheme."""
    
    question_number: str = Field(
        description="Question number (e.g., '1', '2', '22a', 'Q1')"
    )
    question_text: str = Field(
        description="The full question text"
    )
    marking_scheme: str = Field(
        description=(
            "Well-formatted marking scheme using markdown. "
            "Use bullet points (-), numbered lists (1., 2.), "
            "bold (**text**) for key terms, and clear line breaks. "
            "Include point allocations in parentheses "
            "(e.g., '- Key concept explained (2 marks)')."
        )
    )
    marks: int = Field(
        description="Total marks available for this question"
    )


class MarkingSchemeResponse(BaseModel):
    """Response containing extracted marking scheme."""
    
    general_grading_guide: str = Field(
        default="",
        description=(
            "General grading guide for partial marks applicable to "
            "all questions, formatted in markdown"
        ),
    )
    questions: List[Question] = Field(
        description="List of questions with marking schemes and marks"
    )


# Pydantic models for verification
class VerificationItem(BaseModel):
    """Result of verifying a single question."""
    
    question_number: str = Field(
        description="The question identifier (e.g., 'Q1')"
    )
    is_correct: bool = Field(
        description="Whether the question and answer are factually correct"
    )
    feedback: str = Field(
        description="Detailed feedback explaining issues or confirming correctness"
    )
    suggestion: str = Field(
        description="Suggestion for improvement if needed, or 'None' if correct"
    )


class VerificationResponse(BaseModel):
    """Structured verification results."""
    
    items: List[VerificationItem] = Field(
        description="Verification results for all questions"
    )
    general_feedback: str = Field(
        description="Overall feedback on the marking scheme quality"
    )


# Static agent instructions for reuse
MARKING_SCHEME_INSTRUCTION = """Please analyze this marking scheme document and extract structured, well-formatted data.

**FORMATTING REQUIREMENTS for marking_scheme:**
- Use markdown formatting (bullet points -, numbered lists 1., 2., bold **text**)
- Each marking criterion should be on its own line
- Show point allocations clearly (e.g., "- Correct formula (2 marks)")
- Use clear hierarchy with proper indentation for sub-points
- Add line breaks between major sections
- Bold important terms or key concepts
- Make it scannable and easy to read

**EXTRACT:**

1. **GENERAL GRADING GUIDE**: Extract any general grading guide or guidance for partial marks that applies to all/multiple questions (use markdown formatting)

2. **FOR EACH QUESTION**: Extract:
   - Question number (normalize to consistent format)
   - Question text (complete question statement)
   - **Marking scheme** (well-formatted with markdown, bullets, numbering, clear point allocation)
   - Total marks available (must be a positive integer)

**Important Guidelines:**
- When extracting the marking_scheme for each question, incorporate any general grading principles that apply to that question's scoring
- Ensure all questions have non-empty marking schemes
- Validate that mark totals are reasonable (1-100 marks per question)
- Use consistent formatting throughout"""


VERIFICATION_SEARCHER_INSTRUCTION = """You are an expert examiner. Verify the following marking scheme questions and answers for factual correctness using Google Search.

For each question:
1. Check if the question is factually sound.
2. Check if the provided answer key is correct according to real-world facts (use Google Search).
3. Ensure the marking scheme points are relevant and accurate.
4. Provide constructive feedback and suggestions.

Evaluate:
- Whether the facts are accurate.
- Specific feedback citing what you verified.
- A suggestion if the wording or answer can be improved."""


VERIFICATION_FORMATTER_INSTRUCTION = """Format the 'verification_draft' provided by the previous agent into a structured JSON response according to the schema.
Ensure all questions are included in the 'items' list.
Provide an overall 'general_feedback' summary.
**IMPORTANT**: If the source text contains citations in the format '[Title](URL)', you MUST preserve this exact format in the 'feedback' field or 'general_feedback'. Do not simplify them to plain text."""


async def extract_marking_scheme_with_ai(
    markdown_content: str,
    max_retries: int = 3
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extract marking scheme using AI with ADK callback-based caching.
    
    Args:
        markdown_content: Markdown content of the marking scheme document
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (questions_data, general_guide)
        - questions_data: List of question dictionaries
        - general_guide: General grading guide string
        
    Raises:
        Exception: If extraction fails after all retries
    """
    logger.info("Creating marking scheme agent with caching callbacks...")
    
    # Create caching callbacks
    before_callback, after_callback = create_marking_scheme_cache_callbacks(
        markdown_content=markdown_content,
        model="gemini-3-flash-preview"
    )
    
    # Create marking scheme agent with caching callbacks
    marking_scheme_agent_cached = Agent(
        model="gemini-3-flash-preview",
        name="marking_scheme_extractor",
        description="Agent for extracting structured marking schemes from documents.",
        instruction=MARKING_SCHEME_INSTRUCTION,
        output_schema=MarkingSchemeResponse,
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
    
    logger.info("Agent created successfully with caching callbacks")

    user_prompt = f"""**Document Content:**

{markdown_content}
"""
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_prompt)]
    )

    result = await run_agent_with_retry(
        agent=marking_scheme_agent_cached,
        user_content=content,
        app_name="marking_scheme_extractor",
        output_type=MarkingSchemeResponse,
        max_retries=max_retries,
        logger=logger,
    )

    general_guide = result.general_grading_guide
    questions_data = [q.model_dump() for q in result.questions]

    logger.info(f"Successfully extracted {len(questions_data)} questions")
    if general_guide:
        logger.info(f"General grading guide extracted ({len(general_guide)} characters)")

    return questions_data, general_guide


async def verify_marking_scheme_with_ai(
    questions_data: List[Dict[str, Any]],
    max_retries: int = 3
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Verify marking scheme correctness using AI with Google Search and caching.
    
    Creates verification agents dynamically with caching callbacks.
    Both the searcher and formatter agents have caching:
    - Searcher: Caches Google Search results with citations
    - Formatter: Caches final formatted JSON output
    
    Args:
        questions_data: List of question dictionaries to verify
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (verification_items, general_feedback)
        - verification_items: List of verification result dictionaries
        - general_feedback: Overall feedback string
    """
    logger.info("Creating verification agents with caching callbacks...")
    
    # Create caching callbacks for the searcher agent (Google Search + citations)
    before_callback_searcher, after_callback_searcher = create_verification_searcher_cache_callbacks(
        questions_data=questions_data,
        model="gemini-3-flash-preview"
    )
    
    # Create caching callbacks for the formatter agent (final output)
    before_callback_formatter, after_callback_formatter = create_marking_scheme_verification_cache_callbacks(
        questions_data=questions_data,
        model="gemini-3-flash-preview"
    )
    
    # Create searcher agent with caching + citation callbacks
    verifier_searcher = Agent(
        model="gemini-3-flash-preview",
        name="marking_scheme_verifier_searcher",
        description="Agent that verifies marking schemes using Google Search.",
        instruction=VERIFICATION_SEARCHER_INSTRUCTION,
        tools=[GoogleSearchTool()],
        output_key="verification_draft",
        before_model_callback=before_callback_searcher,  # Check cache
        after_model_callback=after_callback_searcher,    # Add citations + save to cache
        generate_content_config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=65535,
        ),
    )
    
    # Create formatter agent with caching callbacks
    verifier_formatter = Agent(
        model="gemini-3-flash-preview",
        name="marking_scheme_verifier_formatter",
        description="Agent that formats verification results into structured JSON.",
        instruction=VERIFICATION_FORMATTER_INSTRUCTION,
        output_schema=VerificationResponse,
        output_key="output",
        before_model_callback=before_callback_formatter,  # Check cache
        after_model_callback=after_callback_formatter,    # Save to cache
        generate_content_config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=65535,
            response_mime_type="application/json",
        ),
    )
    
    # Create sequential agent with both cached agents
    verifier_cached = SequentialAgent(
        name="marking_scheme_verifier",
        description="Sequential agent for marking scheme verification and formatting.",
        sub_agents=[
            verifier_searcher,      # Cached: Google Search + citations
            verifier_formatter      # Cached: Formatted JSON
        ]
    )
    
    logger.info("Verification agents created with caching")
    
    # Prepare content for verification
    questions_text = ""
    for q in questions_data:
        questions_text += (
            f"Question {q.get('question_number')}: "
            f"{q.get('question_text')}\n"
        )
        questions_text += f"Answer/Marking: {q.get('marking_scheme')}\n\n"
        
    user_prompt = f"""**Marking Scheme to Verify:**

{questions_text}
"""
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_prompt)]
    )

    # Run the Sequential Agent with caching
    result = await run_agent_with_retry(
        agent=verifier_cached,
        user_content=content,
        app_name="marking_scheme_verifier",
        output_type=VerificationResponse,
        max_retries=max_retries,
        logger=logger,
    )

    verification_items = [v.model_dump() for v in result.items]
    general_feedback = result.general_feedback
    
    logger.info(f"Sequential verification completed: {len(verification_items)} items checked")
    
    return verification_items, general_feedback
