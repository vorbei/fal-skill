# /fal-edit-photo

Advanced image editing using the Fibo Edit suite - colorize, relight, reseason, restore, restyle, and object manipulation.

## Usage

```
# Colorize black & white photos
/fal-edit-photo old_bw_photo.jpg --operation colorize

# Change lighting
/fal-edit-photo portrait.jpg --operation relight --lighting-prompt "sunset golden hour"

# Change season
/fal-edit-photo landscape.jpg --operation reseason --season winter

# Restore old photos
/fal-edit-photo damaged.jpg --operation restore

# Apply artistic style
/fal-edit-photo photo.jpg --operation restyle --style-prompt "watercolor painting"
```

## What it does

1. Validates API key is configured
2. Parses image URL/path and operation parameters
3. Selects appropriate Fibo Edit model based on operation
4. Applies editing operation (fast, <10s)
5. Extracts result URL using Response Adapter
6. Displays edited image with metadata

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
IMAGE_URL=""
OPERATION=""
PROMPT=""
STRENGTH=0.8
LIGHTING_PROMPT=""
SEASON=""
STYLE_PROMPT=""

# Parse all arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --operation)
      OPERATION="$2"
      shift 2
      ;;
    --prompt)
      PROMPT="$2"
      shift 2
      ;;
    --strength)
      STRENGTH="$2"
      shift 2
      ;;
    --lighting-prompt)
      LIGHTING_PROMPT="$2"
      shift 2
      ;;
    --season)
      SEASON="$2"
      shift 2
      ;;
    --style-prompt)
      STYLE_PROMPT="$2"
      shift 2
      ;;
    *)
      # First non-flag argument is the image URL/path
      if [ -z "$IMAGE_URL" ]; then
        IMAGE_URL="$1"
      fi
      shift
      ;;
  esac
done

# Validation
if [ -z "$IMAGE_URL" ]; then
  echo "❌ Image URL/path required"
  echo ""
  echo "Usage: /fal-edit-photo <image> --operation <op> [options]"
  echo ""
  echo "Operations:"
  echo "  colorize      - Add color to black & white photos"
  echo "  relight       - Change lighting conditions"
  echo "  reseason      - Change season in photos"
  echo "  restore       - Repair old/damaged photos"
  echo "  restyle       - Apply artistic styles"
  echo ""
  echo "Examples:"
  echo "  /fal-edit-photo bw.jpg --operation colorize"
  echo "  /fal-edit-photo photo.jpg --operation relight --lighting-prompt \"sunset\""
  echo "  /fal-edit-photo scene.jpg --operation reseason --season winter"
  exit 1
fi

if [ -z "$OPERATION" ]; then
  echo "❌ Operation required. Use --operation <op>"
  echo "Available: colorize, relight, reseason, restore, restyle"
  exit 1
fi

# Validate operation
case "$OPERATION" in
  colorize|relight|reseason|restore|restyle|inpaint|outpaint|add-object|remove-object)
    # Valid
    ;;
  *)
    echo "❌ Invalid operation: $OPERATION"
    echo "Valid options: colorize, relight, reseason, restore, restyle"
    exit 1
    ;;
esac
```

### Step 3: Select Model Based on Operation

```bash
case "$OPERATION" in
  colorize)
    MODEL="fal-ai/fibo-edit/colorize"
    ;;
  relight)
    MODEL="fal-ai/fibo-edit/relight"
    ;;
  reseason)
    MODEL="fal-ai/fibo-edit/reseason"
    ;;
  restore)
    MODEL="fal-ai/fibo-edit/restore"
    ;;
  restyle)
    MODEL="fal-ai/fibo-edit/restyle"
    ;;
  *)
    echo "❌ Operation not yet supported: $OPERATION"
    exit 1
    ;;
esac
```

### Step 4: Call Python API Client

```bash
echo "✨ Editing image with $OPERATION..."
echo "📸 Image: $IMAGE_URL"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Build command
CMD="cd \"$SCRIPT_DIR\" && uv run python scripts/fal_api.py edit --model \"$MODEL\" --image-url \"$IMAGE_URL\" --operation \"$OPERATION\" --strength $STRENGTH"

if [ -n "$PROMPT" ]; then
  CMD="$CMD --prompt \"$PROMPT\""
fi

if [ -n "$LIGHTING_PROMPT" ]; then
  CMD="$CMD --lighting-prompt \"$LIGHTING_PROMPT\""
fi

if [ -n "$SEASON" ]; then
  CMD="$CMD --season \"$SEASON\""
fi

if [ -n "$STYLE_PROMPT" ]; then
  CMD="$CMD --style-prompt \"$STYLE_PROMPT\""
fi

# Execute editing operation (fast, <10s)
RESULT=$(eval "$CMD" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Editing failed:"
  echo "$RESULT"
  echo ""
  echo "Possible causes:"
  echo "  - Invalid image URL/path"
  echo "  - Unsupported image format"
  echo "  - API rate limit exceeded"
  echo "  - Operation not compatible with image"
  echo ""
  echo "Try: /fal-edit-photo image.jpg --operation restore"
  exit 1
fi
```

### Step 5: Display Result

```bash
# Parse response
EDITED_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])" 2>/dev/null)

if [ -z "$EDITED_URL" ]; then
  echo "❌ Could not extract edited image URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Image edited successfully!"
echo ""
echo "🖼️  Result: $EDITED_URL"
echo "✨ Operation: $OPERATION"
echo "🎚️  Strength: $STRENGTH"

case "$OPERATION" in
  relight)
    if [ -n "$LIGHTING_PROMPT" ]; then
      echo "💡 Lighting: $LIGHTING_PROMPT"
    fi
    ;;
  reseason)
    if [ -n "$SEASON" ]; then
      echo "🍂 Season: $SEASON"
    fi
    ;;
  restyle)
    if [ -n "$STYLE_PROMPT" ]; then
      echo "🎨 Style: $STYLE_PROMPT"
    fi
    ;;
esac

echo ""
echo "Tips:"
echo "  - Adjust --strength (0-1) to control effect intensity"
echo "  - Use multiple operations in sequence for complex edits"
echo "  - Original image is preserved (operation is non-destructive)"
```

## Operations

### colorize

Add natural color to black & white photos.

```bash
/fal-edit-photo old_photo.jpg --operation colorize
/fal-edit-photo old_photo.jpg --operation colorize --strength 0.9
```

**Parameters**:
- `--strength`: Effect intensity (0-1, default: 0.8)

### relight

Change lighting conditions in photos.

```bash
/fal-edit-photo photo.jpg --operation relight --lighting-prompt "sunset golden hour"
/fal-edit-photo photo.jpg --operation relight --lighting-prompt "studio lighting, soft"
```

**Parameters**:
- `--lighting-prompt`: Lighting description
- `--strength`: Effect intensity (0-1, default: 0.8)

### reseason

Transform the season in outdoor photos.

```bash
/fal-edit-photo summer.jpg --operation reseason --season winter
/fal-edit-photo winter.jpg --operation reseason --season spring
```

**Parameters**:
- `--season`: Target season (spring, summer, fall, winter)

### restore

Repair old, damaged, or low-quality photos.

```bash
/fal-edit-photo damaged.jpg --operation restore
/fal-edit-photo faded.jpg --operation restore --strength 1.0
```

**Parameters**:
- `--strength`: Restoration intensity (0-1, default: 0.8)

### restyle

Apply artistic styles to photos.

```bash
/fal-edit-photo photo.jpg --operation restyle --style-prompt "watercolor painting"
/fal-edit-photo photo.jpg --operation restyle --style-prompt "oil painting, impressionist"
/fal-edit-photo photo.jpg --operation restyle --style-prompt "pencil sketch"
```

**Parameters**:
- `--style-prompt`: Style description
- `--strength`: Style intensity (0-1, default: 0.8)

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | string | required | Image URL or local file path |
| `--operation` | string | required | Edit operation (colorize, relight, reseason, restore, restyle) |
| `--strength` | float | 0.8 | Effect intensity (0-1) |
| `--prompt` | string | - | General editing instruction |
| `--lighting-prompt` | string | - | Lighting description (for relight) |
| `--season` | string | - | Target season (for reseason) |
| `--style-prompt` | string | - | Style description (for restyle) |

## Examples

### Colorization

```bash
# Basic colorization
/fal-edit-photo bw_portrait.jpg --operation colorize

# Strong colorization
/fal-edit-photo bw_photo.jpg --operation colorize --strength 1.0

# Subtle colorization
/fal-edit-photo bw_photo.jpg --operation colorize --strength 0.5
```

### Relighting

```bash
# Golden hour sunset
/fal-edit-photo portrait.jpg --operation relight --lighting-prompt "sunset golden hour"

# Studio lighting
/fal-edit-photo photo.jpg --operation relight --lighting-prompt "studio lighting, soft shadows"

# Dramatic lighting
/fal-edit-photo scene.jpg --operation relight --lighting-prompt "dramatic side lighting, high contrast"
```

### Seasonal Transformation

```bash
# Summer to winter
/fal-edit-photo summer_scene.jpg --operation reseason --season winter

# Fall foliage
/fal-edit-photo landscape.jpg --operation reseason --season fall

# Spring bloom
/fal-edit-photo garden.jpg --operation reseason --season spring
```

### Photo Restoration

```bash
# Restore old photo
/fal-edit-photo vintage_photo.jpg --operation restore

# Aggressive restoration
/fal-edit-photo damaged_photo.jpg --operation restore --strength 1.0
```

### Artistic Restyling

```bash
# Watercolor effect
/fal-edit-photo photo.jpg --operation restyle --style-prompt "watercolor painting"

# Oil painting
/fal-edit-photo portrait.jpg --operation restyle --style-prompt "oil painting, thick brush strokes"

# Pencil sketch
/fal-edit-photo photo.jpg --operation restyle --style-prompt "pencil sketch, detailed"
```

## Cost Information

- All Fibo Edit operations: ~$0.01-0.02 per image
- Fast execution (<10 seconds)
- Budget-friendly compared to video operations
- Multiple edits can be chained for complex transformations

## Notes

- Editing is fast (<10 seconds per operation)
- Original image is never modified (non-destructive)
- Works best with high-quality input images (1024px+ recommended)
- Strength parameter controls effect intensity (0 = minimal, 1 = maximum)
- Can chain multiple operations for complex edits
- Supports common formats: JPG, PNG, WebP

## Troubleshooting

### Poor Colorization Results

```bash
# Solution: Adjust strength or use higher quality source image
/fal-edit-photo bw.jpg --operation colorize --strength 0.9
```

### Lighting Doesn't Match Prompt

```bash
# Solution: Be more specific in lighting description
/fal-edit-photo photo.jpg --operation relight --lighting-prompt "warm sunset, orange tones, soft shadows"
```

### Season Change Not Obvious

```bash
# Solution: Choose photos with obvious seasonal elements (trees, landscapes)
/fal-edit-photo landscape.jpg --operation reseason --season winter
```

## Related Skills

- `/fal-generate-image` - Generate new images from text
- `/fal-upscale` - Enhance image quality
- `/fal-remove-bg` - Remove image backgrounds
- `/fal-generate` - Smart orchestrator (auto-routes to editing when appropriate)
