---
name: fal-ai
description: |
  Generate and edit images, videos, audio, and music using fal.ai API. This skill provides a comprehensive suite of AI media generation capabilities including text-to-image, text-to-video, image-to-video, video editing, text-to-speech, music generation, background removal, avatar creation with lipsync, and speech-to-text transcription. Use when the user wants to generate images, create videos, produce audio/music, remove backgrounds, create talking avatars, or transcribe speech.
---

# fal-ai

AI-powered media generation and editing using fal.ai API.

## Capabilities

| Command | Description |
|---------|-------------|
| `/fal-ai setup` | Configure API key |
| `/fal-ai generate <prompt>` | Smart routing - auto-detect intent and route to appropriate generator |
| `/fal-ai image <prompt>` | Generate image from text |
| `/fal-ai video <prompt>` | Generate video from text or image |
| `/fal-ai audio <text>` | Text-to-speech generation |
| `/fal-ai music <prompt>` | Generate music or sound effects |
| `/fal-ai edit-photo <image> <prompt>` | Edit image with AI |
| `/fal-ai edit-video <video> [--prompt]` | Edit video (effects, background removal) |
| `/fal-ai remove-bg <image>` | Remove image background |
| `/fal-ai avatar --audio <audio> --image <image>` | Create lipsync avatar video |
| `/fal-ai transcribe <audio>` | Speech-to-text transcription |

## Setup

Before using any command, configure the API key:

```bash
# Check if API key exists
if [ ! -f ~/.config/fal-skill/.env ]; then
  # Prompt user for API key
  # Get from: https://fal.ai/dashboard/keys
  mkdir -p ~/.config/fal-skill
  echo "FAL_KEY=<user-provided-key>" > ~/.config/fal-skill/.env
  chmod 600 ~/.config/fal-skill/.env
fi
```

## Quick Reference

### Image Generation

```bash
# Basic
uv run python scripts/fal_api.py generate --model "fal-ai/flux-2" --prompt "a wizard cat" --size square_hd --steps 28 --guidance 3.5

# Sizes: square_hd, square, portrait_4_3, portrait_16_9, landscape_4_3, landscape_16_9
# Quality tiers: fast (20 steps), balanced (28 steps), high (flux-2-pro)
```

### Video Generation

```bash
# Text-to-video
uv run python scripts/fal_api.py video --model "fal-ai/veo3.1/fast" --prompt "a cat walking" --duration 5 --aspect-ratio 16:9

# Image-to-video
uv run python scripts/fal_api.py video --model "fal-ai/veo3.1/fast/image-to-video" --prompt "animate" --image-url "https://..." --duration 5

# Video-to-video (remix)
uv run python scripts/fal_api.py video --model "fal-ai/sora-2/video-to-video/remix" --prompt "make it anime" --video-url "https://..."
```

### Audio Generation (TTS)

```bash
# Basic TTS (ElevenLabs - 30+ languages, best quality)
uv run python scripts/fal_api.py tts --model "fal-ai/elevenlabs/tts/turbo-v2.5" --text "Hello world"

# With voice
uv run python scripts/fal_api.py tts --model "fal-ai/elevenlabs/tts/turbo-v2.5" --text "Hello" --voice Aria
```

### Music Generation

```bash
# Music
uv run python scripts/fal_api.py music --model "fal-ai/elevenlabs/music" --prompt "upbeat electronic"

# Sound effects
uv run python scripts/fal_api.py music --model "cassetteai/sound-effects-generator" --prompt "thunder" --duration 5

# Music with lyrics
uv run python scripts/fal_api.py music --model "fal-ai/minimax-music/v2" --prompt "indie folk" --lyrics "[verse]Walking alone..."
```

### Image Editing

```bash
# Edit image
uv run python scripts/fal_api.py run "fal-ai/qwen-image-max/edit" '{"image_urls": ["https://..."], "prompt": "add sunglasses"}'
```

### Video Editing

```bash
# Apply effects
uv run python scripts/fal_api.py video-edit --model "fal-ai/wan-effects" --video-url "https://..." --prompt "cinematic neon glow"

# Remove background
uv run python scripts/fal_api.py video-edit --model "veed/video-background-removal" --video-url "https://..."
```

### Background Removal

```bash
uv run python scripts/fal_api.py run "fal-ai/birefnet/v2" '{"image_url": "https://..."}'
```

### Avatar (Lipsync)

```bash
uv run python scripts/fal_api.py avatar --model "veed/fabric-1.0" --audio-url "https://..." --image-url "https://..."
```

### Transcription (ASR)

```bash
uv run python scripts/fal_api.py transcribe --model "fal-ai/elevenlabs/speech-to-text/scribe-v2" --audio-url "https://..."
```

## Model Selection

To get recommended model for a category:

```bash
uv run python scripts/get_model.py <category>
# Categories: text-to-image, background-removal, text-to-video, image-to-video,
#             video-to-video, video-editing, image-editing, tts, music-audio,
#             lipsync-avatar, asr
```

To list all models in a category:

```bash
uv run python scripts/get_model.py <category> --list
```

## File Upload

To upload local files before API calls:

```bash
URL=$(uv run python scripts/upload_image.py /path/to/file.jpg)
echo $URL  # Use this URL in API calls
```

Supported formats:
- Images: jpg, jpeg, png, webp, gif
- Videos: mp4
- Audio: wav, mp3, m4a, aac, flac, ogg

Max size: 10MB

## Intent Detection

The `/fal-ai generate` command auto-detects intent:

```bash
uv run python scripts/detect_intent.py "a wizard cat"
# → {"skill": "fal-generate-image", "args": [...]}

uv run python scripts/detect_intent.py "remove background from photo.jpg"
# → {"skill": "fal-remove-bg", "args": ["photo.jpg"]}

uv run python scripts/detect_intent.py "create a video of ocean waves"
# → {"skill": "fal-generate-video", "args": [...]}
```

## Response Handling

All API responses are normalized by the ResponseAdapter. Common response patterns:

```python
# Images
{"images": [{"url": "..."}]}  # or {"image": {"url": "..."}}

# Videos
{"video": {"url": "..."}}  # or {"video": "url"}

# Audio
{"audio": {"url": "..."}}  # or {"url": "..."}
```

## Cache

Results are cached in `~/.cache/fal-skill/generate/` by hash of input parameters.

- Default: Use cache if same request exists
- Use `--force` flag to regenerate

## Error Handling

Common errors:

| Error | Cause | Solution |
|-------|-------|----------|
| API key not configured | Missing ~/.config/fal-skill/.env | Run setup |
| File too large (>10MB) | Upload limit | Compress file |
| Invalid image format | Unsupported format | Use PNG, JPG, WEBP |
| Rate limit exceeded | Too many requests | Wait and retry |

## Model Reference

See `references/models.yaml` for complete model catalog with:
- Endpoint IDs
- Cost tiers (budget, standard, premium)
- Speed tiers (fast, medium, slow)
- Quality tiers (medium, high, highest)
- Required parameters

## Dependencies

```
fal-client>=0.5.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

Install with: `uv pip install -r requirements.txt`
