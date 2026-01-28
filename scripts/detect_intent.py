#!/usr/bin/env python3
"""
Intent detection for /fal-generate orchestrator
Analyzes natural language requests and routes to appropriate skill
"""

import re
import sys
import json

def detect_intent(text: str) -> dict:
    """
    Detect generation intent from natural language

    Args:
        text: User's natural language request

    Returns:
        dict with 'skill' and 'args' keys
    """
    text_lower = text.lower()

    # Background removal keywords
    bg_keywords = ["remove background", "transparent", "remove bg", "cut out", "make transparent"]
    if any(kw in text_lower for kw in bg_keywords):
        # Extract image reference
        image_ref = extract_image_reference(text)
        return {
            "skill": "fal-remove-bg",
            "args": [image_ref] if image_ref else []
        }

    # Text-to-image (default)
    # Extract size hints
    size = "square_hd"  # default
    if "portrait" in text_lower:
        size = "portrait_16_9"
    elif "landscape" in text_lower:
        size = "landscape_16_9"
    elif "square" in text_lower:
        size = "square_hd"

    # Extract quality hints
    quality = "balanced"  # default
    if "fast" in text_lower or "quick" in text_lower:
        quality = "fast"
    elif "high quality" in text_lower or "detailed" in text_lower:
        quality = "high"

    # Clean prompt (remove size/quality hints)
    prompt = clean_prompt(text)

    return {
        "skill": "fal-generate-image",
        "args": [prompt, f"--size {size}", f"--quality {quality}"]
    }

def extract_image_reference(text: str) -> str:
    """
    Extract image URL or path from text

    Args:
        text: Text containing image reference

    Returns:
        URL or file path, or None if not found
    """
    # Match URLs
    url_match = re.search(r'https?://[^\s]+', text)
    if url_match:
        return url_match.group(0)

    # Match file paths
    path_match = re.search(r'[\w./~-]+\.(jpg|jpeg|png|webp)', text, re.I)
    if path_match:
        return path_match.group(0)

    return None

def clean_prompt(text: str) -> str:
    """
    Remove size and quality hints from prompt

    Args:
        text: Original prompt with potential hints

    Returns:
        Cleaned prompt text
    """
    # Remove size hints
    text = re.sub(r'\b(portrait|landscape|square)\b', '', text, flags=re.I)
    # Remove quality hints
    text = re.sub(r'\b(fast|quick|high quality|detailed)\b', '', text, flags=re.I)
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: detect_intent.py <request>", file=sys.stderr)
        sys.exit(1)

    request = " ".join(sys.argv[1:])
    intent = detect_intent(request)
    print(json.dumps(intent))
