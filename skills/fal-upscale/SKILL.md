# /fal-upscale

Enhance and upscale images or videos using AI-powered super-resolution.

## Usage

```
# Image upscaling
/fal-upscale image.jpg --scale 2
/fal-upscale lowres.png --scale 4
/fal-upscale photo.jpg --scale 8 --creativity 0.5

# Video upscaling (uses async workflow)
/fal-upscale video.mp4 --scale 2
/fal-upscale clip.mov --scale 4
```

## What it does

1. Validates API key is configured
2. Parses input (image or video) and scale parameters
3. Selects appropriate upscaler model (Crystal Upscaler by default)
4. For images: Applies upscaling (fast, 10-20s)
5. For videos: Uses async workflow with progress (30-60s)
6. Extracts result URL using Response Adapter
7. Displays enhanced media with metadata

## Instructions

### Step 1: Validate API Key

```bash
#!/usr/bin/env bash
if [ ! -f ~/.config/fal-skill/.env ]; then
  echo "❌ API key not configured. Please run /fal-setup first."
  exit 1
fi
```

### Step 2: Parse User Input

```bash
# Parse arguments
INPUT_FILE=""
SCALE=2
CREATIVITY=0.35
TYPE=""

# Parse all arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --scale)
      SCALE="$2"
      shift 2
      ;;
    --creativity)
      CREATIVITY="$2"
      shift 2
      ;;
    *)
      # First non-flag argument is the input file
      if [ -z "$INPUT_FILE" ]; then
        INPUT_FILE="$1"
      fi
      shift
      ;;
  esac
done

# Validation
if [ -z "$INPUT_FILE" ]; then
  echo "❌ Input file required"
  echo ""
  echo "Usage: /fal-upscale <file> --scale <2|4|8> [--creativity 0-1]"
  echo ""
  echo "Examples:"
  echo "  /fal-upscale image.jpg --scale 2"
  echo "  /fal-upscale lowres.png --scale 4"
  echo "  /fal-upscale video.mp4 --scale 2"
  exit 1
fi

# Validate scale
case "$SCALE" in
  2|4|8)
    # Valid for images
    ;;
  *)
    echo "❌ Invalid scale: $SCALE. Must be 2, 4, or 8"
    exit 1
    ;;
esac

# Detect type from file extension
case "$INPUT_FILE" in
  *.jpg|*.jpeg|*.png|*.webp)
    TYPE="image"
    IMAGE_URL="$INPUT_FILE"
    VIDEO_URL=""
    ;;
  *.mp4|*.mov|*.avi|*.webm|*.mkv)
    TYPE="video"
    VIDEO_URL="$INPUT_FILE"
    IMAGE_URL=""
    # Videos only support 2x and 4x
    if [ "$SCALE" = "8" ]; then
      echo "❌ Video upscaling only supports 2x and 4x"
      exit 1
    fi
    ;;
  *)
    echo "❌ Unsupported file format: $INPUT_FILE"
    echo "Supported: JPG, PNG, WebP (images), MP4, MOV, WebM (videos)"
    exit 1
    ;;
esac
```

### Step 3: Select Model

```bash
# Default to Crystal Upscaler (general-purpose)
MODEL="fal-ai/crystal-upscaler"

echo "🔍 Upscaling $TYPE..."
echo "📂 Input: $INPUT_FILE"
echo "📊 Scale: ${SCALE}x"
echo "🎨 Creativity: $CREATIVITY"
echo ""

if [ "$TYPE" = "video" ]; then
  echo "⏱️  ETA: 30-60 seconds (async workflow)"
  echo ""
fi
```

### Step 4: Call Python API Client

```bash
# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Build command
CMD="cd \"$SCRIPT_DIR\" && uv run python scripts/fal_api.py upscale --model \"$MODEL\" --scale $SCALE --creativity $CREATIVITY"

if [ "$TYPE" = "image" ]; then
  CMD="$CMD --image-url \"$IMAGE_URL\""
else
  CMD="$CMD --video-url \"$VIDEO_URL\""
fi

# Execute upscaling
# Video uses async workflow with progress indication
RESULT=$(eval "$CMD" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Upscaling failed:"
  echo "$RESULT"
  echo ""
  echo "Possible causes:"
  echo "  - Invalid file URL/path"
  echo "  - Unsupported file format"
  echo "  - File too large (max ~50MB for images, ~100MB for videos)"
  echo "  - API rate limit exceeded"
  echo ""
  echo "Try: /fal-upscale smaller_file.jpg --scale 2"
  exit 1
fi
```

### Step 5: Display Result

```bash
# Parse response
RESULT_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])" 2>/dev/null)
RESULT_TYPE=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('type', 'unknown'))" 2>/dev/null)

if [ -z "$RESULT_URL" ]; then
  echo "❌ Could not extract result URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Upscaling complete!"
echo ""
echo "🎯 Result: $RESULT_URL"
echo "📊 Scale: ${SCALE}x"
echo "📁 Type: $RESULT_TYPE"

# Show before/after info
if [ "$TYPE" = "image" ]; then
  echo ""
  echo "Quality improvement:"
  echo "  - Resolution increased by ${SCALE}x"
  echo "  - Enhanced details and sharpness"
  echo "  - AI-powered noise reduction"
else
  echo ""
  echo "Video enhancement:"
  echo "  - Resolution increased by ${SCALE}x"
  echo "  - Frame-by-frame enhancement"
  echo "  - Consistent quality across frames"
fi

echo ""
echo "Tips:"
echo "  - Use 2x for general enhancement (fastest)"
echo "  - Use 4x for significant quality boost"
echo "  - Use 8x for maximum detail (images only)"
echo "  - Adjust --creativity (0-1) for AI enhancement level"
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | string | required | Image or video file (URL or local path) |
| `--scale` | int | 2 | Upscale factor (2, 4, or 8) |
| `--creativity` | float | 0.35 | AI enhancement level (0-1) |

**Scale options**:
- **2x**: Fast, general-purpose (works for images and videos)
- **4x**: Significant quality boost (works for images and videos)
- **8x**: Maximum detail (images only)

**Creativity values**:
- **0.0-0.3**: Conservative enhancement (preserves original look)
- **0.35** (default): Balanced enhancement
- **0.5-1.0**: Aggressive enhancement (adds more AI-generated details)

## Examples

### Image Upscaling

```bash
# Basic 2x upscale
/fal-upscale lowres.jpg --scale 2

# 4x upscale with conservative enhancement
/fal-upscale photo.png --scale 4 --creativity 0.2

# Maximum quality with aggressive enhancement
/fal-upscale image.jpg --scale 8 --creativity 0.8
```

### Video Upscaling

```bash
# 2x upscale (fast, ~30-40s)
/fal-upscale video.mp4 --scale 2

# 4x upscale with high enhancement
/fal-upscale clip.mov --scale 4 --creativity 0.5
```

### Use Cases

```bash
# Enhance old photos
/fal-upscale vintage_photo.jpg --scale 4

# Improve screenshot quality
/fal-upscale screenshot.png --scale 2

# Upscale social media images
/fal-upscale instagram.jpg --scale 2 --creativity 0.5

# Enhance video quality for upload
/fal-upscale video_720p.mp4 --scale 2  # 720p → 1440p
```

## Cost Information

- **Image upscaling**: ~$0.01-0.05 per image (depending on scale)
- **Video upscaling**: ~$0.10-0.50 per video (depending on scale and duration)
- 2x scale is cheapest and fastest
- 4x scale takes longer and costs more
- 8x scale (images only) is most expensive but highest quality

## Performance

| Type | Scale | Time | Quality |
|------|-------|------|---------|
| Image | 2x | 10-15s | Good |
| Image | 4x | 15-20s | Excellent |
| Image | 8x | 20-30s | Maximum |
| Video | 2x | 30-45s | Good |
| Video | 4x | 45-60s | Excellent |

## Notes

- **Image upscaling**: Fast, uses blocking mode (10-30s)
- **Video upscaling**: Slower, uses async workflow with progress (30-60s)
- Videos only support 2x and 4x scale (not 8x)
- Best results with high-quality source material
- Creativity parameter controls AI enhancement intensity
- Original file is never modified (non-destructive)
- Maximum file sizes: ~50MB (images), ~100MB (videos)

## Supported Formats

**Images**:
- JPG/JPEG
- PNG
- WebP

**Videos**:
- MP4
- MOV
- WebM
- AVI
- MKV

## Troubleshooting

### File Too Large

```bash
# Solution: Compress or trim video first
ffmpeg -i large.mp4 -c:v libx264 -crf 23 smaller.mp4
/fal-upscale smaller.mp4 --scale 2
```

### Poor Upscaling Results

```bash
# Solution: Adjust creativity parameter
/fal-upscale image.jpg --scale 4 --creativity 0.2  # Conservative
/fal-upscale image.jpg --scale 4 --creativity 0.8  # Aggressive
```

### Video Timeout

```bash
# Solution: Use 2x instead of 4x for faster processing
/fal-upscale video.mp4 --scale 2
```

### Unsupported Format

```bash
# Solution: Convert to supported format first
ffmpeg -i input.avi -c:v libx264 output.mp4
/fal-upscale output.mp4 --scale 2
```

## Resolution Examples

### Image Upscaling

- **2x**: 1920x1080 → 3840x2160 (4K)
- **4x**: 1920x1080 → 7680x4320 (8K)
- **8x**: 1920x1080 → 15360x8640

### Video Upscaling

- **2x**: 1280x720 → 2560x1440 (2K/QHD)
- **4x**: 1280x720 → 5120x2880

## Related Skills

- `/fal-edit-photo` - Edit images before upscaling
- `/fal-generate-video` - Generate videos
- `/fal-generate-image` - Generate high-resolution images
- `/fal-generate` - Smart orchestrator (auto-routes to upscale when appropriate)
