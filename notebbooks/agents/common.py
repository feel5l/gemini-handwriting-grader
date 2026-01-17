"""Common utilities for ADK agents."""

import os
import sys
import logging
import time
from typing import Optional, Type, TypeVar
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

T = TypeVar('T')


def setup_agent_environment(file_path: str) -> logging.Logger:
    """
    Set up environment for agents including logging, sys.path, and API keys.
    
    Args:
        file_path: Path to the agent file (typically __file__)
        
    Returns:
        Configured logger instance
    """
    # Setup path to import grading_utils (../../ relative to agent file)
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(file_path), "../../")))

    # Initialize environment and credentials FIRST
    try:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(file_path), "../../../")
        )
        env_path = os.path.join(project_root, ".env")
        load_dotenv(env_path)
    except Exception as e:
        # Log error later after logger is set up
        pass

    # Get log level from environment variable (default: INFO) - AFTER loading .env
    log_level_str = os.getenv("AGENT_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    logger = logging.getLogger(os.path.basename(os.path.dirname(file_path)))
    logger.setLevel(log_level)

    # Continue with API key setup
    try:
        # Ensure GOOGLE_API_KEY is set for ADK
        genai_key = os.getenv("GOOGLE_GENAI_API_KEY")
        api_key = os.getenv("GOOGLE_API_KEY")

        if genai_key and not api_key:
            os.environ["GOOGLE_API_KEY"] = genai_key            
            logger.info("Mapped GOOGLE_GENAI_API_KEY to GOOGLE_API_KEY for ADK")
        elif api_key:
            logger.info("GOOGLE_API_KEY found in environment")
        else:
            logger.error("No API key found! ADK execution will likely fail.")

    except Exception as e:
        logger.error(f"Failed to initialize environment: {e}")
    
    return logger


async def run_agent_with_retry(
    agent,
    user_content: types.Content,
    app_name: str,
    output_type: Type[T],
    max_retries: int = 3,
    logger: Optional[logging.Logger] = None,
    output_key: str = "output"
) -> T:
    """
    Execute an ADK agent with retry logic and return structured output.
    
    Args:
        agent: ADK agent instance to execute
        user_content: User content to send to agent
        app_name: Application name for session management
        output_type: Expected output type (Pydantic model)
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance
        output_key: Key to retrieve output from session state
        
    Returns:
        Structured output of specified type
        
    Raises:
        Exception: If all retry attempts fail
    """
    import asyncio
    
    session_service = InMemorySessionService()
    
    if logger is None:
        logger = logging.getLogger(app_name)

    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries} for {app_name}")

            session_id = f"session_{os.urandom(4).hex()}"
            await session_service.create_session(
                app_name=app_name,
                session_id=session_id,
                user_id="user",
            )

            runner = Runner(
                agent=agent,
                app_name=app_name,
                session_service=session_service,
            )

            logger.debug(f"Starting runner.run_async for {app_name}...")
            event_count = 0
            last_log_time = time.time()
            start_time = time.time()
            
            # Add timeout to detect hangs
            try:
                async def run_with_logging():
                    nonlocal event_count, last_log_time
                    async for event in runner.run_async(
                        session_id=session_id,
                        user_id="user",
                        new_message=user_content
                    ):
                        event_count += 1
                        current_time = time.time()
                        
                        # Log event details (DEBUG level)
                        event_type = type(event).__name__
                        logger.debug(f"Event {event_count}: {event_type}")
                        
                        # Log progress every 30 seconds (INFO level)
                        if current_time - last_log_time >= 30:
                            elapsed = int(current_time - start_time)
                            logger.info(f"Processing {app_name}... {event_count} events, {elapsed}s elapsed")
                            last_log_time = current_time
                        
                        # Check if this is a final response
                        if event.is_final_response():
                            logger.debug(f"Received final response event for {app_name}")
                
                # 600 second timeout for the entire operation (10 minutes for large documents)
                await asyncio.wait_for(run_with_logging(), timeout=600.0)
                elapsed = int(time.time() - start_time)
                logger.info(f"Runner completed: {app_name} ({event_count} events, {elapsed}s)")
                
            except asyncio.TimeoutError:
                elapsed = int(time.time() - start_time)
                logger.error(f"Runner timed out after {elapsed}s (processed {event_count} events)")
                raise TimeoutError(f"Agent execution timed out after {elapsed} seconds")

            session = await session_service.get_session(
                app_name=app_name,
                session_id=session_id,
                user_id="user",
            )
            structured_output = session.state.get(output_key)

            if structured_output:
                if isinstance(structured_output, dict):
                    return output_type(**structured_output)
                if isinstance(structured_output, output_type):
                    return structured_output
            
            logger.warning(
                f"No valid response from agent (Attempt {attempt + 1})"
            )
            if attempt == max_retries - 1:
                raise ValueError("No valid structured response received")

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                logger.info("Retrying...")
                continue
            else:
                raise
