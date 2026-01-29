# /fal-generate-audio

Text-to-speech generation using fal.ai models.

## Usage

```
/fal-generate-audio "Hello, this is a test"
/fal-generate-audio "Hola mundo" --language es
/fal-generate-audio "Welcome back" --model fal-ai/elevenlabs/tts/turbo-v2.5 --voice Aria
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

### Step 2: Parse Input

```bash
TEXT=""
MODEL_OVERRIDE=""
VOICE=""
SPEED=""
LANGUAGE=""
STABILITY=""
SIMILARITY_BOOST=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --model)
      MODEL_OVERRIDE="$2"
      shift 2
      ;;
    --voice)
      VOICE="$2"
      shift 2
      ;;
    --speed)
      SPEED="$2"
      shift 2
      ;;
    --language)
      LANGUAGE="$2"
      shift 2
      ;;
    --stability)
      STABILITY="$2"
      shift 2
      ;;
    --similarity-boost)
      SIMILARITY_BOOST="$2"
      shift 2
      ;;
    *)
      TEXT="$TEXT $1"
      shift
      ;;
  esac
done

TEXT=$(echo "$TEXT" | xargs)

if [ -z "$TEXT" ]; then
  echo "❌ Text required. Usage: /fal-generate-audio \"your text\""
  exit 1
fi
```

### Step 3: Get Model from Curated List

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

if [ -n "$MODEL_OVERRIDE" ]; then
  MODEL="$MODEL_OVERRIDE"
else
  MODEL=$(cd "$SCRIPT_DIR" && uv run python scripts/get_model.py tts 2>/dev/null)
  if [ -z "$MODEL" ]; then
    MODEL="fal-ai/elevenlabs/tts/turbo-v2.5"
  fi
fi

echo "🔊 Generating audio..."
echo "📝 Text: $TEXT"
echo "🤖 Model: $MODEL"
echo ""
```

### Step 4: Call API

```bash
CMD="cd \"$SCRIPT_DIR\" && uv run python scripts/fal_api.py tts --model \"$MODEL\" --text \"$TEXT\""

if [ -n "$VOICE" ]; then
  CMD="$CMD --voice \"$VOICE\""
fi
if [ -n "$SPEED" ]; then
  CMD="$CMD --speed \"$SPEED\""
fi
if [ -n "$LANGUAGE" ]; then
  CMD="$CMD --language \"$LANGUAGE\""
fi
if [ -n "$STABILITY" ]; then
  CMD="$CMD --stability \"$STABILITY\""
fi
if [ -n "$SIMILARITY_BOOST" ]; then
  CMD="$CMD --similarity-boost \"$SIMILARITY_BOOST\""
fi

RESULT=$(eval "$CMD" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ TTS failed:"
  echo "$RESULT"
  exit 1
fi
```

### Step 5: Display Result

```bash
AUDIO_URL=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])" 2>/dev/null)

if [ -z "$AUDIO_URL" ]; then
  echo "❌ Could not extract audio URL from response"
  echo "$RESULT"
  exit 1
fi

echo "✅ Audio generated!"
echo "🔊 Result: $AUDIO_URL"
```

## Available Models

Models are loaded from `models/curated.yaml` under the `tts` category.

To list available models:
```bash
uv run python scripts/get_model.py tts --list
```

## Notes

- Default model is the recommended one from curated.yaml
- Use `--model` to override with any model from the curated list

## Cache Control

Results cached in `~/.cache/fal-skill/generate/` by hash of input parameters.

- **Default**: Use cache if same request exists
- **`--force`**: Force regenerate, ignore cache

Cache key: `{model}:{text}:{voice}:{language}`
