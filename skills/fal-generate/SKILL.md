# /fal-generate

Universal generation orchestrator - detects intent and routes to specialized skills.

## Usage

```
/fal-generate "a wizard cat"
/fal-generate "remove background from image.jpg"
/fal-generate "portrait of a warrior in high quality"
```

## What it does

1. Analyzes user request to detect intent
2. Routes to appropriate specialized skill
3. Passes through parameters
4. Provides clear feedback on detected intent

## Instructions

### Step 1: Validate API Key

```bash
if [ ! -f ~/.config/fal-skill/.env ]; then
  echo "❌ API key not configured. Please run /fal-setup first."
  exit 1
fi
```

### Step 2: Parse User Request

```bash
USER_REQUEST="$*"

if [ -z "$USER_REQUEST" ]; then
  echo "❌ Request required. Usage: /fal-generate <what you want>"
  echo ""
  echo "Examples:"
  echo "  /fal-generate \"a fantasy castle\""
  echo "  /fal-generate \"remove background from photo.jpg\""
  echo "  /fal-generate \"portrait of a warrior in high quality\""
  exit 1
fi
```

### Step 3: Detect Intent

```bash
# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Detect intent using Python helper
INTENT=$(cd "$SCRIPT_DIR" && python3 scripts/detect_intent.py "$USER_REQUEST" 2>&1)
INTENT_EXIT=$?

if [ $INTENT_EXIT -ne 0 ]; then
  echo "❌ Could not understand request: $USER_REQUEST"
  echo ""
  echo "Try being more specific:"
  echo "  - For images: \"a wizard cat wearing purple robes\""
  echo "  - For background removal: \"remove background from image.jpg\""
  exit 1
fi

# Parse intent JSON
SKILL=$(echo "$INTENT" | python3 -c "import sys, json; print(json.load(sys.stdin)['skill'])" 2>/dev/null)
ARGS=$(echo "$INTENT" | python3 -c "import sys, json; print(' '.join(json.load(sys.stdin)['args']))" 2>/dev/null)

if [ -z "$SKILL" ]; then
  echo "❌ Failed to parse intent"
  echo "$INTENT"
  exit 1
fi

echo "🎯 Detected: $SKILL"
echo "📝 Request: $USER_REQUEST"
echo ""
```

### Step 4: Route to Specialized Skill

```bash
# Route to appropriate skill based on detected intent
case "$SKILL" in
  fal-generate-image)
    # Call fal-generate-image with detected args
    # The detect_intent script returns args in the format:
    # ["prompt text", "--size SIZE", "--quality QUALITY"]
    exec "$SCRIPT_DIR/skills/fal-generate-image/SKILL.md" $ARGS
    ;;

  fal-remove-bg)
    # Call fal-remove-bg with detected args
    # The detect_intent script returns args in the format:
    # ["image_url_or_path"]
    exec "$SCRIPT_DIR/skills/fal-remove-bg/SKILL.md" $ARGS
    ;;

  *)
    echo "❌ Unknown skill: $SKILL"
    echo ""
    echo "Supported skills:"
    echo "  - fal-generate-image (text-to-image generation)"
    echo "  - fal-remove-bg (background removal)"
    exit 1
    ;;
esac
```

## Intent Detection Examples

**Text-to-Image** (default):
- `"a wizard cat"` → `/fal-generate-image "a wizard cat" --size square_hd --quality balanced`
- `"portrait of a warrior"` → `/fal-generate-image "of a warrior" --size portrait_16_9 --quality balanced`
- `"quick sketch of a car"` → `/fal-generate-image "sketch of a car" --size square_hd --quality fast`
- `"detailed landscape"` → `/fal-generate-image "landscape" --size square_hd --quality high`

**Background Removal**:
- `"remove background from photo.jpg"` → `/fal-remove-bg photo.jpg`
- `"make transparent: image.png"` → `/fal-remove-bg image.png`
- `"cut out https://example.com/photo.jpg"` → `/fal-remove-bg https://example.com/photo.jpg`

## Error Handling

### Empty Request
```
❌ Request required. Usage: /fal-generate <what you want>

Examples:
  /fal-generate "a fantasy castle"
  /fal-generate "remove background from photo.jpg"
  /fal-generate "portrait of a warrior in high quality"
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

# Image with size hint
/fal-generate "portrait of a warrior"

# Image with quality hint
/fal-generate "high quality detailed painting"

# Background removal from URL
/fal-generate "remove background from https://example.com/photo.jpg"

# Background removal from local file
/fal-generate "make photo.png transparent"

# Fast generation
/fal-generate "quick sketch of a spaceship"
```

## How Intent Detection Works

The orchestrator uses `scripts/detect_intent.py` to analyze requests:

1. **Keyword Matching**: Looks for phrases like "remove background", "transparent", "cut out"
2. **Size Hints**: Detects "portrait", "landscape", "square" in the prompt
3. **Quality Hints**: Detects "fast", "quick", "high quality", "detailed"
4. **Default Behavior**: Assumes text-to-image if no background removal keywords

The detected intent is then translated into appropriate skill calls with the right parameters.

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
- `/fal-setup` - Configure API key
