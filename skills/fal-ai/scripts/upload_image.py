#!/usr/bin/env python3
"""
Upload image to fal.ai storage for API use
Uses fal_client built-in upload functionality
"""

import sys
import os
from pathlib import Path
from lib.utils import load_api_key


def upload_image(file_path: str) -> str:
    """
    Upload image to fal.ai storage and return URL

    Args:
        file_path: Path to local image file

    Returns:
        Public URL of uploaded image

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too large or invalid format
        Exception: If upload fails
    """
    # Validate file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file size (10MB limit)
    size = os.path.getsize(file_path)
    if size > 10 * 1024 * 1024:
        raise ValueError("File too large (>10MB)")

    # Check file format
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg']
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in valid_extensions:
        raise ValueError(f"Invalid file format. Supported: {', '.join(valid_extensions)}")

    # Load API key and set environment variable for fal_client
    api_key = load_api_key()
    os.environ['FAL_KEY'] = api_key

    # Use fal_client's built-in upload
    import fal_client
    url = fal_client.upload_file(file_path)

    return url


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 upload_image.py <file-path>", file=sys.stderr)
        sys.exit(1)

    try:
        url = upload_image(sys.argv[1])
        print(url)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
