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

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(os.path.basename(os.path.dirname(file_path)))

    # Initialize environment and credentials
    try:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(file_path), "../../../")
        )
        env_path = os.path.join(project_root, ".env")
        load_dotenv(env_path)

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
    session_service = InMemorySessionService()
    
    if logger is None:
        logger = logging.getLogger(app_name)

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} for {app_name}")

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

            async for event in runner.run_async(
                session_id=session_id,
                user_id="user",
                new_message=user_content
            ):
                pass

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
