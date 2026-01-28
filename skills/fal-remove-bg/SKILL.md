# /fal-remove-bg

Remove backgrounds from images using AI.

## Usage

```
/fal-remove-bg https://example.com/image.jpg
/fal-remove-bg path/to/image.png
/fal-remove-bg [upload image file]
```

## What it does

1. Validates image input (file, URL, or path)
2. Uploads image if needed (to fal.ai storage)
3. Calls birefnet/v2 model
4. Extracts transparent PNG result
5. Displays result with optional download

## Instructions

### Step 1: Validate API Key

```bash
if [ ! -f ~/.config/fal-skill/.env ]; then
  echo "❌ API key not configured. Please run /fal-setup first."
  exit 1
fi
```

### Step 2: Validate Input

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

### Step 3: Determine Input Type

```bash
# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Check if input is a URL
if [[ "$INPUT" =~ ^https?:// ]]; then
  IMAGE_URL="$INPUT"
  echo "📥 Using provided URL"

# Check if input is a local file path
elif [ -f "$INPUT" ]; then
  # Upload to fal.ai storage
  echo "⏳ Uploading image..."
  IMAGE_URL=$(cd "$SCRIPT_DIR" && python3 scripts/upload_image.py "$INPUT" 2>&1)
  UPLOAD_EXIT=$?

  if [ $UPLOAD_EXIT -ne 0 ]; then
    echo "❌ Failed to upload image:"
    echo "$IMAGE_URL"
    echo ""
    echo "Possible causes:"
    echo "  - File too large (>10MB)"
    echo "  - Invalid image format (use PNG, JPG, WEBP)"
    echo "  - Network issue"
    echo ""
    echo "Try: Compress image or use a URL instead"
    exit 1
  fi

  echo "✅ Uploaded: $IMAGE_URL"

else
  echo "❌ Invalid input: $INPUT"
  echo "Must be a URL (http:// or https://) or valid file path"
  exit 1
fi
```

### Step 4: Call Background Removal API

```bash
MODEL="fal-ai/birefnet/v2"

echo "⏳ Removing background with birefnet..."
echo ""

# Execute model via Python CLI
# birefnet/v2 expects image_url parameter
INPUT_JSON="{\"image_url\":\"$IMAGE_URL\"}"

RESULT=$(cd "$SCRIPT_DIR" && python3 scripts/fal_api.py run "$MODEL" "$INPUT_JSON" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Background removal failed:"
  echo "$RESULT"
  echo ""
  echo "Possible causes:"
  echo "  - Invalid image format"
  echo "  - Image too large (>4096x4096)"
  echo "  - API rate limit"
  echo ""
  echo "Try: Use a smaller image or wait a moment"
  exit 1
fi
```

### Step 5: Extract and Display Result

```bash
# Parse response - birefnet returns image in 'image' field
RESULT_URL=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Try common response fields
    if 'image' in data:
        if isinstance(data['image'], dict) and 'url' in data['image']:
            print(data['image']['url'])
        elif isinstance(data['image'], str):
            print(data['image'])
    elif 'url' in data:
        print(data['url'])
    elif 'output' in data:
        if isinstance(data['output'], dict) and 'url' in data['output']:
            print(data['output']['url'])
        elif isinstance(data['output'], str):
            print(data['output'])
except:
    pass
" 2>/dev/null)

if [ -z "$RESULT_URL" ]; then
  echo "❌ Could not extract result URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Background removed!"
echo ""
echo "🖼️  Result: $RESULT_URL"
echo "📥 Original: $IMAGE_URL"
echo ""
echo "💡 Tip: Right-click the URL to save the transparent PNG"
```

## Error Handling

### No Image Provided
```
❌ Image required. Usage: /fal-remove-bg <image-url-or-path>

Examples:
  /fal-remove-bg https://example.com/photo.jpg
  /fal-remove-bg ~/Downloads/photo.png
  /fal-remove-bg [upload file via Claude Code]
```

### Invalid URL
```
❌ Invalid input: [url]
Must be a URL (http:// or https://) or valid file path
```

### File Not Found
```
❌ Invalid input: [path]
Must be a URL (http:// or https://) or valid file path
```

### Upload Failed
```
❌ Failed to upload image:
[error details]

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
  - Image too large (>4096x4096)
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
/fal-remove-bg /tmp/uploaded_image.jpg
```

## Technical Notes

**Supported Formats**:
- Input: PNG, JPG, JPEG, WEBP
- Output: PNG with transparency

**Size Limits**:
- Max upload: 10MB
- Max dimensions: 4096x4096

**Model**: fal-ai/birefnet/v2
- Fast processing (1-3 seconds)
- High-quality edge detection
- Works on photos, illustrations, logos

**Processing Time**: ~1-3 seconds

## Related Skills

- `/fal-generate-image` - Generate new images
- `/fal-generate` - Universal generator
- `/fal-setup` - Configure API key
