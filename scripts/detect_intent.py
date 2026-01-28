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

    # Upscaling (Priority 1 - most specific keywords)
    upscale_keywords = ["upscale", "enhance quality", "improve quality", "increase resolution", "make larger", "2x", "4x", "8x"]
    if any(kw in text_lower for kw in upscale_keywords):
        image_ref = extract_image_reference(text)
        video_ref = extract_video_reference(text)
        scale = extract_scale_hint(text)

        if video_ref:
            return {
                "skill": "fal-upscale",
                "args": [video_ref, f"--scale {scale}", "--type video"]
            }
        elif image_ref:
            return {
                "skill": "fal-upscale",
                "args": [image_ref, f"--scale {scale}", "--type image"]
            }

    # Background removal (Priority 2 - before editing to avoid "remove" conflict)
    bg_keywords = ["remove background", "transparent background", "remove bg", "cut out", "make transparent"]
    if any(kw in text_lower for kw in bg_keywords):
        image_ref = extract_image_reference(text)
        return {
            "skill": "fal-remove-bg",
            "args": [image_ref] if image_ref else []
        }

    # Video generation (Priority 3 for video keywords)
    video_keywords = ["video", "animate", "animation", "motion", "movie", "clip", "footage", "video of", "moving"]
    if any(kw in text_lower for kw in video_keywords):
        # Check if image-to-video or text-to-video
        image_ref = extract_image_reference(text)
        duration = extract_duration_hint(text)
        aspect_ratio = extract_aspect_ratio(text)

        if image_ref:
            return {
                "skill": "fal-generate-video",
                "args": [text, f"--image-url {image_ref}", f"--duration {duration}", f"--aspect-ratio {aspect_ratio}"]
            }
        else:
            return {
                "skill": "fal-generate-video",
                "args": [text, f"--duration {duration}", f"--aspect-ratio {aspect_ratio}"]
            }

    # Advanced editing (Priority 4)
    editing_keywords = {
        "colorize": ["colorize", "add color", "color this", "make colorful", "color the photo"],
        "relight": ["relight", "change lighting", "different light", "lighting", "light it"],
        "reseason": ["reseason", "change season", "make winter", "make summer", "make spring", "make fall"],
        "restore": ["restore", "fix photo", "repair photo", "enhance old", "restore old", "fix damaged"],
        "restyle": ["restyle", "change style", "artistic style", "make it look", "style transfer"],
        "inpaint": ["fill in", "repair part", "inpaint", "fill area"],
        "outpaint": ["expand", "extend", "outpaint", "make bigger", "expand borders"],
        "add-object": ["add", "insert", "place", "put in"],
        "remove-object": ["remove", "erase", "delete", "get rid of", "take out"]
    }

    for operation, keywords in editing_keywords.items():
        if any(kw in text_lower for kw in keywords):
            image_ref = extract_image_reference(text)
            if not image_ref:
                # If no image found, might be a video request, continue checking
                continue

            return {
                "skill": "fal-edit-photo",
                "args": [image_ref, f"--operation {operation}", f"--prompt \"{text}\""]
            }

    # Text-to-image (default fallback)
    size = "square_hd"  # default
    if "portrait" in text_lower:
        size = "portrait_16_9"
    elif "landscape" in text_lower:
        size = "landscape_16_9"
    elif "square" in text_lower:
        size = "square_hd"

    quality = "balanced"  # default
    if "fast" in text_lower or "quick" in text_lower:
        quality = "fast"
    elif "high quality" in text_lower or "detailed" in text_lower:
        quality = "high"

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

def extract_duration_hint(text: str) -> int:
    """
    Extract video duration from text (5 or 10 seconds)

    Args:
        text: Text containing duration hint

    Returns:
        Duration in seconds (5 or 10)
    """
    # Match patterns like "10 seconds", "5 second", "10s", "5s"
    # Use word boundary after 's' to avoid matching 'second' multiple times
    match = re.search(r'(\d+)\s*(?:seconds?|secs?|s)(?:\s|$)', text, re.I)
    if match:
        duration = int(match.group(1))
        return 10 if duration >= 10 else 5

    # Default to 5 seconds (cheaper)
    return 5

def extract_aspect_ratio(text: str) -> str:
    """
    Extract aspect ratio hint from text

    Args:
        text: Text containing aspect ratio hint

    Returns:
        Aspect ratio string (e.g., '16:9', '9:16', '1:1')
    """
    text_lower = text.lower()

    # Explicit ratios
    ratio_map = {
        "16:9": ["16:9", "widescreen", "landscape", "horizontal", "wide"],
        "9:16": ["9:16", "vertical", "portrait", "phone", "tall", "tiktok"],
        "1:1": ["1:1", "square", "instagram"],
        "4:3": ["4:3", "classic", "standard"],
        "3:4": ["3:4"]
    }

    for ratio, keywords in ratio_map.items():
        if any(kw in text_lower for kw in keywords):
            return ratio

    # Default to 16:9 (most common)
    return "16:9"

def extract_video_reference(text: str) -> str:
    """
    Extract video URL or path from text

    Args:
        text: Text containing video reference

    Returns:
        Video URL or file path, or None if not found
    """
    # Match video URLs
    video_url_match = re.search(r'https?://[^\s]+\.(mp4|mov|avi|webm|mkv)', text, re.I)
    if video_url_match:
        return video_url_match.group(0)

    # Match file paths
    video_path_match = re.search(r'[\w./~-]+\.(mp4|mov|avi|webm|mkv)', text, re.I)
    if video_path_match:
        return video_path_match.group(0)

    return None

def extract_scale_hint(text: str) -> int:
    """
    Extract upscale factor from text (2, 4, or 8)

    Args:
        text: Text containing scale hint

    Returns:
        Scale factor (2, 4, or 8)
    """
    text_lower = text.lower()

    # Match explicit scale factors
    if "8x" in text_lower or "eight times" in text_lower:
        return 8
    if "4x" in text_lower or "four times" in text_lower or "quadruple" in text_lower:
        return 4
    if "2x" in text_lower or "two times" in text_lower or "double" in text_lower:
        return 2

    # Default to 2x (safest and cheapest)
    return 2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: detect_intent.py <request>", file=sys.stderr)
        sys.exit(1)

    request = " ".join(sys.argv[1:])
    intent = detect_intent(request)
    print(json.dumps(intent))
