---
title: Phase 2 - Core Generation Skills
type: feat
date: 2026-01-28
parent_plan: 2026-01-28-fal-skill-roadmap.md
status: ready
branch: feat/phase-2-generation-skills
---

# Phase 2: Core Generation Skills

**Goal**: Implement three Claude Code skills that leverage the Response Adapter for reliable result extraction

**Duration**: 2-3 days focused work (12-18 hours)

**Context**: Phase 1 foundation is complete (8.5/10 production readiness). Response Adapter enables reliable extraction from variable response formats. Now ready to build user-facing generation skills.

---

## Problem Statement

Users need simple, reliable ways to generate images and remove backgrounds without dealing with:
1. **API complexity**: Different models have different parameter formats
2. **Response variability**: Each model returns results in different JSON structures
3. **Model selection**: Choosing the right model for the task
4. **Prompt engineering**: Knowing what parameters work best

**Current Status**: Infrastructure ready, no generation skills exist
**Target Status**: Three working skills covering common generation tasks

---

## Success Metrics

### Must-Have (Core Functionality)
- [x] `/fal-generate-image` skill works with natural language prompts
- [x] `/fal-remove-bg` skill works with uploaded images
- [x] `/fal-generate` orchestrator routes to correct skill
- [x] All skills use Response Adapter for result extraction
- [x] Test coverage for skill logic

### Should-Have (User Experience)
- [x] Clear error messages for common failures
- [x] Progress indication for long operations
- [x] Result preview with metadata (dimensions, cost estimate)
- [x] Support for optional parameters (size, quality)

### Nice-to-Have (Polish)
- [ ] `/fal-generate` understands context ("make it bigger", "remove background")
- [ ] Skill-specific help and examples
- [ ] Cost tracking and budgeting
- [ ] Multiple output format support

---

## Technical Approach

### Architecture

```
User → Claude Code → Skill (SKILL.md)
                        ↓
                    Parse Intent
                        ↓
                    Python CLI
                        ↓
               ┌────────┴────────┐
               ↓                 ↓
          ModelRegistry    FalAPIClient
               ↓                 ↓
          Select Model    Execute Request
               ↓                 ↓
          Build Params    Get Response
               ↓                 ↓
               └────────┬────────┘
                        ↓
                ResponseAdapter
                        ↓
                  Extract URL
                        ↓
              Return to User
```

### Skill Structure

Each skill follows this pattern:

```
skills/
├── fal-generate-image/
│   └── SKILL.md
├── fal-remove-bg/
│   └── SKILL.md
└── fal-generate/
    └── SKILL.md
```

---

## Implementation Plan

### Task 1: Create /fal-generate-image Skill ⭐ HIGH PRIORITY ✅

**Objective**: Enable text-to-image generation with natural language

**File**: `skills/fal-generate-image/SKILL.md`

**Implementation**:

````markdown
# /fal-generate-image

Generate images from text descriptions using fal.ai models.

## Usage

```
/fal-generate-image "a wizard cat wearing purple robes"
/fal-generate-image "mountain landscape at sunset" --size landscape_16_9
/fal-generate-image "abstract art" --quality high
```

## What it does

1. Validates API key is configured
2. Parses prompt and optional parameters
3. Selects best text-to-image model (FLUX.1 [dev] by default)
4. Generates image via fal.ai API
5. Extracts result URL using Response Adapter
6. Displays image with metadata

## Instructions

### Step 1: Validate API Key

Check if user has run setup:

```bash
if [ ! -f ~/.config/fal-skill/.env ]; then
  echo "❌ API key not configured. Please run /fal-setup first."
  exit 1
fi
```

### Step 2: Parse User Input

Extract prompt and optional parameters from user message:

```bash
# Required: prompt (everything after command)
PROMPT="$1"

# Optional: --size (square_hd, square, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9)
SIZE="${2:-square_hd}"

# Optional: --quality (fast, balanced, high)
# Maps to: dev (fast), dev+steps (balanced), pro (high)
QUALITY="${3:-balanced}"

if [ -z "$PROMPT" ]; then
  echo "❌ Prompt required. Usage: /fal-generate-image \"your prompt here\""
  exit 1
fi
```

### Step 3: Select Model Based on Quality

```bash
case "$QUALITY" in
  fast)
    MODEL="fal-ai/flux/dev"
    STEPS=20
    ;;
  balanced)
    MODEL="fal-ai/flux/dev"
    STEPS=28
    ;;
  high)
    MODEL="fal-ai/flux-pro"
    STEPS=28
    ;;
  *)
    echo "❌ Invalid quality: $QUALITY. Use: fast, balanced, high"
    exit 1
    ;;
esac
```

### Step 4: Build Input Parameters

```bash
# Create JSON input
INPUT_JSON=$(cat <<EOF
{
  "prompt": "$PROMPT",
  "image_size": "$SIZE",
  "num_inference_steps": $STEPS,
  "guidance_scale": 3.5,
  "num_images": 1
}
EOF
)
```

### Step 5: Call Python API Client

```bash
echo "⏳ Generating image with $MODEL..."

# Execute model via Python CLI
RESULT=$(python3 scripts/fal_api.py run "$MODEL" "$INPUT_JSON" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Generation failed:"
  echo "$RESULT"
  exit 1
fi
```

### Step 6: Extract Result Using Response Adapter

```python
# This happens inside fal_api.py
from scripts.lib.adapter import ResponseAdapter

adapter = ResponseAdapter()
response_json = json.loads(api_response)
image_url = adapter.extract_result(response_json, model_endpoint)

if not image_url:
    raise Exception("Could not extract image URL from response")

# Return JSON with result
print(json.dumps({
    "url": image_url,
    "model": model_endpoint,
    "prompt": input_data["prompt"]
}))
```

### Step 7: Display Result

```bash
# Parse response
IMAGE_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])")

echo "✅ Image generated!"
echo ""
echo "🖼️  Result: $IMAGE_URL"
echo "📝 Prompt: $PROMPT"
echo "🎨 Model: $MODEL"
echo "📐 Size: $SIZE"
echo ""
echo "💡 Tip: Right-click the URL to download or open in browser"
```

## Error Handling

### API Key Not Found
```
❌ API key not configured. Please run /fal-setup first.
```

### Invalid Prompt
```
❌ Prompt required. Usage: /fal-generate-image "your prompt here"
```

### Generation Failed
```
❌ Generation failed: [error details]
Possible causes:
- Invalid prompt (check for banned content)
- API rate limit exceeded
- Model temporarily unavailable

Try: /fal-generate-image "simpler prompt" --quality fast
```

### Network Timeout
```
❌ Request timed out after 30s
Try:
1. Check internet connection
2. Use faster model: --quality fast
3. Try again (may be temporary)
```

## Examples

```bash
# Basic usage
/fal-generate-image "a serene mountain landscape"

# Specific size
/fal-generate-image "portrait of a warrior" --size portrait_16_9

# High quality (slower, premium)
/fal-generate-image "detailed fantasy castle" --quality high

# Fast generation (lower quality)
/fal-generate-image "quick sketch of a car" --quality fast
```

## Related Skills

- `/fal-remove-bg` - Remove image backgrounds
- `/fal-generate` - Universal generator (detects intent)
- `/fal-setup` - Configure API key
````

**Success Criteria**:
- [ ] Skill accepts natural language prompts
- [ ] Supports size and quality parameters
- [ ] Uses Response Adapter for extraction
- [ ] Clear error messages for failures
- [ ] Works with all image sizes

**Estimated Time**: 4-6 hours

---

### Task 2: Create /fal-remove-bg Skill ⭐ HIGH PRIORITY ✅

**Objective**: Remove backgrounds from uploaded images

**File**: `skills/fal-remove-bg/SKILL.md`

**Implementation**:

````markdown
# /fal-remove-bg

Remove backgrounds from images using AI.

## Usage

```
/fal-remove-bg [upload image file]
/fal-remove-bg https://example.com/image.jpg
/fal-remove-bg path/to/image.png
```

## What it does

1. Validates image input (file, URL, or path)
2. Uploads image if needed (to temp storage)
3. Calls birefnet/v2 model
4. Extracts transparent PNG result
5. Downloads and saves result locally

## Instructions

### Step 1: Validate Input

```bash
# Check if user provided an image
INPUT="$1"

if [ -z "$INPUT" ]; then
  echo "❌ Image required. Usage: /fal-remove-bg <image-url-or-path>"
  echo ""
  echo "Examples:"
  echo "  /fal-remove-bg https://example.com/photo.jpg"
  echo "  /fal-remove-bg ~/Downloads/photo.png"
  echo "  /fal-remove-bg [upload file via Claude Code]"
  exit 1
fi
```

### Step 2: Determine Input Type

```bash
# Check if input is a URL
if [[ "$INPUT" =~ ^https?:// ]]; then
  IMAGE_URL="$INPUT"
  echo "📥 Using provided URL"

# Check if input is a local file path
elif [ -f "$INPUT" ]; then
  # Upload to temporary storage (use fal.ai storage or imgbb)
  echo "⏳ Uploading image..."
  IMAGE_URL=$(python3 scripts/upload_image.py "$INPUT")

  if [ -z "$IMAGE_URL" ]; then
    echo "❌ Failed to upload image"
    exit 1
  fi

  echo "✅ Uploaded to: $IMAGE_URL"

else
  echo "❌ Invalid input: $INPUT"
  echo "Must be a URL or valid file path"
  exit 1
fi
```

### Step 3: Call Background Removal API

```bash
MODEL="fal-ai/birefnet/v2"

INPUT_JSON=$(cat <<EOF
{
  "image_url": "$IMAGE_URL"
}
EOF
)

echo "⏳ Removing background with birefnet..."

RESULT=$(python3 scripts/fal_api.py run "$MODEL" "$INPUT_JSON" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Background removal failed:"
  echo "$RESULT"
  exit 1
fi
```

### Step 4: Extract Result

```bash
# Parse response (Response Adapter handles this inside fal_api.py)
RESULT_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])")

echo "✅ Background removed!"
echo ""
echo "🖼️  Result: $RESULT_URL"
echo "📥 Original: $IMAGE_URL"
```

### Step 5: Optional - Download Result

```bash
# Ask user if they want to download
echo ""
echo "💾 Download result? (y/n)"
read -r DOWNLOAD

if [ "$DOWNLOAD" = "y" ]; then
  OUTPUT_FILE="./background_removed_$(date +%s).png"
  curl -s -o "$OUTPUT_FILE" "$RESULT_URL"
  echo "✅ Saved to: $OUTPUT_FILE"
fi
```

## Error Handling

### No Image Provided
```
❌ Image required. Usage: /fal-remove-bg <image-url-or-path>
```

### Invalid URL
```
❌ Invalid URL: [url]
Must be a valid http:// or https:// URL
```

### File Not Found
```
❌ File not found: [path]
Check the path and try again
```

### Upload Failed
```
❌ Failed to upload image
Possible causes:
- File too large (>10MB)
- Invalid image format (use PNG, JPG, WEBP)
- Network issue

Try: Compress image or use a URL instead
```

### API Error
```
❌ Background removal failed: [error]
Possible causes:
- Invalid image format
- Image too large
- API rate limit

Try: Use a smaller image or wait a moment
```

## Examples

```bash
# Remove background from URL
/fal-remove-bg https://example.com/photo.jpg

# Remove background from local file
/fal-remove-bg ~/Pictures/photo.png

# Remove background from uploaded file
/fal-remove-bg [drag and drop image]
```

## Technical Notes

**Supported Formats**:
- Input: PNG, JPG, JPEG, WEBP
- Output: PNG with transparency

**Size Limits**:
- Max input: 10MB
- Max dimensions: 4096x4096

**Model**: fal-ai/birefnet/v2
- Fast processing (1-3 seconds)
- High-quality edge detection
- Works on photos, illustrations, logos

## Related Skills

- `/fal-generate-image` - Generate new images
- `/fal-generate` - Universal generator
````

**Success Criteria**:
- [ ] Accepts URLs and file paths
- [ ] Handles file uploads gracefully
- [ ] Uses birefnet/v2 model
- [ ] Extracts transparent PNG result
- [ ] Option to download result locally

**Estimated Time**: 3-4 hours

---

### Task 3: Create /fal-generate Orchestrator ⭐ MEDIUM PRIORITY ✅

**Objective**: Universal generator that routes to specialized skills

**File**: `skills/fal-generate/SKILL.md`

**Implementation**:

````markdown
# /fal-generate

Universal generation orchestrator - detects intent and routes to specialized skills.

## Usage

```
/fal-generate "a wizard cat"
/fal-generate "remove background from image.jpg"
/fal-generate "make a video of..."
```

## What it does

1. Analyzes user request to detect intent
2. Routes to appropriate specialized skill
3. Passes through parameters
4. Handles multi-step workflows

## Instructions

### Step 1: Parse User Intent

```bash
USER_REQUEST="$*"

if [ -z "$USER_REQUEST" ]; then
  echo "❌ Request required. Usage: /fal-generate <what you want>"
  echo ""
  echo "Examples:"
  echo "  /fal-generate \"a fantasy castle\""
  echo "  /fal-generate \"remove background from photo.jpg\""
  exit 1
fi
```

### Step 2: Detect Intent Type

```python
# Intent detection script (scripts/detect_intent.py)
import re
import sys

def detect_intent(text: str) -> dict:
    """Detect generation intent from natural language"""

    text_lower = text.lower()

    # Background removal keywords
    bg_keywords = ["remove background", "transparent", "remove bg", "cut out"]
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
    """Extract image URL or path from text"""
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
    """Remove size and quality hints from prompt"""
    # Remove size hints
    text = re.sub(r'\b(portrait|landscape|square)\b', '', text, flags=re.I)
    # Remove quality hints
    text = re.sub(r'\b(fast|quick|high quality|detailed)\b', '', text, flags=re.I)
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

if __name__ == "__main__":
    import json
    request = " ".join(sys.argv[1:])
    intent = detect_intent(request)
    print(json.dumps(intent))
```

### Step 3: Route to Specialized Skill

```bash
# Detect intent
INTENT=$(python3 scripts/detect_intent.py "$USER_REQUEST")
SKILL=$(echo "$INTENT" | python3 -c "import sys, json; print(json.load(sys.stdin)['skill'])")
ARGS=$(echo "$INTENT" | python3 -c "import sys, json; print(' '.join(json.load(sys.stdin)['args']))")

echo "🎯 Detected: $SKILL"
echo "📝 Request: $USER_REQUEST"
echo ""

# Route to appropriate skill
case "$SKILL" in
  fal-generate-image)
    /fal-generate-image $ARGS
    ;;
  fal-remove-bg)
    /fal-remove-bg $ARGS
    ;;
  *)
    echo "❌ Unknown skill: $SKILL"
    exit 1
    ;;
esac
```

## Intent Detection Examples

**Text-to-Image** (default):
- "a wizard cat" → `/fal-generate-image "a wizard cat"`
- "portrait of a warrior" → `/fal-generate-image "portrait of a warrior" --size portrait_16_9`
- "quick sketch of a car" → `/fal-generate-image "sketch of a car" --quality fast`

**Background Removal**:
- "remove background from photo.jpg" → `/fal-remove-bg photo.jpg`
- "make transparent: image.png" → `/fal-remove-bg image.png`
- "cut out https://example.com/photo.jpg" → `/fal-remove-bg https://example.com/photo.jpg`

## Error Handling

### Empty Request
```
❌ Request required. Usage: /fal-generate <what you want>
```

### Intent Detection Failed
```
❌ Could not understand request: [request]

Try being more specific:
- For images: "a wizard cat wearing purple robes"
- For background removal: "remove background from image.jpg"
```

### Skill Execution Failed
```
❌ [Skill] failed: [error]

[Error details from specialized skill]
```

## Examples

```bash
# Simple image generation
/fal-generate "a serene mountain landscape"

# Image with hints
/fal-generate "portrait of a warrior in high quality"

# Background removal
/fal-generate "remove background from photo.jpg"

# Quick generation
/fal-generate "fast sketch of a spaceship"
```

## Future Enhancements

**Phase 3 - Conversational Context**:
- "make it bigger" → understands "it" refers to last result
- "remove the background" → implies from last generated image
- "try again with more detail" → re-runs with modified parameters

**Phase 4 - Multi-Step Workflows**:
- "generate a cat and remove its background" → chain operations
- Session-based memory for complex tasks

## Related Skills

- `/fal-generate-image` - Direct image generation
- `/fal-remove-bg` - Direct background removal
````

**Success Criteria**:
- [ ] Detects text-to-image intent
- [ ] Detects background removal intent
- [ ] Routes to correct specialized skill
- [ ] Preserves parameters through routing
- [ ] Clear feedback on detected intent

**Estimated Time**: 3-4 hours

---

### Task 4: Add Python CLI Commands 🔧 SUPPORTING ✅

**Objective**: Extend fal_api.py to support skills workflow

**File**: `scripts/fal_api.py`

**New Commands**:

```python
# Add to fal_api.py command handler

def handle_generate(args):
    """Generate image from prompt"""
    endpoint_id = args.model  # e.g., fal-ai/flux/dev

    # Build input from args
    input_data = {
        "prompt": args.prompt,
        "image_size": args.size,
        "num_inference_steps": args.steps,
        "guidance_scale": args.guidance
    }

    # Remove None values
    input_data = {k: v for k, v in input_data.items() if v is not None}

    # Execute via API client
    client = FalAPIClient()
    result = client.run_model(endpoint_id, input_data)

    # Extract URL with adapter
    adapter = ResponseAdapter()
    url = adapter.extract_result(result, endpoint_id)

    if not url:
        print(json.dumps({"error": "Could not extract URL from response"}))
        sys.exit(1)

    # Return structured result
    output = {
        "url": url,
        "model": endpoint_id,
        "prompt": input_data.get("prompt")
    }

    print(json.dumps(output))

# Add argparse subcommand
generate_parser = subparsers.add_parser('generate', help='Generate image')
generate_parser.add_argument('--model', required=True)
generate_parser.add_argument('--prompt', required=True)
generate_parser.add_argument('--size', default='square_hd')
generate_parser.add_argument('--steps', type=int)
generate_parser.add_argument('--guidance', type=float)
generate_parser.set_defaults(func=handle_generate)
```

**Success Criteria**:
- [ ] `python3 scripts/fal_api.py generate --model X --prompt Y` works
- [ ] Returns JSON with URL, model, prompt
- [ ] Uses Response Adapter for extraction
- [ ] Clear error messages

**Estimated Time**: 2-3 hours

---

### Task 5: Add Helper Scripts 🔧 SUPPORTING ✅

**Objective**: Support scripts for skills

**Files**:
- `scripts/detect_intent.py` - Intent detection
- `scripts/upload_image.py` - Image upload helper

**detect_intent.py**:
```python
"""Intent detection for /fal-generate orchestrator"""
import re
import sys
import json

def detect_intent(text: str) -> dict:
    # (Implementation from Task 3)
    pass

if __name__ == "__main__":
    request = " ".join(sys.argv[1:])
    intent = detect_intent(request)
    print(json.dumps(intent))
```

**upload_image.py**:
```python
"""Upload image to temporary storage for API use"""
import sys
import os
import requests

def upload_image(file_path: str) -> str:
    """Upload image and return URL"""

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file size
    size = os.path.getsize(file_path)
    if size > 10 * 1024 * 1024:  # 10MB
        raise ValueError("File too large (>10MB)")

    # TODO: Use fal.ai storage or imgbb API
    # For now, return error
    raise NotImplementedError("Image upload not yet implemented")

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
```

**Success Criteria**:
- [ ] detect_intent.py correctly identifies intents
- [ ] upload_image.py validates files
- [ ] Both scripts return JSON/text to stdout
- [ ] Errors go to stderr with exit code 1

**Estimated Time**: 2 hours

---

### Task 6: Add Tests for Skills Logic 🧪 HIGH PRIORITY ✅

**Objective**: Test skill logic without mocking full skills

**Files**:
- `tests/test_intent_detection.py`
- `tests/test_skill_helpers.py`

**test_intent_detection.py**:
```python
import unittest
from scripts.detect_intent import detect_intent

class TestIntentDetection(unittest.TestCase):

    def test_text_to_image_simple(self):
        """Test basic text-to-image intent"""
        result = detect_intent("a wizard cat")
        self.assertEqual(result["skill"], "fal-generate-image")
        self.assertIn("a wizard cat", result["args"][0])

    def test_text_to_image_with_size(self):
        """Test text-to-image with size hint"""
        result = detect_intent("portrait of a warrior")
        self.assertEqual(result["skill"], "fal-generate-image")
        self.assertIn("portrait", result["args"][1])

    def test_background_removal_with_url(self):
        """Test background removal with URL"""
        result = detect_intent("remove background from https://example.com/photo.jpg")
        self.assertEqual(result["skill"], "fal-remove-bg")
        self.assertIn("https://example.com/photo.jpg", result["args"])

    def test_background_removal_with_path(self):
        """Test background removal with file path"""
        result = detect_intent("remove background from ~/photo.png")
        self.assertEqual(result["skill"], "fal-remove-bg")
        self.assertIn("~/photo.png", result["args"])

    def test_quality_hint_fast(self):
        """Test quality hint detection"""
        result = detect_intent("quick sketch of a car")
        self.assertIn("fast", result["args"][2])

    def test_quality_hint_high(self):
        """Test high quality detection"""
        result = detect_intent("detailed painting of a landscape")
        self.assertIn("high", result["args"][2])

if __name__ == '__main__':
    unittest.main()
```

**Success Criteria**:
- [ ] All intent detection tests pass
- [ ] Tests cover text-to-image and background removal
- [ ] Tests cover size and quality hints
- [ ] Fast test execution (<100ms)

**Estimated Time**: 2 hours

---

## Testing Plan

### Manual Testing

**Test 1: Basic Image Generation**
```bash
/fal-generate-image "a wizard cat wearing purple robes"
Expected:
- ⏳ Generating message
- ✅ Success with URL
- Image displays in Claude Code
```

**Test 2: Background Removal from URL**
```bash
/fal-remove-bg "https://example.com/photo.jpg"
Expected:
- 📥 Using provided URL
- ⏳ Removing background
- ✅ Result URL with transparent PNG
```

**Test 3: Orchestrator Routing**
```bash
/fal-generate "a mountain landscape"
Expected:
- 🎯 Detected: fal-generate-image
- Routes to image generation
- ✅ Result URL
```

**Test 4: Error Handling**
```bash
/fal-generate-image ""  # Empty prompt
Expected:
- ❌ Prompt required
- Usage message
```

### Automated Testing

```bash
# Run all tests
python3 -m unittest discover tests/

# Run intent detection tests only
python3 -m unittest tests.test_intent_detection
```

---

## Deliverables Checklist

### Critical (Must-Have)
- [x] `/fal-generate-image` skill (`skills/fal-generate-image/SKILL.md`)
- [x] `/fal-remove-bg` skill (`skills/fal-remove-bg/SKILL.md`)
- [x] `/fal-generate` orchestrator (`skills/fal-generate/SKILL.md`)
- [x] Python CLI commands in `scripts/fal_api.py`
- [x] Intent detection script (`scripts/detect_intent.py`)
- [x] Tests for intent detection

### Important (Should-Have)
- [x] Image upload helper (`scripts/upload_image.py`)
- [x] Error handling for all failure modes
- [x] Clear user feedback messages
- [x] Skill documentation with examples

### Nice-to-Have
- [ ] Progress indicators for long operations
- [ ] Download result option in remove-bg
- [ ] Cost tracking
- [ ] Multiple size/quality presets

---

## Branch Strategy

**Branch**: `feat/phase-2-generation-skills`

**Workflow**:
```bash
# Create new branch from main
git checkout main
git pull origin main
git checkout -b feat/phase-2-generation-skills

# Implement skills incrementally
git add skills/fal-generate-image/
git commit -m "feat(skill): add /fal-generate-image skill"

git add skills/fal-remove-bg/
git commit -m "feat(skill): add /fal-remove-bg skill"

git add skills/fal-generate/
git commit -m "feat(skill): add /fal-generate orchestrator"

# When complete, merge to main
git checkout main
git merge feat/phase-2-generation-skills
```

---

## Risk Management

### High Priority Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Response Adapter fails on new model | High | Test with multiple models, add fallback patterns |
| Image upload complexity | Medium | Start with URL-only, add upload in Phase 3 |
| Intent detection accuracy | Medium | Start simple, improve with user feedback |
| Network timeouts on slow models | Medium | Already have 30s timeout + retry logic |

### Medium Priority Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Skill parameter parsing fragile | Low | Use simple bash parsing, validate inputs |
| Error messages unclear | Low | Test with real users, iterate |
| Cost tracking missing | Low | Add in Phase 4 |

---

## Success Criteria Summary

**Phase 2 is complete when:**
- ✅ All three skills work end-to-end
- ✅ Response Adapter successfully extracts results
- ✅ Test coverage for skill logic
- ✅ Clear error messages for common failures
- ✅ Documentation with examples

**Phase 3 Ready When:**
- `/fal-generate-image` and `/fal-remove-bg` proven reliable
- Intent detection works for common cases
- Orchestrator successfully routes requests
- User feedback collected for improvements

---

## References

### Internal References
- Response Adapter: `scripts/lib/adapter.py:72-102`
- API Client: `scripts/lib/api_client.py:29-77`
- Model Registry: `scripts/lib/models.py:25-53`
- Setup Skill: `skills/fal-setup/SKILL.md`

### External References
- fal.ai API docs: https://docs.fal.ai
- FLUX.1 model: https://fal.ai/models/fal-ai/flux/dev
- Birefnet: https://fal.ai/models/fal-ai/birefnet

### Related Plans
- Phase 1 Foundation: `docs/plans/2026-01-28-phase-1-foundation-implementation-plan.md`
- Phase 1 Refinements: `docs/plans/2026-01-28-phase-1-refinements-plan.md`

---

**Status**: Ready to implement
**Blocking Issues**: None
**Dependencies**: Phase 1 complete (Response Adapter, API Client, Model Registry)
**Estimated Total Time**: 14-20 hours (2-3 days)
