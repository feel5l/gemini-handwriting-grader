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
from typing import Optional, Dict, Any, Tuple, Callable
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

import grading_utils
from .model_config import ModelConfig
from .config_loader import config

logger = logging.getLogger(__name__)


def _create_llm_response(text: str) -> LlmResponse:
    """Create a standard LlmResponse from text."""
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=text)]
        )
    )


def _create_generic_callbacks(
    agent_type: str,
    cache_key: Tuple[str, str],
    cache_dir: str,
    response_formatter: Callable[[Any], str] = None,
    response_parser: Callable[[str], Any] = None,
    cache_saver: Callable[[Any], Any] = None
) -> Tuple[Callable, Callable]:
    """
    Generic callback creator that eliminates repetitive code.
    
    Args:
        agent_type: Agent type for cache control (e.g., 'ocr', 'grading')
        cache_key: Cache key tuple (cache_type, hash)
        cache_dir: Cache directory path
        response_formatter: Function to format cached data to response text (default: json.dumps)
        response_parser: Function to parse response text to data (default: json.loads)
        cache_saver: Function to transform parsed data before caching (default: identity)
        
    Returns:
        Tuple of (before_callback, after_callback)
    """
    cache_enabled = is_cache_enabled(agent_type)
    
    if response_formatter is None:
        response_formatter = lambda data: json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
    
    if response_parser is None:
        response_parser = json.loads
    
    if cache_saver is None:
        cache_saver = lambda data: data
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        agent_name = callback_context.agent_name
        
        if not cache_enabled:
            logger.info(f"[{agent_name}] {agent_type.title()} caching DISABLED")
            return None
        
        logger.debug(f"[{agent_name}] Checking cache (key: {cache_key[1][:16]}...)")
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(f"[{agent_name}] Cache hit (key: {cache_key[1][:8]}...)")
                response_text = response_formatter(cached_result)
                logger.debug(f"[{agent_name}] Returning cached result ({len(response_text)} chars)")
                return _create_llm_response(response_text)
            
            logger.debug(f"[{agent_name}] Cache miss, proceeding with LLM call")
            
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
        logger.debug(f"[{agent_name}] Saving to cache")
        
        try:
            if llm_response.content and llm_response.content.parts:
                response_text = llm_response.content.parts[0].text
                if response_text:
                    logger.debug(f"[{agent_name}] Parsing response ({len(response_text)} chars)")
                    response_data = response_parser(response_text)
                    cache_data = cache_saver(response_data)
                    
                    grading_utils.save_to_cache(cache_key, cache_data, cache_dir=cache_dir)
                    logger.info(f"[{agent_name}] Saved to cache (key: {cache_key[1][:8]}...)")
                else:
                    logger.warning(f"[{agent_name}] Response text is empty")
            else:
                logger.warning(f"[{agent_name}] No content or parts in response")
        except Exception as e:
            logger.warning(f"[{agent_name}] Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback


def is_cache_enabled(agent_type: str) -> bool:
    """
    Check if caching is enabled for a specific agent type.
    
    Args:
        agent_type: Agent type identifier (e.g., 'ocr', 'grading', 'moderation')
        
    Returns:
        True if caching is enabled, False otherwise
    """
    # Use config.yaml for cache settings
    enabled = config.is_agent_cache_enabled(agent_type)
    
    if not enabled:
        logger.debug(f"[{agent_type}] Caching disabled in config.yaml")
    
    return enabled


def create_ocr_cache_callbacks(
    prompt: str,
    image_data: bytes,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for OCR operations."""
    model = model or ModelConfig.OCR_MODEL
    image_hash = hashlib.sha256(image_data).hexdigest()
    cache_key = grading_utils.get_cache_key("ocr", model=model, prompt=prompt, image_hash=image_hash)
    
    return _create_generic_callbacks(
        agent_type="ocr",
        cache_key=cache_key,
        cache_dir=cache_dir,
        response_formatter=lambda data: data.get('result', str(data)) if isinstance(data, dict) else str(data),
        response_parser=lambda text: text.strip(),
        cache_saver=lambda data: {"result": data}
    )


def create_grading_cache_callbacks(
    question_text: str,
    submitted_answer: str,
    marking_scheme_text: str,
    total_marks: float,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for grading operations."""
    model = model or ModelConfig.GRADING_MODEL
    cache_key = grading_utils.get_cache_key(
        "grade_answer", model=model, question=question_text,
        answer=submitted_answer, scheme=marking_scheme_text, marks=total_marks
    )
    
    return _create_generic_callbacks(
        agent_type="grading",
        cache_key=cache_key,
        cache_dir=cache_dir
    )


def create_ocr_grading_cache_callbacks(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    image_data: bytes,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for OCR+grading operations."""
    model = model or ModelConfig.GRADING_MODEL
    image_hash = hashlib.sha256(image_data).hexdigest()
    cache_key = grading_utils.get_cache_key(
        "grade_answer_ocr", model=model, question=question_text,
        scheme=marking_scheme_text, marks=total_marks, image_hash=image_hash
    )
    
    return _create_generic_callbacks(
        agent_type="grading",
        cache_key=cache_key,
        cache_dir=cache_dir
    )



def create_moderation_cache_callbacks(
    question_text: str,
    marking_scheme_text: str,
    total_marks: float,
    entries: list,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for moderation operations."""
    model = model or ModelConfig.MODERATION_MODEL
    cache_key = grading_utils.get_cache_key(
        "grade_moderator", model=model, question=question_text,
        scheme=marking_scheme_text, total_marks=total_marks, entries=entries
    )
    
    return _create_generic_callbacks(
        agent_type="moderation",
        cache_key=cache_key,
        cache_dir=cache_dir,
        response_formatter=lambda data: json.dumps({"items": data}, ensure_ascii=False),
        cache_saver=lambda data: data.get('items', data) if isinstance(data, dict) else data
    )


def create_marking_scheme_cache_callbacks(
    markdown_content: str,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for marking scheme extraction."""
    model = model or ModelConfig.MARKING_SCHEME_MODEL
    content_hash = hashlib.sha256(markdown_content.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key("marking_scheme_extraction", model=model, content_hash=content_hash)
    
    def format_response(cached_result):
        """Format cached tuple to JSON response."""
        return json.dumps({
            "questions": cached_result[0],
            "general_grading_guide": cached_result[1]
        }, ensure_ascii=False)
    
    def save_data(response_data):
        """Extract and format data for caching."""
        questions_data = response_data.get("questions", [])
        general_guide = response_data.get("general_grading_guide", "")
        if not questions_data:
            raise ValueError("No questions in response")
        return (questions_data, general_guide)
    
    return _create_generic_callbacks(
        agent_type="marking_scheme",
        cache_key=cache_key,
        cache_dir=cache_dir,
        response_formatter=format_response,
        cache_saver=save_data
    )


def create_annotation_cache_callbacks(
    image_data: bytes,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for annotation extraction."""
    model = model or ModelConfig.ANNOTATION_MODEL
    image_hash = hashlib.sha256(image_data).hexdigest()
    cache_key = grading_utils.get_cache_key("annotation_extraction", model=model, image_hash=image_hash)
    
    return _create_generic_callbacks(
        agent_type="annotation",
        cache_key=cache_key,
        cache_dir=cache_dir
    )


def create_analytics_cache_callbacks(
    cache_type: str,
    payload_data: Any,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for analytics operations."""
    model = model or ModelConfig.ANALYTICS_MODEL
    
    payload_str = json.dumps(payload_data, sort_keys=True) if isinstance(payload_data, dict) else str(payload_data)
    payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key(cache_type, model=model, payload_hash=payload_hash)
    
    def safe_parse(text):
        """Try JSON parse, fallback to string."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    
    return _create_generic_callbacks(
        agent_type="analytics",
        cache_key=cache_key,
        cache_dir=cache_dir,
        response_parser=safe_parse
    )


def create_marking_scheme_verification_cache_callbacks(
    questions_data: list,
    model: str = None,
    cache_dir: str = "../cache"
):
    """Create callbacks for marking scheme verification (final formatted output)."""
    model = model or ModelConfig.MARKING_SCHEME_MODEL
    
    questions_str = json.dumps(questions_data, sort_keys=True)
    questions_hash = hashlib.sha256(questions_str.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key("marking_scheme_verification", model=model, questions_hash=questions_hash)
    
    def format_response(cached_result):
        """Format cached tuple/list to JSON response."""
        if isinstance(cached_result, (list, tuple)) and len(cached_result) == 2:
            return json.dumps({
                "items": cached_result[0],
                "general_feedback": cached_result[1]
            }, ensure_ascii=False)
        elif isinstance(cached_result, dict):
            return json.dumps(cached_result, ensure_ascii=False)
        else:
            logger.warning(f"Unexpected cache format: {type(cached_result)}")
            return str(cached_result)
    
    def save_data(response_data):
        """Extract and format data for caching."""
        verification_items = response_data.get("items", [])
        general_feedback = response_data.get("general_feedback", "")
        if not verification_items:
            raise ValueError("No verification items in response")
        return (verification_items, general_feedback)
    
    return _create_generic_callbacks(
        agent_type="marking_scheme",
        cache_key=cache_key,
        cache_dir=cache_dir,
        response_formatter=format_response,
        cache_saver=save_data
    )


def create_verification_searcher_cache_callbacks(
    questions_data: list,
    model: str = None,
    cache_dir: str = "../cache"
):
    """
    Create callbacks for verification searcher agent.
    
    This caches the searcher's output (text with citations from Google Search).
    The after_callback combines citation extraction with caching.
    """
    model = model or ModelConfig.MARKING_SCHEME_MODEL
    cache_enabled = is_cache_enabled("marking_scheme")
    
    questions_str = json.dumps(questions_data, sort_keys=True)
    questions_hash = hashlib.sha256(questions_str.encode("utf-8")).hexdigest()
    cache_key = grading_utils.get_cache_key("marking_scheme_verification_searcher", model=model, questions_hash=questions_hash)
    
    def before_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Check cache before LLM call."""
        agent_name = callback_context.agent_name
        
        if not cache_enabled:
            logger.info(f"[{agent_name}] Verification searcher caching DISABLED")
            return None
        
        try:
            cached_result = grading_utils.get_from_cache(cache_key, cache_dir=cache_dir)
            
            if cached_result:
                logger.info(f"[{agent_name}] Verification searcher cache hit (key: {cache_key[1][:8]}...)")
                response_text = cached_result.get('result', str(cached_result)) if isinstance(cached_result, dict) else str(cached_result)
                return _create_llm_response(response_text)
            
            logger.debug(f"[{agent_name}] Verification searcher cache miss, proceeding with LLM call")
            
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}, proceeding with LLM call")
        
        return None
    
    def after_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> LlmResponse:
        """Combined callback: Add citations from grounding metadata AND save to cache."""
        # First, add citations if grounding metadata is present
        if (llm_response.grounding_metadata and
            llm_response.grounding_metadata.grounding_chunks):
            
            if llm_response.content and llm_response.content.parts:
                citation_text = "\n\nCitations:\n"
                found_citations = False
                
                for chunk in llm_response.grounding_metadata.grounding_chunks:
                    if chunk.web:
                        found_citations = True
                        citation_text += f"  - [{chunk.web.title}]({chunk.web.uri})\n"
                
                if found_citations:
                    # Append to first text part if it exists
                    for part in llm_response.content.parts:
                        if part.text:
                            part.text += citation_text
                            break
                    else:
                        # Add new part if no text part exists
                        llm_response.content.parts.append(types.Part(text=citation_text))
        
        # Then, save to cache (with citations included) if enabled
        if cache_enabled:
            try:
                if llm_response.content and llm_response.content.parts:
                    response_text = llm_response.content.parts[0].text
                    if response_text:
                        grading_utils.save_to_cache(cache_key, {"result": response_text}, cache_dir=cache_dir)
                        logger.debug(f"Saved verification searcher result to cache (key: {cache_key[1][:8]}...)")
            except Exception as e:
                logger.warning(f"Failed to save to cache: {e}")
        
        return llm_response
    
    return before_callback, after_callback
