# /fal-edit-photo

Edit images using AI - add objects, modify elements, apply transformations.

## Usage

```
/fal-edit-photo image.jpg "add a wizard hat"
/fal-edit-photo portrait.jpg "add sunglasses" --model fal-ai/nano-banana-pro/edit
/fal-edit-photo photo.jpg "make it look like a watercolor painting"
```

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
IMAGE_URL=""
PROMPT=""
MODEL_OVERRIDE=""

# Parse all arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --model)
      MODEL_OVERRIDE="$2"
      shift 2
      ;;
    --prompt)
      PROMPT="$2"
      shift 2
      ;;
    *)
      # First non-flag argument is the image URL/path
      if [ -z "$IMAGE_URL" ]; then
        IMAGE_URL="$1"
      elif [ -z "$PROMPT" ]; then
        PROMPT="$1"
      fi
      shift
      ;;
  esac
done

# Validation
if [ -z "$IMAGE_URL" ]; then
  echo "❌ Image URL/path required"
  echo ""
  echo "Usage: /fal-edit-photo <image> <prompt> [--model <model>]"
  echo ""
  echo "Examples:"
  echo "  /fal-edit-photo photo.jpg \"add a hat\""
  echo "  /fal-edit-photo portrait.jpg \"make eyes blue\""
  echo "  /fal-edit-photo scene.jpg \"add snow\" --model fal-ai/gpt-image-1.5/edit"
  exit 1
fi

if [ -z "$PROMPT" ]; then
  echo "❌ Edit prompt required"
  echo ""
  echo "Usage: /fal-edit-photo <image> <prompt>"
  exit 1
fi
```

### Step 3: Get Model from Curated List

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

if [ -n "$MODEL_OVERRIDE" ]; then
  MODEL="$MODEL_OVERRIDE"
else
  # Get recommended model from curated.yaml
  MODEL=$(cd "$SCRIPT_DIR" && uv run python scripts/get_model.py image-editing 2>/dev/null)
  if [ -z "$MODEL" ]; then
    MODEL="fal-ai/qwen-image-max/edit"
  fi
fi

echo "✨ Editing image..."
echo "📸 Image: $IMAGE_URL"
echo "📝 Prompt: $PROMPT"
echo "🤖 Model: $MODEL"
echo ""
```

### Step 4: Call API

```bash
# These models use image_urls (array) format
INPUT_JSON="{\"image_urls\": [\"$IMAGE_URL\"], \"prompt\": \"$PROMPT\"}"

RESULT=$(cd "$SCRIPT_DIR" && uv run python scripts/fal_api.py run "$MODEL" "$INPUT_JSON" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Editing failed:"
  echo "$RESULT"
  exit 1
fi
```

### Step 5: Display Result

```bash
EDITED_URL=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Try different response formats
if 'images' in data and len(data['images']) > 0:
    img = data['images'][0]
    print(img.get('url', '') if isinstance(img, dict) else img)
elif 'image' in data:
    img = data['image']
    print(img.get('url', '') if isinstance(img, dict) else img)
elif 'url' in data:
    print(data['url'])
" 2>/dev/null)

if [ -z "$EDITED_URL" ]; then
  echo "❌ Could not extract edited image URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Image edited successfully!"
echo "🖼️  Result: $EDITED_URL"
```

## Available Models

Models are loaded from `models/curated.yaml` under the `image-editing` category.

To list available models:
```bash
uv run python scripts/get_model.py image-editing --list
```

## Examples

```bash
# Add objects
/fal-edit-photo portrait.jpg "add sunglasses"
/fal-edit-photo photo.jpg "add a rainbow in the sky"

# Modify elements
/fal-edit-photo face.jpg "change hair color to blue"
/fal-edit-photo room.jpg "change the wall color to green"

# Style transfer
/fal-edit-photo photo.jpg "make it look like an oil painting"
/fal-edit-photo scene.jpg "convert to anime style"

# Use specific model
/fal-edit-photo photo.jpg "add snow" --model fal-ai/gpt-image-1.5/edit
```

## Notes

- **Default model**: Qwen Image Max Edit (recommended for precise, semantic-aware edits)
- **Alternative**: Nano Banana Pro Edit (better for photorealistic lighting/textures)
- **Alternative**: GPT Image 1.5 Edit (may regenerate entire image - less precise)
- Use `--model` to override with any model from the curated list
- Supports common formats: JPG, PNG, WebP
- Original image is preserved (non-destructive editing)

## Cache Control

Results cached in `~/.cache/fal-skill/generate/` by hash of input parameters.

- **Default**: Use cache if same request exists
- **`--force`**: Force regenerate, ignore cache

Cache key: `{model}:{image_url}:{prompt}`

## Related Skills

- `/fal-generate-image` - Generate new images from text
- `/fal-remove-bg` - Remove image backgrounds
