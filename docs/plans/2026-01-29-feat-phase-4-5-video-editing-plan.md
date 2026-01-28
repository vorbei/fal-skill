---
title: Phase 4-5 - Video Generation & Advanced Editing
type: feat
date: 2026-01-29
parent_plan: 2026-01-28-fal-skill-roadmap.md
status: ready
branch: feat/phase-4-5-video-editing
---

# Phase 4-5: Video Generation & Advanced Editing

**Goal**: Implement comprehensive video generation and advanced image editing capabilities with proper async workflow support

**Duration**: 3-4 days focused work (18-24 hours)

**Context**: Phases 1-3 complete (image generation, background removal, audio/avatars, queue migration). The async methods (submit_async, get_result, check_status) are now ready for their primary use case: long-running video operations.

---

## Problem Statement

Users need powerful video generation and advanced editing without dealing with:
1. **Long wait times**: Video generation takes 30-120+ seconds per request
2. **Model complexity**: 255+ video models across text-to-video, image-to-video, video-to-video categories
3. **Parameter overload**: Duration, aspect ratio, FPS, quality, motion scale, etc.
4. **Async workflows**: Need to submit jobs and check back later for long operations
5. **Editing complexity**: Fibo Edit suite has 10+ specialized operations with different parameters
6. **Quality vs. cost tradeoffs**: Pro vs. standard modes, resolution choices

**Current Status**: Audio/avatar skills working, no video/editing skills exist
**Target Status**: Three major skills covering video generation, advanced editing, and enhancement

---

## Why Now? (Async Methods Justification)

The queue migration in Phase 3 preserved async methods specifically for this phase:

```python
# Phase 4-5 will heavily use these:
request_id = client.submit_async("fal-ai/kling-video/v1/standard/text-to-video", {...})
# User can do other work...
result = client.get_result("fal-ai/kling-video/v1/standard/text-to-video", request_id)
```

**Video generation timing**:
- Text-to-video (5s): ~30-60 seconds
- Text-to-video (10s): ~60-120 seconds
- Image-to-video: ~45-90 seconds
- Video upscaling: ~30-60 seconds

These long-running operations make async workflows essential for good UX.

---

## Success Metrics

### Must-Have (Core Functionality)
- [x] `/fal-generate-video` works for text-to-video and image-to-video
- [x] `/fal-edit-photo` supports 5+ Fibo Edit operations
- [x] `/fal-upscale` handles image and video upscaling
- [x] Async workflow support (submit, check status, retrieve)
- [x] Progress indication for long operations (30+ seconds)
- [x] Test coverage for video intent detection

### Should-Have (User Experience)
- [x] Duration selection (5s, 10s) with cost warnings
- [ ] Quality mode selection (standard, pro) with comparison
- [x] Aspect ratio presets (16:9, 9:16, 1:1, 4:3, 3:4)
- [x] Clear ETA for video generation
- [ ] Batch operation support for multiple edits
- [ ] Preview mode for expensive operations

### Nice-to-Have (Polish)
- [ ] Video concatenation/stitching
- [ ] Frame extraction from videos
- [ ] Style transfer between videos
- [ ] Background music integration
- [ ] Watermark removal

---

## Technical Approach

### Architecture (Existing + New)

```
User → /fal-generate (Orchestrator)
         ↓
    Intent Detection (detect_intent.py)
         ↓
   ┌─────┴──────┬──────────┬──────────┬──────────┐
   ↓            ↓          ↓          ↓          ↓
Image/Audio   Video     Editing    Upscale    Existing
Skills        Skills    Skills     Skills     Skills
(done)          ↓
         Video Models (255)
         - Kling (O1, 1.5, 2.6): Text-to-video, image-to-video (23 models)
         - Runway Gen-3: Text-to-video turbo
         - Haiper: Fast video generation
              ↓
         Editing Models (349 imageToImage)
         - Fibo Edit: Colorize, relight, reseason, restore, restyle
         - Inpaint/Outpaint: Object add/remove/replace
         - Style Transfer: Artistic transformations
              ↓
         Enhancement Models (19 upscale + 129 videoToVideo)
         - Crystal Upscaler (2x, 4x, 8x)
         - Clarity Upscaler
         - Video enhancers
              ↓
    Python API Client (fal_api.py)
         ↓ (Uses async methods for long operations)
    fal_client.submit() + status() + result()
         ↓
    Response Adapter (self-learning)
```

**Key Design Decision**: Use async workflow for operations >30 seconds

```python
# Fast operations (<30s): Blocking
result = client.run_model(endpoint, data)

# Long operations (30s+): Async
request_id = client.submit_async(endpoint, data)
# Show spinner with status checks
while True:
    status = client.check_status(endpoint, request_id)
    if status["status"] == "COMPLETED":
        break
    # Update UI with progress
result = client.get_result(endpoint, request_id)
```

---

## Implementation Plan

### Task 1: Extend Python CLI for Video Commands ⭐ HIGH PRIORITY

**Objective**: Add subcommands to `scripts/fal_api.py` for video, edit, upscale

**Implementation**:

```python
# Add to scripts/fal_api.py

def handle_video(args, client):
    """
    Video generation (text-to-video or image-to-video)
    Uses async workflow for long operations
    """
    endpoint_id = args.model  # e.g., fal-ai/kling-video/v1/standard/text-to-video

    input_data = {
        "prompt": args.prompt if args.prompt else None,
        "image_url": args.image_url if hasattr(args, 'image_url') else None,
        "duration": args.duration,  # 5 or 10
        "aspect_ratio": args.aspect_ratio,  # 16:9, 9:16, 1:1, etc.
        "negative_prompt": args.negative_prompt
    }

    input_data = {k: v for k, v in input_data.items() if v is not None}

    # Video generation is slow (30-120s), use async workflow
    logger.info(f"⏳ Submitting video generation (ETA: 30-120s)")
    request_id = client.submit_async(endpoint_id, input_data)

    logger.info(f"📋 Request ID: {request_id}")
    logger.info(f"⏳ Generating video... (this may take 1-2 minutes)")

    # Poll for status with progress indication
    import time
    start_time = time.time()
    while True:
        status = client.check_status(endpoint_id, request_id)

        if status.get("status") == "COMPLETED":
            break
        elif status.get("status") == "FAILED":
            error = status.get("error", "Unknown error")
            print(json.dumps({"error": f"Video generation failed: {error}"}), file=sys.stderr)
            sys.exit(1)

        elapsed = int(time.time() - start_time)
        logger.info(f"⏳ Status: {status.get('status', 'IN_QUEUE')} ({elapsed}s elapsed)")

        # Log any progress messages
        for log in status.get("logs", []):
            if "message" in log:
                logger.info(f"📝 {log['message']}")

        time.sleep(5)  # Check every 5 seconds

    # Retrieve final result
    result = client.get_result(endpoint_id, request_id)

    adapter = ResponseAdapter()
    video_url = adapter.extract_result(result, endpoint_id)

    if not video_url:
        print(json.dumps({"error": "Could not extract video URL"}), file=sys.stderr)
        sys.exit(1)

    output = {
        "url": video_url,
        "model": endpoint_id,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "generation_time": int(time.time() - start_time)
    }

    print(json.dumps(output))

def handle_edit(args, client):
    """
    Advanced image editing (Fibo Edit suite)
    Fast operations, can use blocking mode
    """
    endpoint_id = args.model  # e.g., fal-ai/fibo-edit/relight

    input_data = {
        "image_url": args.image_url,
        "prompt": args.prompt if hasattr(args, 'prompt') else None,
        "strength": args.strength if hasattr(args, 'strength') else 0.8
    }

    # Add operation-specific parameters
    if args.operation == "relight":
        input_data["lighting_prompt"] = args.lighting_prompt if hasattr(args, 'lighting_prompt') else None
    elif args.operation == "reseason":
        input_data["season"] = args.season if hasattr(args, 'season') else None
    elif args.operation == "restyle":
        input_data["style_prompt"] = args.style_prompt if hasattr(args, 'style_prompt') else None

    input_data = {k: v for k, v in input_data.items() if v is not None}

    # Editing is fast (<10s), use blocking mode
    result = client.run_model(endpoint_id, input_data)

    adapter = ResponseAdapter()
    image_url = adapter.extract_result(result, endpoint_id)

    output = {
        "url": image_url,
        "model": endpoint_id,
        "operation": args.operation
    }

    print(json.dumps(output))

def handle_upscale(args, client):
    """
    Image or video upscaling
    Video upscaling is slow (30-60s), use async if needed
    """
    endpoint_id = args.model  # e.g., fal-ai/crystal-upscaler

    input_data = {
        "image_url": args.image_url if hasattr(args, 'image_url') else None,
        "video_url": args.video_url if hasattr(args, 'video_url') else None,
        "scale": args.scale,  # 2, 4, or 8
        "creativity": args.creativity if hasattr(args, 'creativity') else 0.35
    }

    input_data = {k: v for k, v in input_data.items() if v is not None}

    # Video upscaling is slow, use async
    if args.video_url:
        logger.info(f"⏳ Submitting video upscale (ETA: 30-60s)")
        request_id = client.submit_async(endpoint_id, input_data)

        import time
        start_time = time.time()
        while True:
            status = client.check_status(endpoint_id, request_id)

            if status.get("status") == "COMPLETED":
                break
            elif status.get("status") == "FAILED":
                error = status.get("error", "Unknown error")
                print(json.dumps({"error": f"Upscale failed: {error}"}), file=sys.stderr)
                sys.exit(1)

            elapsed = int(time.time() - start_time)
            logger.info(f"⏳ Upscaling ({elapsed}s elapsed)")
            time.sleep(5)

        result = client.get_result(endpoint_id, request_id)
    else:
        # Image upscaling is faster, blocking is fine
        result = client.run_model(endpoint_id, input_data)

    adapter = ResponseAdapter()
    result_url = adapter.extract_result(result, endpoint_id)

    output = {
        "url": result_url,
        "model": endpoint_id,
        "scale": args.scale
    }

    print(json.dumps(output))

# Add argparse subcommands
video_parser = subparsers.add_parser('video', help='Video generation')
video_parser.add_argument('--model', required=True)
video_parser.add_argument('--prompt', help='Text prompt for text-to-video')
video_parser.add_argument('--image-url', help='Image URL for image-to-video')
video_parser.add_argument('--duration', type=int, default=5, choices=[5, 10])
video_parser.add_argument('--aspect-ratio', default='16:9',
    choices=['16:9', '9:16', '1:1', '4:3', '3:4'])
video_parser.add_argument('--negative-prompt', help='What to avoid')
video_parser.set_defaults(func=handle_video)

edit_parser = subparsers.add_parser('edit', help='Advanced image editing')
edit_parser.add_argument('--model', required=True)
edit_parser.add_argument('--image-url', required=True)
edit_parser.add_argument('--operation', required=True,
    choices=['colorize', 'relight', 'reseason', 'restore', 'restyle',
             'inpaint', 'outpaint', 'add-object', 'remove-object'])
edit_parser.add_argument('--prompt', help='Editing instruction')
edit_parser.add_argument('--strength', type=float, default=0.8)
edit_parser.add_argument('--lighting-prompt', help='For relight operation')
edit_parser.add_argument('--season', help='For reseason operation',
    choices=['spring', 'summer', 'fall', 'winter'])
edit_parser.add_argument('--style-prompt', help='For restyle operation')
edit_parser.set_defaults(func=handle_edit)

upscale_parser = subparsers.add_parser('upscale', help='Image/video upscaling')
upscale_parser.add_argument('--model', required=True)
upscale_parser.add_argument('--image-url', help='Image to upscale')
upscale_parser.add_argument('--video-url', help='Video to upscale')
upscale_parser.add_argument('--scale', type=int, default=2, choices=[2, 4, 8])
upscale_parser.add_argument('--creativity', type=float, default=0.35)
upscale_parser.set_defaults(func=handle_upscale)
```

**Success Criteria**:
- [x] All 3 subcommands work: `video`, `edit`, `upscale`
- [x] Async workflow works for long operations
- [x] Progress indication shows during generation
- [x] Return structured JSON with URLs
- [x] Handle errors gracefully with clear messages

**Estimated Time**: 6-8 hours

---

### Task 2: Extend Response Adapter for Video/Editing Patterns 🔧 SUPPORTING

**Objective**: Add common video/editing response patterns

**File**: `scripts/lib/adapter.py`

**Implementation**:

```python
# Add to COMMON_PATTERNS list (line 16)
COMMON_PATTERNS = [
    # ... existing patterns ...

    # Video generation patterns (text-to-video, image-to-video)
    "video.url",
    "data.video.url",
    "video_url",
    "output.video.url",
    "result.video.url",
    "videos[0].url",

    # Fibo Edit patterns (image editing)
    "edited_image.url",
    "result.edited_image.url",
    "output.image.url",
    "data.result.url",

    # Upscale patterns
    "upscaled_image.url",
    "upscaled_video.url",
    "enhanced.url",
    "result.enhanced.url",

    # Generic result patterns
    "output_url",
    "result_url",
    "data.output_url",
]
```

**Success Criteria**:
- [x] Adapter recognizes video/editing response formats
- [x] Tests pass with new patterns
- [x] No breaking changes to existing patterns

**Estimated Time**: 1 hour

---

### Task 3: Extend Intent Detection for Video/Editing Keywords ⭐ HIGH PRIORITY

**Objective**: Add intent detection for video, editing, upscaling

**File**: `scripts/detect_intent.py`

**Implementation**:

```python
def detect_intent(text: str) -> dict:
    """Detect generation intent"""
    text_lower = text.lower()

    # Video generation (Priority 1 for video keywords)
    video_keywords = ["video", "animate", "motion", "movie", "clip", "footage", "video of"]
    if any(kw in text_lower for kw in video_keywords):
        # Check if image-to-video or text-to-video
        image_ref = extract_image_reference(text)
        if image_ref:
            return {
                "skill": "fal-generate-video",
                "args": [text, f"--image-url {image_ref}", "--mode image-to-video"]
            }
        else:
            duration = extract_duration_hint(text)  # 5 or 10 seconds
            aspect_ratio = extract_aspect_ratio(text)
            return {
                "skill": "fal-generate-video",
                "args": [text, f"--duration {duration}", f"--aspect-ratio {aspect_ratio}"]
            }

    # Advanced editing (Priority 2)
    editing_keywords = {
        "colorize": ["colorize", "add color", "color this", "make colorful"],
        "relight": ["relight", "change lighting", "different light", "lighting"],
        "reseason": ["reseason", "change season", "make winter", "make summer"],
        "restore": ["restore", "fix photo", "repair", "enhance old"],
        "restyle": ["restyle", "change style", "artistic style", "make it look"],
        "inpaint": ["fill in", "fix", "repair part", "inpaint"],
        "outpaint": ["expand", "extend", "outpaint", "make bigger"],
        "add-object": ["add", "insert", "place"],
        "remove-object": ["remove", "erase", "delete", "get rid of"]
    }

    for operation, keywords in editing_keywords.items():
        if any(kw in text_lower for kw in keywords):
            image_ref = extract_image_reference(text)
            if not image_ref:
                return {"error": "No image reference found for editing"}

            return {
                "skill": "fal-edit-photo",
                "args": [image_ref, f"--operation {operation}", f"--prompt \"{text}\""]
            }

    # Upscaling (Priority 3)
    upscale_keywords = ["upscale", "enhance", "improve quality", "increase resolution", "make larger", "2x", "4x", "8x"]
    if any(kw in text_lower for kw in upscale_keywords):
        image_ref = extract_image_reference(text)
        video_ref = extract_video_reference(text)
        scale = extract_scale_hint(text)  # 2, 4, or 8

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

    # ... continue with existing intents (audio, TTS, etc.)

    # Text-to-image (default fallback)
    size = extract_size_hint(text)
    quality = extract_quality_hint(text)
    prompt = clean_prompt(text)

    return {
        "skill": "fal-generate-image",
        "args": [prompt, f"--size {size}", f"--quality {quality}"]
    }

def extract_duration_hint(text: str) -> int:
    """Extract video duration from text (5 or 10 seconds)"""
    import re

    # Match "10 seconds", "5 second", "10s", "5s"
    match = re.search(r'(\d+)\s*(?:second|sec|s)\b', text, re.I)
    if match:
        duration = int(match.group(1))
        return 10 if duration >= 10 else 5

    # Default to 5 seconds (cheaper)
    return 5

def extract_aspect_ratio(text: str) -> str:
    """Extract aspect ratio hint from text"""
    text_lower = text.lower()

    # Explicit ratios
    ratio_map = {
        "16:9": ["16:9", "widescreen", "landscape", "horizontal"],
        "9:16": ["9:16", "vertical", "portrait", "phone"],
        "1:1": ["1:1", "square", "instagram"],
        "4:3": ["4:3", "classic"],
        "3:4": ["3:4"]
    }

    for ratio, keywords in ratio_map.items():
        if any(kw in text_lower for kw in keywords):
            return ratio

    # Default to 16:9 (most common)
    return "16:9"

def extract_video_reference(text: str) -> str:
    """Extract video URL or path from text"""
    import re

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
    """Extract upscale factor from text (2, 4, or 8)"""
    import re

    # Match "2x", "4x", "8x", "2 times", "double"
    if "8x" in text.lower() or "eight times" in text.lower():
        return 8
    if "4x" in text.lower() or "four times" in text.lower() or "quadruple" in text.lower():
        return 4
    if "2x" in text.lower() or "two times" in text.lower() or "double" in text.lower():
        return 2

    # Default to 2x (safest)
    return 2
```

**Success Criteria**:
- [x] Detects video, editing, upscale intents
- [x] Distinguishes text-to-video vs. image-to-video
- [x] Extracts duration, aspect ratio, scale hints
- [x] Handles video/image file references
- [x] Maintains backward compatibility

**Estimated Time**: 5-6 hours

---

### Task 4: Create /fal-generate-video Skill ⭐ HIGH PRIORITY

**Objective**: Comprehensive video generation (text-to-video and image-to-video)

**File**: `skills/fal-generate-video/SKILL.md`

**Key Features**:
- Text-to-video (prompt → video)
- Image-to-video (image + prompt → animated video)
- Duration selection (5s, 10s) with cost warnings
- Aspect ratio presets (16:9, 9:16, 1:1, 4:3, 3:4)
- Quality modes (standard, pro)
- Async workflow with progress indication

**Implementation Summary**: Follow Phase 3 pattern with async enhancements:
- Validate API key
- Parse prompt + image (optional) + duration + aspect ratio
- Select model based on quality/cost preferences
- Call Python CLI: `python3 fal_api.py video --model X --prompt Y --duration 5`
- Show progress spinner during generation
- Extract video URL with Response Adapter
- Display result with metadata (duration, size, generation time)

**Async Workflow UX**:
```bash
/fal-generate-video "a wizard cat casting spells" --duration 10

⏳ Submitting video generation...
📋 Request ID: req_abc123xyz
⏳ Generating video (ETA: 60-120s)
⏳ Status: IN_QUEUE (5s elapsed)
⏳ Status: IN_PROGRESS (15s elapsed)
📝 Progress: Processing frame 1/10
📝 Progress: Processing frame 5/10
📝 Progress: Finalizing video
✅ Video generated in 87s

🎬 Video URL: https://fal.ai/files/abc123.mp4
   Model: Kling v1 Standard
   Duration: 10s
   Aspect Ratio: 16:9
   Size: 1280x720
```

**Success Criteria**:
- [x] Text-to-video works with various prompts
- [x] Image-to-video works with image + motion prompt
- [x] Duration selection works (5s, 10s)
- [x] Aspect ratio selection works (5 ratios)
- [x] Progress indication shows during generation
- [x] Clear cost warnings for expensive operations
- [x] Graceful timeout handling (>2 minutes)

**Estimated Time**: 6-8 hours

---

### Task 5: Create /fal-edit-photo Skill (Fibo Edit Suite) ⭐ HIGH PRIORITY

**Objective**: Advanced image editing with 10+ operations

**File**: `skills/fal-edit-photo/SKILL.md`

**Key Features**:
- Colorize (black & white → color)
- Relight (change lighting conditions)
- Reseason (change season in photo)
- Restore (repair old/damaged photos)
- Restyle (apply artistic styles)
- Inpaint (fill in missing parts)
- Outpaint (extend image borders)
- Add object (insert objects via text)
- Remove object (erase objects via text)
- Replace object (swap objects via text)

**Implementation Summary**:
- Parse operation type + image + prompt
- Validate image reference (URL or path)
- Operation-specific parameters:
  - Colorize: strength
  - Relight: lighting_prompt
  - Reseason: season (spring/summer/fall/winter)
  - Restyle: style_prompt
  - Inpaint/Add/Remove: prompt + mask
- Call Python CLI: `python3 fal_api.py edit --model X --operation Y --image-url Z --prompt P`
- Extract result image URL
- Display with operation metadata

**Success Criteria**:
- [x] At least 5 core operations work (colorize, relight, reseason, restore, restyle)
- [ ] Inpaint/outpaint work with proper masking
- [ ] Add/remove object work with text prompts
- [x] Strength parameter works for applicable operations
- [x] Clear examples for each operation type
- [x] Fast execution (<10s per operation)

**Estimated Time**: 5-7 hours

---

### Task 6: Create /fal-upscale Skill ⭐ HIGH PRIORITY

**Objective**: Image and video upscaling with quality enhancement

**File**: `skills/fal-upscale/SKILL.md`

**Key Features**:
- Image upscaling (2x, 4x, 8x)
- Video upscaling (2x, 4x)
- Quality enhancement (Crystal vs. Clarity)
- Creativity control (AI enhancement level)
- Async support for video upscaling

**Implementation Summary**:
- Parse input (image or video) + scale factor
- Validate scale (2, 4, or 8 for images; 2 or 4 for videos)
- Select model (Crystal for general, Clarity for photos)
- Call Python CLI: `python3 fal_api.py upscale --model X --image-url Y --scale 2`
- For video: Use async workflow with progress
- Extract result URL
- Display with before/after comparison info

**Async Workflow for Video**:
```bash
/fal-upscale video.mp4 --scale 2

⏳ Submitting video upscale (ETA: 30-60s)
📋 Request ID: req_upscale_xyz
⏳ Upscaling (15s elapsed)
⏳ Upscaling (30s elapsed)
✅ Video upscaled in 42s

🎬 Result: https://fal.ai/files/upscaled.mp4
   Scale: 2x
   Original: 1280x720
   Upscaled: 2560x1440
```

**Success Criteria**:
- [x] Image upscaling works (2x, 4x, 8x)
- [x] Video upscaling works (2x, 4x)
- [x] Quality enhancement is visible
- [x] Creativity parameter works
- [x] Async workflow for video is smooth
- [x] Clear comparison info (before/after resolution)

**Estimated Time**: 4-5 hours

---

### Task 7: Extend Orchestrator to Route Video/Editing Skills 🎯 HIGH PRIORITY

**Objective**: Update `/fal-generate` to route to new skills

**File**: `skills/fal-generate/SKILL.md`

**Implementation**:

```bash
# Add to routing logic (line 84+)
case "$SKILL" in
  # ... existing image/audio skills ...

  # NEW: Video skills
  fal-generate-video)
    exec "$SCRIPT_DIR/skills/fal-generate-video/SKILL.md" $ARGS
    ;;

  fal-edit-photo)
    exec "$SCRIPT_DIR/skills/fal-edit-photo/SKILL.md" $ARGS
    ;;

  fal-upscale)
    exec "$SCRIPT_DIR/skills/fal-upscale/SKILL.md" $ARGS
    ;;

  *)
    echo "❌ Unknown skill: $SKILL"
    exit 1
    ;;
esac
```

**Success Criteria**:
- [x] Routes video/editing/upscale intents correctly
- [x] Passes parameters through properly
- [x] Feedback shows detected skill and mode
- [x] No breaking changes to existing routing

**Estimated Time**: 1-2 hours

---

### Task 8: Add Video/Editing Intent Detection Tests 🧪 HIGH PRIORITY

**Objective**: Test video/editing intent detection

**File**: `tests/test_video_intent.py`

**Implementation**:

```python
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from detect_intent import (
    detect_intent,
    extract_duration_hint,
    extract_aspect_ratio,
    extract_video_reference,
    extract_scale_hint
)

class TestVideoIntentDetection(unittest.TestCase):

    def test_text_to_video_simple(self):
        """Test basic text-to-video intent"""
        result = detect_intent("create a video of a wizard cat")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("wizard cat", result["args"][0])

    def test_image_to_video(self):
        """Test image-to-video with image reference"""
        result = detect_intent("animate this image: cat.jpg")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("image-to-video", result["args"][2])

    def test_video_duration_extraction(self):
        """Test duration hint extraction"""
        result = detect_intent("make a 10 second video of fireworks")
        self.assertIn("--duration 10", result["args"][1])

    def test_aspect_ratio_detection(self):
        """Test aspect ratio detection"""
        result = detect_intent("create a vertical video for TikTok")
        self.assertIn("9:16", result["args"][2])

class TestEditingIntentDetection(unittest.TestCase):

    def test_colorize_detection(self):
        """Test colorize intent"""
        result = detect_intent("colorize this old photo: bw.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("colorize", result["args"][1])

    def test_relight_detection(self):
        """Test relight intent"""
        result = detect_intent("relight image.jpg with sunset lighting")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("relight", result["args"][1])

    def test_remove_object_detection(self):
        """Test remove object intent"""
        result = detect_intent("remove the person from photo.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("remove-object", result["args"][1])

class TestUpscaleIntentDetection(unittest.TestCase):

    def test_image_upscale_2x(self):
        """Test image upscale intent"""
        result = detect_intent("upscale image.jpg 2x")
        self.assertEqual(result["skill"], "fal-upscale")
        self.assertIn("--scale 2", result["args"][1])

    def test_video_upscale_4x(self):
        """Test video upscale intent"""
        result = detect_intent("enhance video.mp4 quality 4x")
        self.assertEqual(result["skill"], "fal-upscale")
        self.assertIn("--scale 4", result["args"][1])
        self.assertIn("video", result["args"][2])

class TestVideoHelpers(unittest.TestCase):

    def test_duration_extraction(self):
        """Test duration hint extraction"""
        self.assertEqual(extract_duration_hint("10 seconds"), 10)
        self.assertEqual(extract_duration_hint("5 second video"), 5)
        self.assertEqual(extract_duration_hint("no duration"), 5)

    def test_aspect_ratio_extraction(self):
        """Test aspect ratio extraction"""
        self.assertEqual(extract_aspect_ratio("vertical video"), "9:16")
        self.assertEqual(extract_aspect_ratio("widescreen"), "16:9")
        self.assertEqual(extract_aspect_ratio("square"), "1:1")

    def test_scale_extraction(self):
        """Test scale hint extraction"""
        self.assertEqual(extract_scale_hint("upscale 2x"), 2)
        self.assertEqual(extract_scale_hint("4x enhancement"), 4)
        self.assertEqual(extract_scale_hint("8x quality"), 8)

    def test_video_reference_extraction(self):
        """Test video URL/path extraction"""
        self.assertEqual(
            extract_video_reference("upscale https://example.com/video.mp4"),
            "https://example.com/video.mp4"
        )
        self.assertEqual(
            extract_video_reference("enhance ~/video.mov"),
            "~/video.mov"
        )

if __name__ == '__main__':
    unittest.main()
```

**Success Criteria**:
- [x] All video intent tests pass
- [x] All editing intent tests pass
- [x] All upscale intent tests pass
- [x] Helper function tests pass
- [x] Fast execution (<100ms)

**Estimated Time**: 3-4 hours

---

### Task 9: Extend Curated Model Registry 📋 SUPPORTING

**Objective**: Add video/editing/upscale models to `models/curated.yaml`

**File**: `models/curated.yaml`

**Implementation**:

```yaml
  text-to-video:
    - endpoint_id: fal-ai/kling-video/v1/standard/text-to-video
      display_name: Kling v1 Standard (Text-to-Video)
      description: "Budget-friendly text-to-video, 5-10s"
      cost_tier: standard
      speed_tier: slow  # 30-60s
      quality_tier: high
      recommended: true
      tested: false
      params:
        prompt: "string (required)"
        duration: "int (optional, default: 5, choices: [5, 10])"
        aspect_ratio: "string (optional, default: '16:9')"
        negative_prompt: "string (optional)"

    - endpoint_id: fal-ai/kling-video/v1/pro/text-to-video
      display_name: Kling v1 Pro (Text-to-Video)
      description: "High-quality text-to-video, 5-10s"
      cost_tier: premium
      speed_tier: slow  # 60-120s
      quality_tier: highest
      recommended: false
      tested: false
      params:
        prompt: "string (required)"
        duration: "int (optional, default: 5, choices: [5, 10])"
        aspect_ratio: "string (optional, default: '16:9')"
        negative_prompt: "string (optional)"

  image-to-video:
    - endpoint_id: fal-ai/kling-video/v1/standard/image-to-video
      display_name: Kling v1 Standard (Image-to-Video)
      description: "Animate images, 5-10s"
      cost_tier: standard
      speed_tier: slow  # 45-90s
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (required)"
        prompt: "string (optional)"
        duration: "int (optional, default: 5)"
        negative_prompt: "string (optional)"

  image-editing:
    - endpoint_id: fal-ai/fibo-edit/colorize
      display_name: Fibo Edit - Colorize
      description: "Add color to black & white photos"
      cost_tier: budget
      speed_tier: fast  # <10s
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (required)"
        strength: "float (optional, default: 0.8)"

    - endpoint_id: fal-ai/fibo-edit/relight
      display_name: Fibo Edit - Relight
      description: "Change lighting conditions"
      cost_tier: budget
      speed_tier: fast
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (required)"
        lighting_prompt: "string (optional)"
        strength: "float (optional, default: 0.8)"

    - endpoint_id: fal-ai/fibo-edit/reseason
      display_name: Fibo Edit - Reseason
      description: "Change season in photos"
      cost_tier: budget
      speed_tier: fast
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (required)"
        season: "string (optional, choices: [spring, summer, fall, winter])"

    - endpoint_id: fal-ai/fibo-edit/restore
      display_name: Fibo Edit - Restore
      description: "Repair old/damaged photos"
      cost_tier: budget
      speed_tier: fast
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (required)"

    - endpoint_id: fal-ai/fibo-edit/restyle
      display_name: Fibo Edit - Restyle
      description: "Apply artistic styles"
      cost_tier: budget
      speed_tier: fast
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (required)"
        style_prompt: "string (optional)"
        strength: "float (optional, default: 0.8)"

  upscale:
    - endpoint_id: fal-ai/crystal-upscaler
      display_name: Crystal Upscaler
      description: "General-purpose upscaling (2x, 4x, 8x)"
      cost_tier: standard
      speed_tier: medium  # 10-30s for images, 30-60s for video
      quality_tier: high
      recommended: true
      tested: false
      params:
        image_url: "string (optional)"
        video_url: "string (optional)"
        scale: "int (required, choices: [2, 4, 8])"
        creativity: "float (optional, default: 0.35)"

    - endpoint_id: fal-ai/clarity-upscaler
      display_name: Clarity Upscaler
      description: "Photo-optimized upscaling (2x, 4x)"
      cost_tier: premium
      speed_tier: medium
      quality_tier: highest
      recommended: false
      tested: false
      params:
        image_url: "string (required)"
        scale: "int (required, choices: [2, 4])"
```

**Success Criteria**:
- [x] All 3 categories added with recommended models
- [x] Cost tiers accurate
- [x] Speed tiers reflect actual generation times
- [x] Parameters documented correctly

**Estimated Time**: 2-3 hours

---

## Testing Plan

### Manual Testing

**Test 1: Text-to-Video (Standard)**
```bash
/fal-generate-video "a wizard cat casting magical spells" --duration 5 --aspect-ratio 16:9

Expected:
- ⏳ Async workflow starts
- 📋 Request ID shown
- ⏳ Progress updates every 5-10s
- ✅ Video generated in 30-60s
- 🎬 Valid MP4 URL returned
```

**Test 2: Image-to-Video**
```bash
/fal-generate-video --image cat.jpg --prompt "walking forward" --duration 5

Expected:
- Image uploaded (if local)
- Video shows cat walking
- 5 second duration
- Natural motion
```

**Test 3: Fibo Edit - Colorize**
```bash
/fal-edit-photo bw_photo.jpg --operation colorize

Expected:
- Fast execution (<10s)
- Natural colorization
- Preserves details
```

**Test 4: Fibo Edit - Relight**
```bash
/fal-edit-photo photo.jpg --operation relight --lighting-prompt "sunset golden hour"

Expected:
- Lighting changed to sunset
- Natural-looking result
- Colors adjusted appropriately
```

**Test 5: Image Upscale 4x**
```bash
/fal-upscale image.jpg --scale 4

Expected:
- Execution in 10-20s
- 4x resolution increase
- Quality improvement visible
```

**Test 6: Video Upscale 2x (Async)**
```bash
/fal-upscale video.mp4 --scale 2

Expected:
- Async workflow starts
- Progress updates
- Completion in 30-60s
- 2x resolution increase
```

**Test 7: Orchestrator Routing - Video**
```bash
/fal-generate "create a 10 second video of fireworks"

Expected:
- 🎯 Detected: fal-generate-video
- Routes to video skill
- Duration=10 detected
```

**Test 8: Orchestrator Routing - Editing**
```bash
/fal-generate "colorize this old photo" [upload]

Expected:
- 🎯 Detected: fal-edit-photo
- Routes to editing skill
- Operation=colorize detected
```

### Automated Testing

```bash
# Run all tests
uv run pytest tests/

# Run video intent tests only
uv run pytest tests/test_video_intent.py -v

# Expected: All tests pass
```

---

## Deliverables Checklist

### Critical (Must-Have)
- [x] `/fal-generate-video` skill (`skills/fal-generate-video/SKILL.md`)
- [x] `/fal-edit-photo` skill (`skills/fal-edit-photo/SKILL.md`)
- [x] `/fal-upscale` skill (`skills/fal-upscale/SKILL.md`)
- [x] Python CLI commands in `scripts/fal_api.py` (video, edit, upscale)
- [x] Intent detection extension in `scripts/detect_intent.py`
- [x] Tests for video/editing intent detection (`tests/test_video_intent.py`)
- [x] Async workflow implementation with progress indication

### Important (Should-Have)
- [x] Response Adapter video/editing patterns (`scripts/lib/adapter.py`)
- [x] Curated model registry updates (`models/curated.yaml`)
- [x] Orchestrator routing updates (`skills/fal-generate/SKILL.md`)
- [x] Error handling for async timeouts
- [x] Cost warnings for expensive operations
- [x] Skill documentation with examples

### Nice-to-Have
- [ ] Batch editing support
- [ ] Video concatenation
- [ ] Frame extraction
- [ ] Before/after comparison UI
- [ ] Cost estimation before submission

---

## Success Criteria Summary

**Phase 4-5 is complete when:**
- ✅ All three skills work end-to-end
- ✅ Async workflow provides good UX for long operations
- ✅ Video generation works for both text and image inputs
- ✅ At least 5 Fibo Edit operations work correctly
- ✅ Upscaling works for images and videos
- ✅ Response Adapter successfully extracts video/image URLs
- ✅ Intent detection routes correctly
- ✅ Test coverage for video/editing intents
- ✅ Clear progress indication for operations >30s
- ✅ Documentation with examples

**Ready for Production When:**
- All async workflows tested and stable
- Timeout handling works correctly
- Error messages clear and actionable
- Cost warnings displayed appropriately
- Performance acceptable (video <120s, editing <10s, upscale <60s)

---

## Key Design Decisions

### 1. When to Use Async vs. Blocking

**Async (submit_async + polling):**
- Video generation (30-120s)
- Video upscaling (30-60s)
- Long video-to-video operations (60-180s)

**Blocking (run_model):**
- Image editing (<10s)
- Image upscaling (<20s)
- Image generation (<30s)
- Audio generation (<10s)

**Threshold**: Use async for operations expected to take >30 seconds

### 2. Progress Indication Strategy

```python
# Show initial status
logger.info(f"⏳ Submitting video generation (ETA: 60-120s)")
logger.info(f"📋 Request ID: {request_id}")

# Poll with visual feedback
while not complete:
    elapsed = time.time() - start_time
    logger.info(f"⏳ Status: {status} ({elapsed}s elapsed)")

    # Show any progress logs from API
    for log in status.get("logs", []):
        logger.info(f"📝 {log['message']}")

    time.sleep(5)  # Poll every 5 seconds

# Show completion
logger.info(f"✅ Video generated in {elapsed}s")
```

### 3. Error Handling for Async Operations

```python
# Timeout after 3 minutes (180s)
MAX_WAIT_TIME = 180

start_time = time.time()
while time.time() - start_time < MAX_WAIT_TIME:
    status = client.check_status(endpoint, request_id)

    if status["status"] == "COMPLETED":
        break
    elif status["status"] == "FAILED":
        error = status.get("error", "Unknown error")
        raise Exception(f"Generation failed: {error}")

    time.sleep(5)

if time.time() - start_time >= MAX_WAIT_TIME:
    raise TimeoutError(f"Generation timed out after {MAX_WAIT_TIME}s")
```

### 4. Cost Warnings

Display clear warnings before expensive operations:

```bash
⚠️  Pro mode costs 3x more than Standard
   Standard: $0.05 per 5s video
   Pro: $0.15 per 5s video

   Continue with Pro? (y/n)
```

---

## Risk Management

### High Priority Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Video generation timeout** | High | 3-minute timeout, clear error messages, retry option |
| **Async workflow UX confusing** | High | Clear progress indication, request ID display, ETA estimates |
| **Fibo Edit quality varies** | Medium | Document expected results, multiple examples, strength parameter |
| **Video file size large** | Medium | Display file size warnings, offer compression options |

### Medium Priority Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Cost overruns from video** | High | Clear cost warnings, default to 5s/standard, confirmation for pro |
| **Response format variation** | Low | Response Adapter handles it, add patterns as needed |
| **Upscale quality expectations** | Medium | Show before/after info, set realistic expectations |

---

## Branch Strategy

**Branch**: `feat/phase-4-5-video-editing`

**Workflow**:
```bash
# Create new branch from main
git checkout main
git pull origin main
git checkout -b feat/phase-4-5-video-editing

# Implement incrementally
git add scripts/fal_api.py scripts/detect_intent.py
git commit -m "feat(cli): add video/edit/upscale commands and intent detection"

git add skills/fal-generate-video/
git commit -m "feat(skill): add /fal-generate-video with async workflow"

git add skills/fal-edit-photo/
git commit -m "feat(skill): add /fal-edit-photo (Fibo Edit suite)"

git add skills/fal-upscale/
git commit -m "feat(skill): add /fal-upscale for images and videos"

git add tests/test_video_intent.py
git commit -m "test: add video/editing intent detection tests"

# When complete, merge to main
git checkout main
git merge feat/phase-4-5-video-editing
```

---

## References

### Internal References
- Phase 3 Plan: `docs/plans/2026-01-28-feat-phase-3-audio-avatars-plan.md`
- Queue Migration: `docs/QUEUE_MIGRATION.md`
- Roadmap: `docs/plans/2026-01-28-fal-skill-roadmap.md`
- API Client: `scripts/lib/api_client.py`
- Response Adapter: `scripts/lib/adapter.py`
- Intent Detection: `scripts/detect_intent.py`

### External References
- fal.ai API Documentation: https://docs.fal.ai/
- Kling Video: https://fal.ai/models/fal-ai/kling-video/v1/standard/text-to-video/api
- Fibo Edit Suite: https://fal.ai/models/fal-ai/fibo-edit/colorize/api
- Crystal Upscaler: https://fal.ai/models/fal-ai/crystal-upscaler/api
- Async Workflows: https://docs.fal.ai/tutorials/using-the-queue

---

## Appendix: Async Methods Usage Examples

### Basic Async Pattern

```python
from scripts.lib.api_client import FalAPIClient

client = FalAPIClient()

# Submit job
request_id = client.submit_async(
    "fal-ai/kling-video/v1/standard/text-to-video",
    {
        "prompt": "a wizard cat",
        "duration": 10
    }
)

print(f"Request ID: {request_id}")

# Check status periodically
import time
while True:
    status = client.check_status(
        "fal-ai/kling-video/v1/standard/text-to-video",
        request_id
    )

    print(f"Status: {status['status']}")

    if status["status"] == "COMPLETED":
        break

    time.sleep(5)

# Get final result
result = client.get_result(
    "fal-ai/kling-video/v1/standard/text-to-video",
    request_id
)

print(f"Video URL: {result['video']['url']}")
```

### Batch Async Operations

```python
# Submit multiple videos at once
request_ids = []
for prompt in ["wizard cat", "dragon flying", "ocean waves"]:
    request_id = client.submit_async(
        "fal-ai/kling-video/v1/standard/text-to-video",
        {"prompt": prompt, "duration": 5}
    )
    request_ids.append((prompt, request_id))

# Wait for all to complete
results = []
for prompt, request_id in request_ids:
    # Poll until complete
    while True:
        status = client.check_status(endpoint, request_id)
        if status["status"] == "COMPLETED":
            break
        time.sleep(5)

    result = client.get_result(endpoint, request_id)
    results.append((prompt, result))

# Process all results
for prompt, result in results:
    print(f"{prompt}: {result['video']['url']}")
```

---

**Status**: ✅ Ready for implementation
**Next Step**: Begin Task 1 - Extend Python CLI for video/edit/upscale commands
**Estimated Completion**: 2026-02-01 or 2026-02-02 (3-4 days from 2026-01-29)
**Dependencies**: Phase 3 complete, queue migration done, async methods available
