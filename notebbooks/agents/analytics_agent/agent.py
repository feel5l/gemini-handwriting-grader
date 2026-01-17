"""Analytics agent for generating performance reports and insights."""

import os
import json
import uuid
from io import BytesIO
from typing import Optional, Dict, Any, List
from PIL import Image
from google import genai
from google.genai import types
from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent
from pydantic import BaseModel, Field

from ..common import setup_agent_environment, run_agent_with_retry

# Setup environment and logging
logger = setup_agent_environment(__file__)


# ============================================================================
# Student Performance Agent
# ============================================================================

class StudentPerformanceResponse(BaseModel):
    """Structured response for student performance report."""
    
    report_text: str = Field(
        description="The generated performance report text."
    )


# Define static student performance agent (for backward compatibility)
student_performance_agent = Agent(
    model="gemini-3-flash-preview",
    name="student_performance_generator",
    description="Agent for generating individual student performance reports.",
    instruction="""You are an instructor drafting a concise performance report.

Write:
- 2-3 sentence overall summary of strengths and weaknesses.
- One short bullet per question with actionable feedback tied to the marking scheme.
- 2 concrete next-step study suggestions focused on the weakest skills.
Keep it under 220 words and avoid restating the input verbatim.""",
    output_schema=StudentPerformanceResponse,
    output_key="output",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.35,
        top_p=0.9,
        max_output_tokens=1536,
        response_mime_type="application/json",
    ),
)


async def generate_student_report_with_ai(
    student_id: str,
    student_name: str,
    student_class: str,
    total_score: float,
    question_details: str,
    max_retries: int = 3,
) -> str:
    """
    Generate student performance report using AI with ADK callback-based caching.
    
    Args:
        student_id: Student identifier
        student_name: Student name
        student_class: Student class
        total_score: Total score achieved
        question_details: Detailed question-by-question breakdown
        max_retries: Maximum retry attempts
        
    Returns:
        Generated performance report text
    """
    # Import callback creator
    from ..caching_callback import create_analytics_cache_callbacks
    
    # Create caching callbacks
    payload_data = {
        "student_id": str(student_id),
        "question_details": question_details
    }
    before_callback, after_callback = create_analytics_cache_callbacks(
        cache_type="performance_report",
        payload_data=payload_data,
        model="gemini-3-flash-preview"
    )
    
    # Create student performance agent with caching callbacks
    student_performance_agent_cached = Agent(
        model="gemini-3-flash-preview",
        name="student_performance_generator",
        description="Agent for generating personalized student performance reports.",
        instruction=student_performance_agent.instruction,  # Reuse the detailed instruction
        output_schema=StudentPerformanceResponse,
        output_key="output",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
        before_model_callback=before_callback,
        after_model_callback=after_callback
    )

    try:
        user_prompt = f"""Student: {student_id} - {student_name} (Class: {student_class})
Total score: {total_score}

Use the question details, marking schemes, awarded marks, and answers below:
{question_details}
"""
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)]
        )

        result = await run_agent_with_retry(
            agent=student_performance_agent_cached,
            user_content=content,
            app_name="student_performance_generator",
            output_type=StudentPerformanceResponse,
            max_retries=max_retries,
            logger=logger
        )

        return result.report_text

    except Exception as e:
        logger.error(f"Student report generation failed: {e}")
        return f"Report generation failed: {e}"


# ============================================================================
# Class Overview Agent
# ============================================================================

class ClassOverviewResponse(BaseModel):
    """Structured response for class overview report."""
    
    report_text: str = Field(
        description="The generated class overview report text."
    )
    infograph_image_path: Optional[str] = Field(
        default=None,
        description=(
            "File path to the generated infographic image, "
            "or None if generation failed."
        )
    )


def generate_infographic_tool(report_text: str) -> str:
    """
    Generate an infographic image based on report text using NanoBanana.
    
    Args:
        report_text: Report text to visualize
        
    Returns:
        File path of the saved image or error message
    """
    try:
        logger.info("Generating infographic with NanoBanana tool...")
        
        # Initialize client
        api_key = (
            os.getenv("GOOGLE_GENAI_API_KEY") or
            os.getenv("GOOGLE_API_KEY")
        )
        client = genai.Client(vertexai=True, api_key=api_key)
        
        # Define cache directory
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        cache_dir = os.path.join(base_dir, "cache", "class_overview_report")
        os.makedirs(cache_dir, exist_ok=True)
        
        prompt = f"""Create a professional, high-quality infographic summarizing this class performance:
        
        {report_text}
        
        Visual style: Clean, modern, educational. Include charts or icons representing strengths/weaknesses."""
        
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    output_mime_type="image/png",
                    aspect_ratio="16:9"
                )
            )
        )
        
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                try:
                    filename = f"infograph_{uuid.uuid4().hex}.png"
                    image_path = os.path.join(cache_dir, filename)
                    
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(image_path)
                    
                    logger.info(f"Tool saved infographic to {image_path}")
                    return os.path.abspath(image_path)
                except Exception as img_err:
                    logger.error(f"Failed to process/save image data: {img_err}")
                    raise img_err
                
        logger.warning("No image data found in NanoBanana response")
        return "IMAGE_GENERATION_FAILED"
        
    except Exception as e:
        logger.error(f"Infographic tool failed: {e}")
        return f"IMAGE_GENERATION_ERROR: {str(e)}"


class_overview_text_generator = Agent(
    model="gemini-3-flash-preview",
    name="class_overview_text_generator",
    description="Agent for generating class-level performance overview text.",
    instruction="""You are summarizing overall class performance from individual reports.

Write a concise class-level overview (<200 words):
- 4-6 bullets on class strengths and weaknesses
- 3 targeted next-step actions for instruction
- 2 questions/topics to re-teach next
Focus on patterns; do not restate student names or IDs.""",
    output_key="overview_text_draft",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.35,
        top_p=0.9,
        max_output_tokens=1536,
    ),
)


class_overview_infograph_generator = Agent(
    model="gemini-3-flash-preview",
    name="class_overview_infograph_generator",
    description="Orchestrator for creating a class performance infographic.",
    instruction="""You are an expert coordinator.

1.  **Analyze** the provided class overview text.
2.  **Call the 'generate_infographic_tool'** with the overview text to create a visualization.
3.  **Return** a JSON response matching the schema:
    -   'report_text': The exact class overview text provided.
    -   'infograph_image_path': The file path returned by the tool.""",
    tools=[generate_infographic_tool],
    output_schema=ClassOverviewResponse,
    output_key="output",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=2048,
        response_mime_type="application/json",
    ),
)


class_overview_agent = SequentialAgent(
    name="class_overview_agent",
    description="Sequential agent for generating class overview text and infographic.",
    sub_agents=[
        class_overview_text_generator,
        class_overview_infograph_generator
    ]
)


async def generate_class_overview_with_ai(
    summary_payload: Dict[str, Any],
    sample_reports: List[str],
    max_retries: int = 3
) -> ClassOverviewResponse:
    """
    Generate class overview report using AI with ADK callback-based caching.
    
    Args:
        summary_payload: Summary statistics dictionary
        sample_reports: List of sample individual reports
        max_retries: Maximum retry attempts
        
    Returns:
        ClassOverviewResponse with report text and optional infographic path
    """
    # Format sample reports
    report_blob = "\n\n---\n\n".join(sample_reports)

    # Import callback creator
    from ..caching_callback import create_analytics_cache_callbacks
    
    # Create caching callbacks
    payload_data = {
        "summary": summary_payload,
        "reports": report_blob
    }
    before_callback, after_callback = create_analytics_cache_callbacks(
        cache_type="class_overview_report",
        payload_data=payload_data,
        model="gemini-3-flash-preview"
    )
    
    # Create class overview agent with caching callbacks
    class_overview_agent_cached = SequentialAgent(
        name="class_overview_agent",
        description="Sequential agent for generating class overview text and infographic.",
        sub_agents=[
            class_overview_text_generator,
            class_overview_infograph_generator
        ],
        before_model_callback=before_callback,
        after_model_callback=after_callback
    )

    try:
        user_prompt = f"""Key metrics (JSON): {json.dumps(summary_payload)}
Number of sampled individual reports: {len(sample_reports)}
Individual reports (separated by ---):
{report_blob}
"""
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)]
        )

        result = await run_agent_with_retry(
            agent=class_overview_agent_cached,
            user_content=content,
            app_name="class_overview_generator",
            output_type=ClassOverviewResponse,
            max_retries=max_retries,
            logger=logger
        )

        return result

    except Exception as e:
        logger.error(f"Class overview generation failed: {e}")
        return ClassOverviewResponse(
            report_text=(
                "AI-generated class overview temporarily unavailable "
                "due to API issues."
            )
        )


# ============================================================================
# Question Analysis Agent
# ============================================================================

class QuestionAnalysisResponse(BaseModel):
    """Structured response for detailed question analysis."""
    
    report_text: str = Field(
        description=(
            "The generated analysis of question performance, "
            "misconceptions, and patterns."
        )
    )
    infograph_image_path: Optional[str] = Field(
        default=None,
        description="File path to the generated infographic image."
    )


def generate_question_infographic_tool(analysis_text: str) -> str:
    """
    Generate a 'Deep Dive' infographic for question analysis using NanoBanana.
    
    Args:
        analysis_text: Analysis text to visualize
        
    Returns:
        File path of the saved image or error message
    """
    try:
        logger.info("Generating question analysis infographic with NanoBanana tool...")
        
        # Initialize client
        api_key = (
            os.getenv("GOOGLE_GENAI_API_KEY") or
            os.getenv("GOOGLE_API_KEY")
        )
        client = genai.Client(vertexai=True, api_key=api_key)
        
        # Define cache directory
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        cache_dir = os.path.join(base_dir, "cache", "class_overview_report")
        os.makedirs(cache_dir, exist_ok=True)
        
        prompt = f"""Create a professional, high-quality educational infographic titled 'Question Insight'.
        
        Content to visualize (Analysis of ONE specific question):
        {analysis_text}
        
        Visual instructions:
        - Header: Question Title/Topic.
        - Split layout: 'Common Misconceptions' vs 'Key Success Factors'.
        - Use simple icons to represent the core concept of the question.
        - Style: Clean, focused, single-topic educational card."""
        
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    output_mime_type="image/png",
                    aspect_ratio="16:9"
                )
            )
        )
        
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                try:
                    filename = f"infograph_question_{uuid.uuid4().hex}.png"
                    image_path = os.path.join(cache_dir, filename)
                    
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(image_path)
                    
                    logger.info(f"Tool saved question infographic to {image_path}")
                    return os.path.abspath(image_path)
                except Exception as img_err:
                    logger.error(f"Failed to save question image data: {img_err}")
                    raise img_err
                
        logger.warning("No image data found in NanoBanana response")
        return "IMAGE_GENERATION_FAILED"
        
    except Exception as e:
        logger.error(f"Question infographic tool failed: {e}")
        return f"IMAGE_GENERATION_ERROR: {str(e)}"


question_insight_text_generator = Agent(
    model="gemini-3-flash-preview",
    name="question_insight_text_generator",
    description="Agent for analyzing a single question's performance data.",
    instruction="""You are an expert educational analyst.
    
Analyze the provided JSON data for a **SINGLE** question. The data includes stats, the marking scheme, and sample student answers (high vs low scoring).

**OUTPUT REQUIREMENTS:**
Write a concise analysis (approx 150 words) specifically for this question:
1.  **The Hurdle:** What specific concept or keyword did low-scoring students miss? Use the sample "bottom_answers" as evidence.
2.  **The Key:** What did high-scoring students consistently demonstrate? Use "top_answers" as evidence.
3.  **Actionable Tip:** One specific teaching strategy to fix this specific misconception.

**Style:** Focused, specific to this question's content. Do not generalize.""",
    output_key="question_analysis_draft",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1024,
    ),
)


question_insight_infograph_generator = Agent(
    model="gemini-3-flash-preview",
    name="question_insight_infograph_generator",
    description="Orchestrator for creating question analysis infographic.",
    instruction="""You are an expert coordinator.

1.  **Review** the provided question analysis text.
2.  **Call the 'generate_question_infographic_tool'** with this text to create a visualization.
3.  **Return** a JSON response matching the schema:
    -   'report_text': The exact analysis text provided.
    -   'infograph_image_path': The file path returned by the tool.""",
    tools=[generate_question_infographic_tool],
    output_schema=QuestionAnalysisResponse,
    output_key="output",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=1024,
        response_mime_type="application/json",
    ),
)


question_analysis_agent = SequentialAgent(
    name="question_analysis_agent",
    description="Sequential agent for generating question insights and infographic.",
    sub_agents=[
        question_insight_text_generator,
        question_insight_infograph_generator
    ]
)


async def generate_question_insights_with_ai(
    question_data_payload: Dict[str, Any],
    max_retries: int = 3
) -> QuestionAnalysisResponse:
    """
    Generate question-level insights and infographic using AI with ADK callback-based caching.
    
    Args:
        question_data_payload: Question performance data dictionary
        max_retries: Maximum retry attempts
        
    Returns:
        QuestionAnalysisResponse with analysis text and optional infographic path
    """
    # Import callback creator
    from ..caching_callback import create_analytics_cache_callbacks
    
    # Create caching callbacks
    before_callback, after_callback = create_analytics_cache_callbacks(
        cache_type="question_insights",
        payload_data=question_data_payload,
        model="gemini-3-flash-preview"
    )
    
    # Create question analysis agent with caching callbacks
    question_analysis_agent_cached = SequentialAgent(
        name="question_analysis_agent",
        description="Sequential agent for generating question-level insights and infographic.",
        sub_agents=[
            question_insight_text_generator,
            question_insight_infograph_generator
        ],
        before_model_callback=before_callback,
        after_model_callback=after_callback
    )

    try:
        user_prompt = f"""**Question Performance Data (JSON):**
{json.dumps(question_data_payload, indent=2)}
"""
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)]
        )

        result = await run_agent_with_retry(
            agent=question_analysis_agent_cached,
            user_content=content,
            app_name="question_analysis_generator",
            output_type=QuestionAnalysisResponse,
            max_retries=max_retries,
            logger=logger
        )

        return result

    except Exception as e:
        logger.error(f"Question insights generation failed: {e}")
        return QuestionAnalysisResponse(
            report_text=f"AI insights unavailable: {e}"
        )
