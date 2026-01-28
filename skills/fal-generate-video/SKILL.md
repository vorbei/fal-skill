# /fal-generate-video

Generate videos from text descriptions or animate images using fal.ai models with async workflow support.

## Usage

```
# Text-to-video
/fal-generate-video "a wizard cat casting magical spells"
/fal-generate-video "ocean waves at sunset" --duration 10 --aspect-ratio 16:9

# Image-to-video (animate an image)
/fal-generate-video "walking forward" --image-url cat.jpg --duration 5
```

## What it does

1. Validates API key is configured
2. Parses prompt/image and optional parameters (duration, aspect ratio)
3. Selects appropriate video model (Kling v1 Standard by default)
4. Submits video generation job via async workflow
5. Polls for completion with progress indication (30-120s)
6. Extracts result URL using Response Adapter
7. Displays video with metadata and generation time

## Instructions

### Step 1: Validate API Key

Check if user has run setup:

```bash
#!/usr/bin/env bash
if [ ! -f ~/.config/fal-skill/.env ]; then
  echo "❌ API key not configured. Please run /fal-setup first."
  exit 1
fi
```

### Step 2: Parse User Input

Extract prompt/image and optional parameters:

```bash
# Parse arguments
PROMPT=""
IMAGE_URL=""
DURATION=5
ASPECT_RATIO="16:9"
NEGATIVE_PROMPT=""

# Parse all arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --image-url)
      IMAGE_URL="$2"
      shift 2
      ;;
    --duration)
      DURATION="$2"
      shift 2
      ;;
    --aspect-ratio)
      ASPECT_RATIO="$2"
      shift 2
      ;;
    --negative-prompt)
      NEGATIVE_PROMPT="$2"
      shift 2
      ;;
    *)
      # Everything else is part of the prompt
      PROMPT="$PROMPT $1"
      shift
      ;;
  esac
done

# Trim leading/trailing spaces
PROMPT=$(echo "$PROMPT" | xargs)

# Validation
if [ -z "$IMAGE_URL" ] && [ -z "$PROMPT" ]; then
  echo "❌ Either --prompt or --image-url required"
  echo ""
  echo "Usage:"
  echo "  Text-to-video: /fal-generate-video \"your prompt\""
  echo "  Image-to-video: /fal-generate-video \"motion description\" --image-url image.jpg"
  echo ""
  echo "Examples:"
  echo "  /fal-generate-video \"wizard cat casting spells\" --duration 5"
  echo "  /fal-generate-video \"walking forward\" --image-url cat.jpg"
  echo "  /fal-generate-video \"fireworks display\" --duration 10 --aspect-ratio 9:16"
  exit 1
fi

# Validate duration
if [[ ! "$DURATION" =~ ^(5|10)$ ]]; then
  echo "❌ Invalid duration: $DURATION. Must be 5 or 10 seconds"
  exit 1
fi

# Validate aspect ratio
case "$ASPECT_RATIO" in
  16:9|9:16|1:1|4:3|3:4)
    # Valid
    ;;
  *)
    echo "❌ Invalid aspect ratio: $ASPECT_RATIO"
    echo "Valid options: 16:9, 9:16, 1:1, 4:3, 3:4"
    exit 1
    ;;
esac
```

### Step 3: Select Model and Show Cost Warning

```bash
# Default to standard quality (budget-friendly)
MODEL="fal-ai/kling-video/v1/standard/text-to-video"

if [ -n "$IMAGE_URL" ]; then
  MODEL="fal-ai/kling-video/v1/standard/image-to-video"
fi

# Show cost warning for longer videos
if [ "$DURATION" = "10" ]; then
  echo "⚠️  Note: 10-second videos cost 2x more than 5-second videos"
  echo ""
fi
```

### Step 4: Call Python API Client with Async Workflow

```bash
# Determine mode
if [ -n "$IMAGE_URL" ]; then
  MODE="image-to-video"
  echo "🎬 Animating image (ETA: 45-90s)..."
  echo "📸 Image: $IMAGE_URL"
else
  MODE="text-to-video"
  echo "🎬 Generating video (ETA: 30-120s)..."
  echo "📝 Prompt: $PROMPT"
fi

echo "⏱️  Duration: ${DURATION}s"
echo "📐 Aspect Ratio: $ASPECT_RATIO"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Build command
CMD="cd \"$SCRIPT_DIR\" && uv run python scripts/fal_api.py video --model \"$MODEL\" --duration $DURATION --aspect-ratio \"$ASPECT_RATIO\""

if [ -n "$PROMPT" ]; then
  CMD="$CMD --prompt \"$PROMPT\""
fi

if [ -n "$IMAGE_URL" ]; then
  CMD="$CMD --image-url \"$IMAGE_URL\""
fi

if [ -n "$NEGATIVE_PROMPT" ]; then
  CMD="$CMD --negative-prompt \"$NEGATIVE_PROMPT\""
fi

# Execute with async workflow
# The Python CLI handles polling and progress indication
RESULT=$(eval "$CMD" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Video generation failed:"
  echo "$RESULT"
  echo ""
  echo "Possible causes:"
  echo "  - Invalid prompt (check for banned content)"
  echo "  - Generation timeout (try shorter duration)"
  echo "  - API rate limit exceeded"
  echo "  - Model temporarily unavailable"
  echo ""
  echo "Try: /fal-generate-video \"simpler prompt\" --duration 5"
  exit 1
fi
```

### Step 5: Display Result

```bash
# Parse response
VIDEO_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])" 2>/dev/null)
GEN_TIME=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('generation_time', 'N/A'))" 2>/dev/null)

if [ -z "$VIDEO_URL" ]; then
  echo "❌ Could not extract video URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Video generated!"
echo ""
echo "🎬 Result: $VIDEO_URL"
echo "⏱️  Generated in: ${GEN_TIME}s"
echo "🎞️  Duration: ${DURATION}s"
echo "📐 Aspect Ratio: $ASPECT_RATIO"
echo "🤖 Model: $MODEL"
echo ""
echo "Tips:"
echo "  - Use --duration 5 for faster/cheaper results"
echo "  - Use --aspect-ratio 9:16 for vertical videos (TikTok/Reels)"
echo "  - Use --negative-prompt to exclude unwanted elements"
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | required* | Text description for video generation |
| `--image-url` | string | - | Image URL for image-to-video mode |
| `--duration` | int | 5 | Video duration (5 or 10 seconds) |
| `--aspect-ratio` | string | 16:9 | Video aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4) |
| `--negative-prompt` | string | - | What to avoid in the video |

*Either `prompt` or `--image-url` is required

## Examples

### Text-to-Video

```bash
# Basic usage
/fal-generate-video "a wizard cat casting spells in a magical forest"

# With duration and aspect ratio
/fal-generate-video "ocean waves crashing on rocks" --duration 10 --aspect-ratio 16:9

# Vertical video for social media
/fal-generate-video "person dancing" --duration 5 --aspect-ratio 9:16

# With negative prompt
/fal-generate-video "beautiful sunset" --negative-prompt "people, buildings, text"
```

### Image-to-Video

```bash
# Animate an image
/fal-generate-video "walking forward gracefully" --image-url portrait.jpg --duration 5

# Add motion to a scene
/fal-generate-video "clouds moving, camera pan right" --image-url landscape.jpg --duration 10

# Character animation
/fal-generate-video "smiling and waving" --image-url character.png
```

## Cost Information

- **5-second video**: ~$0.05 (Standard), ~$0.15 (Pro)
- **10-second video**: ~$0.10 (Standard), ~$0.30 (Pro)
- Text-to-video and image-to-video have similar costs
- Default model is Standard (budget-friendly)

## Notes

- Video generation takes 30-120 seconds (async workflow with progress)
- 5-second duration is recommended for testing (faster and cheaper)
- 16:9 aspect ratio is best for general use
- 9:16 aspect ratio is ideal for TikTok/Instagram Reels/YouTube Shorts
- The async workflow shows real-time progress updates
- Generation may timeout after 3 minutes (retry with simpler prompts)

## Troubleshooting

### Generation Timeout

```bash
# Solution: Use shorter duration or simpler prompt
/fal-generate-video "cat" --duration 5  # Simpler
```

### Invalid Prompt Error

```bash
# Solution: Check for banned content (violence, explicit content)
/fal-generate-video "peaceful nature scene"  # Safe content
```

### Slow Generation

```bash
# Solution: Use 5-second duration (2x faster than 10s)
/fal-generate-video "your prompt" --duration 5
```

## Related Skills

- `/fal-generate-image` - Generate static images
- `/fal-edit-photo` - Edit images with Fibo Edit
- `/fal-upscale` - Enhance video quality
- `/fal-generate` - Smart orchestrator (auto-routes to video when appropriate)
