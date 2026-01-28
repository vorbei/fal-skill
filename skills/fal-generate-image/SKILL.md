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
# Parse arguments
PROMPT=""
SIZE="square_hd"
QUALITY="balanced"

# Parse all arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --size)
      SIZE="$2"
      shift 2
      ;;
    --quality)
      QUALITY="$2"
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

if [ -z "$PROMPT" ]; then
  echo "❌ Prompt required. Usage: /fal-generate-image \"your prompt here\""
  echo ""
  echo "Examples:"
  echo "  /fal-generate-image \"a serene mountain landscape\""
  echo "  /fal-generate-image \"portrait of a warrior\" --size portrait_16_9"
  echo "  /fal-generate-image \"detailed fantasy castle\" --quality high"
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

### Step 4: Call Python API Client

```bash
echo "⏳ Generating image with $MODEL..."
echo "📝 Prompt: $PROMPT"
echo "📐 Size: $SIZE"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Execute model via Python CLI
RESULT=$(cd "$SCRIPT_DIR" && python3 scripts/fal_api.py generate \
  --model "$MODEL" \
  --prompt "$PROMPT" \
  --size "$SIZE" \
  --steps "$STEPS" \
  --guidance 3.5 \
  2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Generation failed:"
  echo "$RESULT"
  echo ""
  echo "Possible causes:"
  echo "  - Invalid prompt (check for banned content)"
  echo "  - API rate limit exceeded"
  echo "  - Model temporarily unavailable"
  echo ""
  echo "Try: /fal-generate-image \"simpler prompt\" --quality fast"
  exit 1
fi
```

### Step 5: Display Result

```bash
# Parse response
IMAGE_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])" 2>/dev/null)

if [ -z "$IMAGE_URL" ]; then
  echo "❌ Could not extract image URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Image generated!"
echo ""
echo "🖼️  Result: $IMAGE_URL"
echo "🎨 Model: $MODEL"
echo "⚙️  Quality: $QUALITY"
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

Examples:
  /fal-generate-image "a serene mountain landscape"
  /fal-generate-image "portrait of a warrior" --size portrait_16_9
  /fal-generate-image "detailed fantasy castle" --quality high
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

## Parameters

### --size
Valid options:
- `square_hd` (default) - 1024x1024
- `square` - 512x512
- `portrait_4_3` - 768x1024
- `portrait_16_9` - 576x1024
- `landscape_4_3` - 1024x768
- `landscape_16_9` - 1024x576

### --quality
- `fast` - FLUX.1 dev with 20 steps (~5s)
- `balanced` (default) - FLUX.1 dev with 28 steps (~7s)
- `high` - FLUX.1 pro with 28 steps (~10s)

## Related Skills

- `/fal-remove-bg` - Remove image backgrounds
- `/fal-generate` - Universal generator (detects intent)
- `/fal-setup` - Configure API key
