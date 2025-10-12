"""
File validation utilities for Mastercam PDM.

This module provides validation functions for filenames, file types, and content.
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


def validate_link_filename_format(filename: str) -> Tuple[bool, str]:
    """
    Validates a link filename - no extension allowed, must be exactly 7digits_3letters_3numbers.

    Args:
        filename: The link filename to validate (without .link extension)

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

    # Check length limit
    MAX_LENGTH = 13  # 7 digits + 1 underscore + 3 letters + 3 numbers
    if len(filename) > MAX_LENGTH:
        return False, f"Link name cannot exceed {MAX_LENGTH} characters."

    # Stricter pattern for links: exactly 7 digits, underscore, exactly 3 letters, exactly 3 numbers
    pattern = re.compile(r"^\d{7}(_[A-Z]{3}\d{3})?$")
    if not pattern.match(filename):
        return False, "Link name must follow the format: 7digits_3LETTERS3numbers (e.g., 1234567_ABC123)."

    return True, ""


def validate_filename_format(filename: str) -> Tuple[bool, str]:
    """
    Validates a regular file filename format.

    Args:
        filename: The filename to validate (with extension)

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> validate_filename_format("1234567_AB123.mcam")
        (True, "")
        >>> validate_filename_format("toolong1234567890.mcam")
        (False, "Filename (before extension) cannot exceed 15 characters.")
    """
    stem = Path(filename).stem

    # Check length limit
    MAX_LENGTH = 15
    if len(stem) > MAX_LENGTH:
        return False, f"Filename (before extension) cannot exceed {MAX_LENGTH} characters."

    # Updated pattern to be more flexible for regular files
    # Format: 7 digits, optionally followed by underscore and 1-3 letters and 1-3 numbers
    pattern = re.compile(r"^\d{7}(_[A-Z]{1,3}\d{1,3})?$")
    if not pattern.match(stem):
        return False, "Filename must follow the format: 7digits_1-3LETTERS1-3numbers (e.g., 1234567_AB123)."

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


def get_allowed_extensions() -> list:
    """
    Returns a list of allowed file extensions.

    Returns:
        List of allowed file extensions (e.g., ['.mcam', '.vnc', '.emcam'])
    """
    return [ext for ext in ALLOWED_FILE_TYPES.keys() if ext != '.link']
