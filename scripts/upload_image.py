#!/usr/bin/env python3
"""
Upload image to fal.ai storage for API use
Uploads local images and returns public URL
"""

import sys
import os
import json
import urllib.request
from urllib.parse import quote
from pathlib import Path

def load_api_key() -> str:
    """Load API key from config file"""
    config_path = os.path.expanduser("~/.config/fal-skill/.env")
    if not os.path.exists(config_path):
        raise ValueError("API key not found. Run /fal-setup first.")

    with open(config_path, 'r') as f:
        for line in f:
            if line.startswith('FAL_KEY='):
                return line.strip().split('=', 1)[1]

    raise ValueError("FAL_KEY not found in config file")

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
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in valid_extensions:
        raise ValueError(f"Invalid file format. Supported: {', '.join(valid_extensions)}")

    # Load API key
    api_key = load_api_key()

    # Generate target path (use filename with timestamp to avoid collisions)
    import time
    filename = Path(file_path).name
    target_path = f"uploads/{int(time.time())}_{filename}"

    # Build upload URL
    upload_url = f"https://api.fal.ai/v1/serverless/files/file/local/{quote(target_path)}"

    # Read file content
    with open(file_path, 'rb') as f:
        file_content = f.read()

    # Create multipart form data
    boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
    body = []
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="file_upload"; filename="{filename}"'.encode())
    body.append(f'Content-Type: application/octet-stream'.encode())
    body.append(b'')
    body.append(file_content)
    body.append(f'--{boundary}--'.encode())
    body_bytes = b'\r\n'.join(body)

    # Create request
    request = urllib.request.Request(
        upload_url,
        data=body_bytes,
        headers={
            'Authorization': f'Key {api_key}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )

    # Execute upload
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode())

            # fal.ai returns the URL in the response
            # The uploaded file is accessible at the target_path
            if 'url' in response_data:
                return response_data['url']
            else:
                # Construct URL from target_path
                # fal.ai serves files at: https://v3.fal.media/files/{target_path}
                return f"https://v3.fal.media/files/{target_path}"

    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")

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
