"""
File validation utilities for Mastercam PDM.

This module provides validation functions for filenames, file types, and content.
Now supports dynamic regex patterns from admin configuration.
"""

import re
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

# Allowed file types with their magic number signatures for validation
ALLOWED_FILE_TYPES = {
    ".mcam": {
        "signatures": [
            b'\x89HDF\r\n\x1a\n',  # Signature for the commercial version
            b'\x89HDF\x01\x02\x03\x04'  # Example signature for the HLE version
        ]
    },
    ".vnc": {"signatures": None},
    ".emcam": {"signatures": None},
    ".link": {"signatures": None},  # Virtual link files
}


def validate_link_filename_format(
    filename: str,
    pattern_config: Optional[dict] = None
) -> Tuple[bool, str]:
    """
    Validates a link filename using configurable regex pattern.

    Args:
        filename: The link filename to validate (without .link extension)
        pattern_config: Optional dict with 'link_pattern', 'max_stem_length', and 'description'
                       If None, uses default pattern

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_link_filename_format("1234567_ABC123")
        (True, "")
        >>> validate_link_filename_format("invalid")
        (False, "Link name must follow the format...")
    """
    # Check if it has a file extension (shouldn't for links)
    if '.' in filename:
        return False, "Link names cannot have file extensions."

    # Use pattern from config or default
    if pattern_config:
        pattern_str = pattern_config.get('link_pattern', r"^\d{7}(_[A-Z]{3}\d{3})?$")
        max_length = pattern_config.get('max_stem_length', 13)
        description = pattern_config.get('description', 'configured pattern')
    else:
        # Default pattern
        pattern_str = r"^\d{7}(_[A-Z]{3}\d{3})?$"
        max_length = 13
        description = "7 digits, optional underscore + 3 UPPERCASE letters + 3 numbers"

    # Check length limit
    if len(filename) > max_length:
        return False, f"Link name cannot exceed {max_length} characters."

    # Validate against pattern
    try:
        pattern = re.compile(pattern_str)
        if not pattern.match(filename):
            return False, f"Link name must follow the format: {description} (e.g., 1234567_ABC123)."
    except re.error as e:
        logger.error(f"Invalid regex pattern in config: {e}")
        return False, f"Invalid filename pattern configuration: {e}"

    return True, ""


def validate_filename_format(
    filename: str,
    pattern_config: Optional[dict] = None
) -> Tuple[bool, str]:
    """
    Validates a regular file filename format using configurable regex pattern.

    Args:
        filename: The filename to validate (with extension)
        pattern_config: Optional dict with 'file_pattern', 'max_stem_length', and 'description'
                       If None, uses default pattern

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_filename_format("1234567_AB123.mcam")
        (True, "")
        >>> validate_filename_format("toolong1234567890.mcam")
        (False, "Filename (before extension) cannot exceed 15 characters.")
    """
    stem = Path(filename).stem

    # Use pattern from config or default
    if pattern_config:
        pattern_str = pattern_config.get('file_pattern', r"^\d{7}(_[A-Z]{1,3}\d{1,3})?$")
        max_length = pattern_config.get('max_stem_length', 15)
        description = pattern_config.get('description', 'configured pattern')
    else:
        # Default pattern
        pattern_str = r"^\d{7}(_[A-Z]{1,3}\d{1,3})?$"
        max_length = 15
        description = "7 digits, optional underscore + 1-3 UPPERCASE letters + 1-3 numbers"

    # Check length limit
    if len(stem) > max_length:
        return False, f"Filename (before extension) cannot exceed {max_length} characters."

    # Validate against pattern
    try:
        pattern = re.compile(pattern_str)
        if not pattern.match(stem):
            return False, f"Filename must follow the format: {description} (e.g., 1234567_AB123)."
    except re.error as e:
        logger.error(f"Invalid regex pattern in config: {e}")
        return False, f"Invalid filename pattern configuration: {e}"

    return True, ""


async def is_valid_file_type(file: UploadFile) -> bool:
    """
    Validates a file based on its extension and magic number signature.

    This performs two levels of validation:
    1. Checks if the file extension is in ALLOWED_FILE_TYPES
    2. Verifies the file content matches the expected magic numbers (if defined)

    Args:
        file: The uploaded file to validate

    Returns:
        bool: True if file is valid, False otherwise

    Note:
        This function resets the file pointer after reading, so the file
        can be read again later without issues.
    """
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_FILE_TYPES:
        logger.warning(f"File type not allowed: {file_extension}")
        return False

    config = ALLOWED_FILE_TYPES[file_extension]
    signatures = config.get("signatures")

    # If no signatures are defined for this type, we trust the extension
    if not signatures:
        return True

    try:
        # Find the length of the longest signature to know how much to read
        max_len = max(len(s) for s in signatures)
        file_header = await file.read(max_len)

        # Check if the file header starts with ANY of the valid signatures
        for signature in signatures:
            if file_header.startswith(signature):
                return True

        # If no signature matched
        logger.warning(f"File signature mismatch for {file.filename}")
        return False

    except Exception as e:
        logger.error(f"Error validating file type: {e}")
        return False

    finally:
        # IMPORTANT: Reset the file pointer so it can be read again later
        await file.seek(0)


def get_allowed_extensions(allowed_types: Optional[list] = None) -> list:
    """
    Returns a list of allowed file extensions.

    Args:
        allowed_types: Optional list of allowed extensions from config.
                      If None, uses default ALLOWED_FILE_TYPES

    Returns:
        List of allowed file extensions (e.g., ['.mcam', '.vnc', '.emcam'])
    """
    if allowed_types:
        return [ext for ext in allowed_types if ext != '.link']
    return [ext for ext in ALLOWED_FILE_TYPES.keys() if ext != '.link']


def get_pattern_config_from_service(admin_config_service, repo_id: Optional[str] = None) -> Optional[dict]:
    """
    Get filename pattern configuration from admin config service.

    Args:
        admin_config_service: AdminConfigService instance
        repo_id: Optional repository ID (uses first repo if not specified)

    Returns:
        Dict with pattern configuration or None if not available
    """
    if not admin_config_service:
        return None

    try:
        config = admin_config_service.get_config()

        # Get repository config
        if repo_id:
            repo_config = admin_config_service.get_repository_config(repo_id)
        else:
            # Use first repository if no ID specified
            repo_config = config.repositories[0] if config.repositories else None

        if not repo_config:
            return None

        # Get filename pattern
        pattern = admin_config_service.get_filename_pattern(repo_config.filename_pattern_id)
        if not pattern:
            return None

        # Return pattern config as dict
        return {
            'link_pattern': pattern.link_pattern,
            'file_pattern': pattern.file_pattern,
            'max_stem_length': pattern.max_stem_length,
            'description': pattern.description
        }

    except Exception as e:
        logger.error(f"Error getting pattern config: {e}")
        return None
