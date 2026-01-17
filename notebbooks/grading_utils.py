"""
Common utilities for AI Handwrite Grader notebooks.
Consolidates repeated code across all notebook steps.
"""

import os
import json
import hashlib
import logging
from typing import Tuple, Optional, Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Setup logger for this module
logger = logging.getLogger(__name__)

# Suppress verbose logging from Google libraries
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("google.auth").setLevel(logging.WARNING)
logging.getLogger("google.auth.transport").setLevel(logging.WARNING)
logging.getLogger("google.auth.transport.requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("google.api_core.bidi").setLevel(logging.ERROR)
logging.getLogger("google.api_core.retry").setLevel(logging.ERROR)


# =======================
# Path and Config Setup
# =======================

def setup_paths(prefix: str, data_dir: str, base_dir: str = ".."):
    """
    Generate all standard paths for a grading session.

    Args:
        prefix: Test name prefix (e.g., "VTC Test")
        data_dir: Data files directory name
        base_dir: Base directory relative to notebook (default: "..")

    Returns:
        dict: Dictionary containing all standard paths
    """
    paths = {
        "pdf_file": f"{base_dir}/{data_dir}/{prefix}.pdf",
        "name_list_file": f"{base_dir}/{data_dir}/{prefix} Name List.xlsx",
        "marking_scheme_file": f"{base_dir}/{data_dir}/{prefix} Marking Scheme.xlsx",
    }

    file_name = os.path.splitext(os.path.basename(paths["pdf_file"]))[0]
    base_path = f"{base_dir}/marking_form/{file_name}"

    paths.update({
        "file_name": file_name,
        "base_path": base_path,
        "base_path_images": f"{base_path}/images/",
        "base_path_annotations": f"{base_path}/annotations/",
        "base_path_questions": f"{base_path}/questions",
        "base_path_javascript": f"{base_path}/javascript",
        "base_path_marked_images": f"{base_path}/marked/images/",
        "base_path_marked_pdfs": f"{base_path}/marked/pdf/",
        "base_path_marked_scripts": f"{base_path}/marked/scripts/",
        "cache_dir": f"{base_dir}/cache",
    })

    return paths


def create_directories(paths: dict):
    """Create all necessary directories from paths dictionary."""
    dir_keys = [
        "base_path_images", "base_path_annotations", "base_path_questions",
        "base_path_javascript", "base_path_marked_images",
        "base_path_marked_pdfs", "base_path_marked_scripts", "cache_dir"
    ]
    for key in dir_keys:
        if key in paths:
            os.makedirs(paths[key], exist_ok=True)


# =======================
# Gemini Client Setup
# =======================

def init_gemini_client(env_path: str = "../.env"):
    """
    Initialize Gemini client with API key from .env file.

    Args:
        env_path: Path to .env file

    Returns:
        genai.Client: Initialized Gemini client

    Raises:
        ValueError: If API key is missing or invalid
    """
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")

    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            f"Please set GOOGLE_GENAI_API_KEY in {env_path}\n"
            "Get your API key from: https://aistudio.google.com/apikey"
        )

    client = genai.Client(vertexai=True, api_key=api_key)
    logger.info("✓ Vertex AI Express Mode initialized")
    return client


# =======================
# Caching Functions
# =======================

def get_cache_key(cache_type: str, **params) -> Tuple[str, str]:
    """
    Generate a cache key from parameters.

    Args:
        cache_type: Type of cached operation
        **params: Additional parameters for cache key

    Returns:
        Tuple[str, str]: (cache_type, SHA256 hash)
    """
    try:
        # Include versioning if not present
        if "version" not in params:
            params["version"] = "2.0"
            
        key_data = {"type": cache_type, **params}
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        hash_key = hashlib.sha256(key_str.encode('utf-8')).hexdigest()
        return (cache_type, hash_key)
    except Exception as e:
        logger.warning(f"Error generating cache key: {e}")
        # Fallback for non-serializable params
        fallback_str = f"{cache_type}_{str(params)}"
        hash_key = hashlib.sha256(fallback_str.encode()).hexdigest()
        return (cache_type, hash_key)


def get_from_cache(cache_key: Tuple[str, str], cache_dir: str = "../cache") -> Optional[Any]:
    """
    Retrieve cached result.

    Args:
        cache_key: Tuple of (cache_type, hash_key)
        cache_dir: Cache directory path

    Returns:
        Optional[Any]: Cached data if found, None otherwise
    """
    try:
        cache_type, hash_key = cache_key
        cache_subdir = os.path.join(cache_dir, cache_type)
        cache_file = os.path.join(cache_subdir, f"{hash_key}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None


def save_to_cache(cache_key: Tuple[str, str], data: Any, cache_dir: str = "../cache"):
    """
    Save result to cache with formatted JSON.

    Args:
        cache_key: Tuple of (cache_type, hash_key)
        data: Data to cache
        cache_dir: Cache directory path
    """
    try:
        cache_type, hash_key = cache_key
        cache_subdir = os.path.join(cache_dir, cache_type)
        os.makedirs(cache_subdir, exist_ok=True)
        
        cache_file = os.path.join(cache_subdir, f"{hash_key}.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")


# =======================
# Annotation Loading
# =======================

def load_annotations(annotations_path: str):
    """
    Load and process annotations from JSON file.

    Args:
        annotations_path: Path to annotations.json

    Returns:
        tuple: (annotations_list, annotations_dict, questions)
            - annotations_list: Flattened list of all annotations
            - annotations_dict: Dict keyed by label
            - questions: Sorted list of question labels (excluding NAME, ID, CLASS)
    """
    with open(annotations_path, "r") as f:
        annotations = json.load(f)

    # Flatten annotations to list
    annotations_list = []
    for page in annotations:
        for annotation in annotations[page]:
            annotation["page"] = int(page)
            annotation["left"] = annotation.pop("x")
            annotation["top"] = annotation.pop("y")
            annotations_list.append(annotation)

    # Convert to dict keyed by label
    annotations_dict = {ann["label"]: ann for ann in annotations_list}

    # Extract question labels
    questions = []
    for ann in annotations_list:
        label = ann["label"]
        if label not in questions:
            questions.append(label)

    # Remove metadata labels and sort
    for meta_label in ["NAME", "ID", "CLASS"]:
        if meta_label in questions:
            questions.remove(meta_label)

    questions.sort()
    questions = ["NAME", "ID", "CLASS"] + questions

    return annotations_list, annotations_dict, questions


# =======================
# Student ID Mapping
# =======================

def build_student_id_mapping(base_path_questions: str, base_path_annotations: str):
    """
    Build mapping between pages and student IDs.

    Args:
        base_path_questions: Path to questions directory
        base_path_annotations: Path to annotations directory

    Returns:
        tuple: (pageToStudentId dict, numberOfPages, getStudentId function)
    """
    # Get number of pages from annotations
    with open(os.path.join(base_path_annotations, "annotations.json")) as f:
        data = json.load(f)
        numberOfPage = len(data)

    # Build page to student ID mapping
    pageToStudentId = {}
    id_mark_path = os.path.join(base_path_questions, "ID", "mark.json")
    with open(id_mark_path) as f:
        data = json.load(f)
        for item in data:
            pageToStudentId[item["id"]] = (
                item["overridedMark"] if item["overridedMark"] != "" else item["mark"]
            )

    def getStudentId(page: int) -> str:
        """Get student ID for a given page by searching backwards."""
        for p in range(page, page - numberOfPage, -1):
            if str(p) in pageToStudentId:
                return pageToStudentId[str(p)]
        logger.warning(f"{page} is not in pageToStudentId!")
        return None

    return pageToStudentId, numberOfPage, getStudentId


# =======================
# Validation Functions
# =======================

def validate_required_files(*file_paths):
    """
    Validate that all required files exist.
    
    Args:
        *file_paths: Variable number of file paths to check, or a single paths dictionary
        
    Returns:
        tuple: (is_valid, errors) when individual paths are passed
        list: errors when a paths dictionary is passed (for backward compatibility)
    """
    errors = []
    
    # Handle case where a single paths dictionary is passed
    if len(file_paths) == 1 and isinstance(file_paths[0], dict):
        paths_dict = file_paths[0]
        # Check key files from the paths dictionary
        key_files = ['pdf_file', 'name_list_file', 'marking_scheme_file']
        for key in key_files:
            if key in paths_dict:
                file_path = paths_dict[key]
                if not os.path.exists(file_path):
                    errors.append(f"Required file not found: {file_path}")
        # Return just errors list for backward compatibility with notebooks
        return errors
    else:
        # Handle individual file paths
        for file_path in file_paths:
            if not os.path.exists(file_path):
                errors.append(f"Required file not found: {file_path}")
        
        is_valid = len(errors) == 0
        return is_valid, errors


def validate_student_ids(df):
    """
    Validate that student IDs in DataFrame are unique.
    
    Args:
        df: pandas DataFrame containing student data with 'ID' column
        
    Returns:
        tuple: (is_valid, errors) where is_valid is bool and errors is list of strings
    """
    errors = []
    
    # Check if ID column exists
    if 'ID' not in df.columns:
        errors.append("DataFrame must contain 'ID' column")
        return False, errors
    
    # Check for duplicate IDs
    duplicate_ids = df[df.duplicated(subset=['ID'], keep=False)].sort_values('ID')
    
    if not duplicate_ids.empty:
        errors.append("Duplicate Student IDs detected:")
        for _, row in duplicate_ids.iterrows():
            id_val = row['ID']
            name_val = row.get('NAME', 'Unknown')
            class_val = row.get('CLASS', 'Unknown')
            errors.append(f"  ID: {id_val}, Name: {name_val}, Class: {class_val}")
    
    # Check for missing/null IDs
    null_ids = df[df['ID'].isnull()]
    if not null_ids.empty:
        errors.append(f"Found {len(null_ids)} students with missing/null IDs")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def print_validation_summary(title, is_valid, errors):
    """
    Print a formatted validation summary.
    
    Args:
        title: Title for the validation check
        is_valid: Boolean indicating if validation passed
        errors: List of error messages
    """
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{ '='*60}")
    
    if is_valid:
        print("✅ VALIDATION PASSED")
        print("   All checks completed successfully")
    else:
        print("❌ VALIDATION FAILED")
        print(f"   Found {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    
    print(f"{'='*60}")


# =======================
# Markdown Conversion
# =======================

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to HTML without external libraries.

    Args:
        markdown_text: Markdown formatted text

    Returns:
        str: HTML formatted text
    """
    import re

    if not markdown_text:
        return ""

    html = str(markdown_text)

    # Convert headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Convert bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)

    # Convert bullet points
    lines = html.split('\n')
    in_list = False
    result = []
    for line in lines:
        if re.match(r'^[\*\-\+]\s+', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item = re.sub(r'^[\*\-\+]\s+', '', line)
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')

    html = '\n'.join(result)

    # Convert paragraphs
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = f'<p>{html}</p>'

    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<p>\s*<(h[1-6]|ul)>', r'<\1>', html)
    html = re.sub(r'</(h[1-6]|ul)>\s*</p>', r'</\1>', html)

    return html