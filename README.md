# fal-skill

AI-powered media generation skills for Claude Code using [fal.ai](https://fal.ai) API.

## Installation

```bash
npx @anthropic-ai/claude-code skills add https://github.com/anthropics/fal-skill --skill fal-ai
```

## Available Skills

### fal-ai

Comprehensive AI media generation and editing:

| Command | Description |
|---------|-------------|
| `/fal-ai setup` | Configure API key |
| `/fal-ai generate <prompt>` | Smart routing - auto-detect intent |
| `/fal-ai image <prompt>` | Generate image from text |
| `/fal-ai video <prompt>` | Generate video from text or image |
| `/fal-ai audio <text>` | Text-to-speech (ElevenLabs) |
| `/fal-ai music <prompt>` | Generate music or sound effects |
| `/fal-ai edit-photo <image> <prompt>` | Edit image with AI |
| `/fal-ai edit-video <video>` | Video effects & background removal |
| `/fal-ai remove-bg <image>` | Remove image background |
| `/fal-ai avatar` | Create lipsync avatar video |
| `/fal-ai transcribe <audio>` | Speech-to-text transcription |

## Setup

1. Get your API key from [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)
2. Run `/fal-ai setup` and paste your key

## Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

Dependencies are installed automatically:
- `fal-client>=0.5.0`
- `pyyaml>=6.0`
- `python-dotenv>=1.0.0`

## Supported Models

See [models.yaml](skills/fal-ai/references/models.yaml) for the full list of supported models across categories:

- **Text-to-Image**: FLUX.1 dev/pro, Nano Banana Pro, GPT Image 1.5
- **Text-to-Video**: Veo 3.1, Sora 2 Pro
- **Image-to-Video**: Veo 3.1, Sora 2 Pro
- **Video Editing**: WAN Effects, VEED Background Removal
- **Image Editing**: Qwen Image Max, Nano Banana Pro Edit
- **TTS**: ElevenLabs Turbo, Kokoro, MiniMax Speech
- **Music**: ElevenLabs Music, MiniMax Music, CassetteAI SFX
- **Avatar**: VEED Fabric, LTX Audio-to-Video
- **ASR**: ElevenLabs Scribe v2

## License

MIT
