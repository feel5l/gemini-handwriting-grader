"""
Caching callback for ADK agents using before_model_callback and after_model_callback pattern.

This module provides caching functions that follow the Google ADK callback pattern.
- before_model_callback: Checks cache and returns cached responses to skip LLM calls
- after_model_callback: Saves responses to cache after successful LLM calls
"""

import os
import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

import grading_utils
from .model_config import ModelConfig

logger = logging.getLogger(__name__)


def is_cache_enabled(agent_type: str) -> bool:
    """
    Check if caching is enabled for a specific agent type.
    
    Args:
        agent_type: Agent type identifier (e.g., 'ocr', 'grading', 'moderation')
        
    Returns:
        True if caching is enabled, False otherwise
    """
    # Check master cache control
    master_enabled = os.getenv("AGENT_CACHE_ENABLED", "TRUE").upper() == "TRUE"
    if not master_enabled:
        logger.debug(f"[{agent_type}] Caching disabled by AGENT_CACHE_ENABLED=FALSE")
        return False
    
    # Check individual agent cache control
    env_var = f"AGENT_CACHE_{agent_type.upper()}"
    agent_enabled = os.getenv(env_var, "TRUE").upper() == "TRUE"
    
    if not agent_enabled:
        logger.debug(f"[{agent_type}] Caching disabled by {env_var}=FALSE")
    
    return agent_enabled


def create_ocr_cache_callbacks(
    prompt: str,
    image_data: bytes,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for OCR operations.
    
    This follows the Google ADK callback pattern:
    - before_model_callback: Checks cache and skips LLM call on hit
    - after_model_callback: Saves response to cache on miss
    
    Args:
        prompt: OCR prompt text
        image_data: Image bytes
        model: Model name (defaults to ModelConfig.OCR_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    if model is None:
        model = ModelConfig.OCR_MODEL
    
    # Check if caching is enabled for OCR
    cache_enabled = is_cache_enabled("ocr")
    
    # Generate cache key from parameters
    image_hash = hashlib.sha256(image_data).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "ocr",
        model=model,
        prompt=prompt,
        image_hash=image_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        logger.debug(f"[{agent_name}] OCR before_callback - checking cache (key: {cache_key[1][:16]}...)")
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] OCR cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Extract result text
                if isinstance(cached_result, dict) and 'result' in cached_result:
                    response_text = cached_result['result']
                else:
                    response_text = str(cached_result)
                
                logger.debug(f"[{agent_name}] Returning cached OCR result ({len(response_text)} chars)")
                
                # Return cached response to skip LLM call
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] OCR cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"[{agent_name}] Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        agent_name = callback_context.agent_name
        logger.debug(f"[{agent_name}] OCR after_callback - saving to cache")
        
        try:
            if llm_response.content and llm_response.content.parts:
                result_text = llm_response.content.parts[0].text
                if result_text:
                    logger.debug(f"[{agent_name}] Saving OCR result to cache ({len(result_text)} chars)")
                    grading_utils.save_to_cache(
                        cache_key,
                        {"result": result_text.strip()},
                        cache_dir=cache_dir
                    )
                    logger.info(f"[{agent_name}] Saved OCR result to cache (key: {cache_key[1][:8]}...)")
                else:
                    logger.warning(f"[{agent_name}] OCR result text is empty")
            else:
                logger.warning(f"[{agent_name}] No content or parts in OCR response")
        except Exception as e:
            logger.warning(f"[{agent_name}] Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_grading_cache_callbacks(
    question_text: str,
    submitted_answer: str,
    marking_scheme_text: str,
    total_marks: float,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for grading operations.
    
    Args:
        question_text: Question text
        submitted_answer: Student's answer
        marking_scheme_text: Marking scheme
        total_marks: Total marks available
        model: Model name (defaults to ModelConfig.GRADING_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    if model is None:
        model = ModelConfig.GRADING_MODEL
    
    # Check if caching is enabled for grading
    cache_enabled = is_cache_enabled("grading")
    
    cache_key = grading_utils.get_cache_key(
        "grade_answer",
        model=model,
        question=question_text,
        answer=submitted_answer,
        scheme=marking_scheme_text,
        marks=total_marks
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        logger.debug(f"[{agent_name}] Grading before_callback - checking cache (key: {cache_key[1][:16]}...)")
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Grading cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached dict to JSON string for response
                if isinstance(cached_result, dict):
                    response_text = json.dumps(cached_result, ensure_ascii=False)
                else:
                    response_text = str(cached_result)
                
                logger.debug(f"[{agent_name}] Returning cached grading result ({len(response_text)} chars)")
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Grading cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"[{agent_name}] Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        agent_name = callback_context.agent_name
        logger.debug(f"[{agent_name}] Grading after_callback - saving to cache")
        
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    logger.debug(f"[{agent_name}] Parsing grading response ({len(response_text)} chars)")
                    # Parse JSON response and save
                    response_data = json.loads(response_text)
                    grading_utils.save_to_cache(
                        cache_key,
                        response_data,
                        cache_dir=cache_dir
                    )
                    logger.info(f"[{agent_name}] Saved grading result to cache (key: {cache_key[1][:8]}...)")
                else:
                    logger.warning(f"[{agent_name}] Grading response text is empty")
            else:
                logger.warning(f"[{agent_name}] No content or parts in grading response")
        except Exception as e:
            logger.warning(f"[{agent_name}] Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_ocr_grading_cache_callbacks(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    image_data: bytes,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for OCR+grading operations.
    
    Args:
        question_text: Question text
        marking_scheme_text: Marking scheme
        total_marks: Total marks available
        image_data: Image bytes
        model: Model name (defaults to ModelConfig.GRADING_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    if model is None:
        model = ModelConfig.GRADING_MODEL
    
    # Check if caching is enabled for grading (OCR+grading uses grading cache control)
    cache_enabled = is_cache_enabled("grading")
    
    image_hash = hashlib.sha256(image_data).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "grade_answer_ocr",
        model=model,
        question=question_text,
        scheme=marking_scheme_text,
        marks=total_marks,
        image_hash=image_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] OCR+Grading cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached dict to JSON string for response
                if isinstance(cached_result, dict):
                    response_text = json.dumps(cached_result, ensure_ascii=False)
                else:
                    response_text = str(cached_result)
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] OCR+Grading cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    # Parse JSON response and save
                    response_data = json.loads(response_text)
                    grading_utils.save_to_cache(
                        cache_key,
                        response_data,
                        cache_dir=cache_dir
                    )
                    logger.debug(f"Saved OCR+Grading result to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback



def create_moderation_cache_callbacks(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    entries: list,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for moderation operations.
    
    Args:
        question_text: Question text
        marking_scheme_text: Marking scheme
        total_marks: Total marks available
        entries: List of student entries
        model: Model name (defaults to ModelConfig.MODERATION_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
    if model is None:
        model = ModelConfig.MODERATION_MODEL
    
    # Check if caching is enabled for moderation
    cache_enabled = is_cache_enabled("moderation")
    
    cache_key = grading_utils.get_cache_key(
        "grade_moderator",
        model=model,
        question=question_text,
        scheme=marking_scheme_text,
        total_marks=total_marks,
        entries=entries
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Moderation cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached list to JSON string for response
                response_text = json.dumps({"items": cached_result}, ensure_ascii=False)
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Moderation cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    # Parse JSON response and save
                    response_data = json.loads(response_text)
                    # Extract items array if present
                    if isinstance(response_data, dict) and 'items' in response_data:
                        items_data = response_data['items']
                    else:
                        items_data = response_data
                    grading_utils.save_to_cache(
                        cache_key,
                        items_data,
                        cache_dir=cache_dir
                    )
                    logger.debug(f"Saved moderation result to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_marking_scheme_cache_callbacks(
    markdown_content: str,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for marking scheme extraction.
    
    Args:
        markdown_content: Markdown content to extract from
        model: Model name (defaults to ModelConfig.MARKING_SCHEME_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
    if model is None:
        model = ModelConfig.MARKING_SCHEME_MODEL
    
    # Check if caching is enabled for marking scheme
    cache_enabled = is_cache_enabled("marking_scheme")
    
    content_hash = hashlib.sha256(markdown_content.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "marking_scheme_extraction",
        model=model,
        content_hash=content_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        logger.debug(f"[{agent_name}] before_callback called - checking cache...")
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Marking scheme cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached tuple to JSON string for response
                # cached_result is (questions_data, general_guide)
                response_data = {
                    "questions": cached_result[0],
                    "general_grading_guide": cached_result[1]
                }
                response_text = json.dumps(response_data, ensure_ascii=False)
                
                logger.debug(f"[{agent_name}] Returning cached response ({len(response_text)} chars)")
                
                # Create a minimal LlmResponse without model_name or usage_metadata
                # to avoid triggering Vertex AI processing
                cached_response = LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
                
                logger.debug(f"[{agent_name}] Cached LlmResponse created successfully")
                return cached_response
            
            logger.debug(f"[{agent_name}] Marking scheme cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.error(f"[{agent_name}] Cache lookup failed: {e}", exc_info=True)
            logger.debug(f"[{agent_name}] Proceeding with LLM call due to cache error")
        
        # Return None to proceed with actual LLM call
        logger.debug(f"[{agent_name}] before_callback returning None - will make LLM call")
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        agent_name = callback_context.agent_name
        logger.debug(f"[{agent_name}] after_callback called - saving to cache...")
        
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    logger.debug(f"[{agent_name}] Parsing response ({len(response_text)} chars)")
                    
                    # Try to parse JSON response
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as json_err:
                        logger.error(f"[{agent_name}] JSON parsing failed: {json_err}")
                        logger.debug(f"[{agent_name}] Response preview: {response_text[:500]}...")
                        logger.debug(f"[{agent_name}] Response end: ...{response_text[-500:]}")
                        # Don't cache invalid JSON
                        return llm_response
                    
                    questions_data = response_data.get("questions", [])
                    general_guide = response_data.get("general_grading_guide", "")
                    
                    if not questions_data:
                        logger.warning(f"[{agent_name}] No questions in response, not caching")
                        return llm_response
                    
                    logger.debug(f"[{agent_name}] Saving {len(questions_data)} questions to cache")
                    grading_utils.save_to_cache(
                        cache_key,
                        (questions_data, general_guide),
                        cache_dir=cache_dir
                    )
                    logger.info(f"[{agent_name}] Saved marking scheme to cache (key: {cache_key[1][:8]}...)")
                else:
                    logger.warning(f"[{agent_name}] No text in response parts")
            else:
                logger.warning(f"[{agent_name}] No content or parts in LLM response")
        except Exception as e:
            logger.error(f"[{agent_name}] Failed to save to cache: {e}", exc_info=True)
        
        logger.debug(f"[{agent_name}] after_callback returning response")
        return llm_response
    
    return before_callback, after_callback


def create_annotation_cache_callbacks(
    image_data: bytes,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for annotation extraction.
    
    Args:
        image_data: Image bytes
        model: Model name (defaults to ModelConfig.ANNOTATION_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
    if model is None:
        model = ModelConfig.ANNOTATION_MODEL
    
    # Check if caching is enabled for annotation
    cache_enabled = is_cache_enabled("annotation")
    
    image_hash = hashlib.sha256(image_data).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "annotation_extraction",
        model=model,
        image_hash=image_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Annotation cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached dict to JSON string for response
                response_text = json.dumps(cached_result, ensure_ascii=False)
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Annotation cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    # Parse JSON response and save
                    response_data = json.loads(response_text)
                    grading_utils.save_to_cache(
                        cache_key,
                        response_data,
                        cache_dir=cache_dir
                    )
                    logger.debug(f"Saved annotation to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_analytics_cache_callbacks(
    cache_type: str,
    payload_data: Any,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for analytics operations.
    
    Args:
        cache_type: Type of analytics operation (e.g., "performance_report", "class_overview_report")
        payload_data: Data to hash for cache key (dict or string)
        model: Model name (defaults to ModelConfig.ANALYTICS_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
    if model is None:
        model = ModelConfig.ANALYTICS_MODEL
    
    # Check if caching is enabled for analytics
    cache_enabled = is_cache_enabled("analytics")
    
    # Generate hash from payload
    if isinstance(payload_data, dict):
        payload_str = json.dumps(payload_data, sort_keys=True)
    else:
        payload_str = str(payload_data)
    
    payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key(
        cache_type,
        model=model,
        payload_hash=payload_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Analytics cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached data to JSON string for response
                if isinstance(cached_result, dict):
                    response_text = json.dumps(cached_result, ensure_ascii=False)
                else:
                    response_text = str(cached_result)
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Analytics cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    # Try to parse as JSON, fallback to string
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError:
                        response_data = response_text
                    
                    grading_utils.save_to_cache(
                        cache_key,
                        response_data,
                        cache_dir=cache_dir
                    )
                    logger.debug(f"Saved analytics result to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_marking_scheme_verification_cache_callbacks(
    questions_data: list,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for marking scheme verification.
    
    This caches the FINAL formatted output (after both searcher and formatter agents).
    The callback should be attached to the formatter agent (last in sequence).
    
    Args:
        questions_data: List of question dictionaries to verify
        model: Model name (defaults to ModelConfig.MARKING_SCHEME_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
    if model is None:
        model = ModelConfig.MARKING_SCHEME_MODEL
    
    # Check if caching is enabled for marking scheme
    cache_enabled = is_cache_enabled("marking_scheme")
    
    # Generate hash from questions data
    questions_str = json.dumps(questions_data, sort_keys=True)
    questions_hash = hashlib.sha256(questions_str.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "marking_scheme_verification",
        model=model,
        questions_hash=questions_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Verification cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Convert cached tuple/list to proper JSON format
                # cached_result is [verification_items, general_feedback] (saved as JSON array)
                if isinstance(cached_result, (list, tuple)) and len(cached_result) == 2:
                    # Extract items and feedback from the cached tuple/list
                    verification_items = cached_result[0]
                    general_feedback = cached_result[1]
                    
                    response_data = {
                        "items": verification_items,
                        "general_feedback": general_feedback
                    }
                    response_text = json.dumps(response_data, ensure_ascii=False)
                elif isinstance(cached_result, dict):
                    # Already in correct format
                    response_text = json.dumps(cached_result, ensure_ascii=False)
                else:
                    logger.warning(f"Unexpected cache format: {type(cached_result)}")
                    response_text = str(cached_result)
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Verification cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save formatted response to cache after LLM call."""
        if not cache_enabled:
            return llm_response
            
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    # Parse JSON response
                    response_data = json.loads(response_text)
                    
                    # Extract items and general_feedback
                    verification_items = response_data.get("items", [])
                    general_feedback = response_data.get("general_feedback", "")
                    
                    if verification_items:
                        grading_utils.save_to_cache(
                            cache_key,
                            (verification_items, general_feedback),
                            cache_dir=cache_dir
                        )
                        logger.debug(f"Saved verification to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_verification_searcher_cache_callbacks(
    questions_data: list,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for verification searcher agent.
    
    This caches the searcher's output (text with citations from Google Search).
    The after_callback combines citation extraction with caching.
    
    Args:
        questions_data: List of question dictionaries to verify
        model: Model name (defaults to ModelConfig.MARKING_SCHEME_MODEL)
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
    if model is None:
        model = ModelConfig.MARKING_SCHEME_MODEL
    
    # Check if caching is enabled for marking scheme
    cache_enabled = is_cache_enabled("marking_scheme")
    
    # Generate hash from questions data
    questions_str = json.dumps(questions_data, sort_keys=True)
    questions_hash = hashlib.sha256(questions_str.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "marking_scheme_verification_searcher",
        model=model,
        questions_hash=questions_hash
    )
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        if not cache_enabled:
            return None
            
        agent_name = callback_context.agent_name
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(
                    f"[{agent_name}] Verification searcher cache hit (key: {cache_key[1][:8]}...)"
                )
                
                # Cached result is the text with citations
                if isinstance(cached_result, dict) and 'result' in cached_result:
                    response_text = cached_result['result']
                else:
                    response_text = str(cached_result)
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Verification searcher cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """
        Combined callback: Add citations from grounding metadata AND save to cache.
        
        This combines citation extraction with caching in a single callback.
        """
        # First, add citations if grounding metadata is present
        if (llm_response.grounding_metadata and
            llm_response.grounding_metadata.grounding_chunks):
            
            if llm_response.content and llm_response.content.parts:
                citation_text = "\n\nCitations:\n"
                found_citations = False
                
                for chunk in llm_response.grounding_metadata.grounding_chunks:
                    if chunk.web:
                        found_citations = True
                        citation_text += (
                            f"  - [{chunk.web.title}]({chunk.web.uri})\n"
                        )
                
                if found_citations:
                    # Append to first text part if it exists
                    for part in llm_response.content.parts:
                        if part.text:
                            part.text += citation_text
                            break
                    else:
                        # Add new part if no text part exists
                        llm_response.content.parts.append(
                            types.Part(text=citation_text)
                        )
        
        # Then, save to cache (with citations included) if enabled
        if cache_enabled:
            try:
                if llm_response.content and llm_response.content.parts:
                    response_text = llm_response.content.parts[0].text
                    if response_text:
                        grading_utils.save_to_cache(
                            cache_key,
                            {"result": response_text},
                            cache_dir=cache_dir
                        )
                        logger.debug(f"Saved verification searcher result to cache (key: {cache_key[1][:8]}...)")
            except Exception as e:
                logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback
