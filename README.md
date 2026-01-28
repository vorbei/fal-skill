# fal.ai Skill for Claude Code

A comprehensive Claude Code skill for generating images, videos, audio, and more using fal.ai's powerful AI models.

## Features

- 🎨 **Image Generation**: 150+ models including Flux Pro/Dev, z-image
- 🎬 **Video Generation**: Text-to-video and image-to-video with Kling series
- 🗣️ **Text-to-Speech**: 40+ TTS models including ElevenLabs, Kokoro (multi-language)
- 🎵 **Music Generation**: Beatoven, CassetteAI for music and sound effects
- ✂️ **Background Removal**: Birefnet v2 for clean cutouts
- 🎭 **Avatar & Lipsync**: 29 models for animated avatars
- 🖼️ **Image Editing**: Fibo Edit suite (colorize, relight, reseason, etc.)
- 📐 **Upscaling**: Image and video enhancement
- 🤖 **Intelligent Routing**: Automatic intent detection

## Quick Start

1. **Setup** (first time only):
   ```
   /fal-setup
   ```
   Follow the prompts to configure your fal.ai API key.

2. **Generate an image**:
   ```
   /fal-generate "a wizard cat wearing purple robes"
   ```

3. **Remove background**:
   ```
   /fal-remove-bg [upload your image]
   ```

## Available Skills

### Setup & Configuration
- `/fal-setup` - Configure API key

### Generation Skills (MVP - Phase 2)
- `/fal-generate` - Intelligent orchestrator with auto-routing
- `/fal-generate-image` - Text-to-image generation
- `/fal-remove-bg` - Background removal

### Extended Skills (Phase 4-5)
- `/fal-generate-video` - Video generation
- `/fal-edit-photo` - Advanced image editing (Fibo Edit suite)
- `/fal-generate-audio` - Text-to-speech
- `/fal-generate-music` - Music generation
- `/fal-avatar` - Lipsync avatars
- `/fal-face` - Face operations (swap, enhance)
- `/fal-upscale` - Image/video upscaling

## Architecture

```
fal-skill/
├── skills/          # Claude Code skill definitions
├── scripts/         # Python API client and utilities
│   └── lib/         # Core modules (api_client, discovery, models)
├── models/          # Model registry
│   ├── curated.yaml # Hand-picked recommended models
│   └── cache/       # Discovered models cache (24h TTL)
└── config/          # Configuration and learned patterns
```

## Key Features

- **Dynamic Model Discovery**: Automatically discovers 1,000+ models from fal.ai API
- **Intelligent Caching**: 24-hour cache reduces API calls
- **Curated Fallback**: Hand-picked models ensure reliability
- **Cost Awareness**: Defaults to budget-friendly models
- **Self-Learning**: Response adapter learns field patterns

## Requirements

- Python 3.8+ (stdlib only, no external dependencies)
- fal.ai API key (get one at https://fal.ai/dashboard/keys)
- Claude Code

## Project Status

- ✅ **Phase 0**: Planning and architecture (Complete)
- ✅ **Phase 1**: Foundation (Complete)
  - [x] Git repository initialized
  - [x] Directory structure
  - [x] API client with discovery
  - [x] Setup skill
  - [x] Curated model registry
  - [x] Model discovery (1117 models)
- ⏳ **Phase 2**: Core generation skills
- ⏳ **Phase 3**: Intelligence layer
- ⏳ **Phase 4-5**: Video, audio, advanced editing
- ⏳ **Phase 6**: Polish and documentation

## Documentation

- [Full Implementation Plan](docs/plans/2026-01-28-feat-fal-ai-multi-capability-skill-plan.md)
- [Architecture Brainstorm](brainstorm/2026-01-28-fal-skill-architecture-brainstorm.md)
- [Architecture Summary](brainstorm/ARCHITECTURE-SUMMARY.md)
- [fal.ai Best Practices](brainstorm/02-fal-ai-best-practices.md)

## Contributing

See [Phase 1 Implementation Plan](docs/plans/2026-01-28-phase-1-foundation-implementation-plan.md) for current tasks.

## License

[Your License Here]
