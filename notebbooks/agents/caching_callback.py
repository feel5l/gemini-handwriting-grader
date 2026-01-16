"""
Caching callback for ADK agents using before_model_callback and after_model_callback pattern.

This module provides caching functions that follow the Google ADK callback pattern.
- before_model_callback: Checks cache and returns cached responses to skip LLM calls
- after_model_callback: Saves responses to cache after successful LLM calls
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

import grading_utils

logger = logging.getLogger(__name__)


def create_ocr_cache_callbacks(
    prompt: str,
    image_data: bytes,
    model: str = "gemini-3-flash-preview",
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
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
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
        agent_name = callback_context.agent_name
        
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
                
                # Return cached response to skip LLM call
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] OCR cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        try:
            if llm_response.content and llm_response.content.parts:
                result_text = llm_response.content.parts[0].text
                if result_text:
                    grading_utils.save_to_cache(
                        cache_key,
                        {"result": result_text.strip()},
                        cache_dir=cache_dir
                    )
                    logger.debug(f"Saved OCR result to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_grading_cache_callbacks(
    question_text: str,
    submitted_answer: str,
    marking_scheme_text: str,
    total_marks: float,
    model: str = "gemini-3-flash-preview",
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for grading operations.
    
    Args:
        question_text: Question text
        submitted_answer: Student's answer
        marking_scheme_text: Marking scheme
        total_marks: Total marks available
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
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
        agent_name = callback_context.agent_name
        
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
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Grading cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
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
                    logger.debug(f"Saved grading result to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_ocr_grading_cache_callbacks(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    image_data: bytes,
    model: str = "gemini-3-flash-preview",
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for OCR+grading operations.
    
    Args:
        question_text: Question text
        marking_scheme_text: Marking scheme
        total_marks: Total marks available
        image_data: Image bytes
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
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
    model: str = "gemini-3-pro-preview",
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for moderation operations.
    
    Args:
        question_text: Question text
        marking_scheme_text: Marking scheme
        total_marks: Total marks available
        entries: List of student entries
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
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
    model: str = "gemini-3-flash-preview",
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for marking scheme extraction.
    
    Args:
        markdown_content: Markdown content to extract from
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
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
        agent_name = callback_context.agent_name
        
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
                
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=response_text)]
                    )
                )
            
            logger.debug(f"[{agent_name}] Marking scheme cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Save response to cache after LLM call."""
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    # Parse JSON response and save as tuple
                    response_data = json.loads(response_text)
                    questions_data = response_data.get("questions", [])
                    general_guide = response_data.get("general_grading_guide", "")
                    
                    grading_utils.save_to_cache(
                        cache_key,
                        (questions_data, general_guide),
                        cache_dir=cache_dir
                    )
                    logger.debug(f"Saved marking scheme to cache (key: {cache_key[1][:8]}...)")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def create_annotation_cache_callbacks(
    image_data: bytes,
    model: str = "gemini-3-flash-preview",
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for annotation extraction.
    
    Args:
        image_data: Image bytes
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
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
    model: str = "gemini-3-flash-preview",
    cache_dir: str = "../cache"
):
    """
    Create before and after callback functions for analytics operations.
    
    Args:
        cache_type: Type of analytics operation (e.g., "performance_report", "class_overview_report")
        payload_data: Data to hash for cache key (dict or string)
        model: Model name
        cache_dir: Cache directory
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    import json
    
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
