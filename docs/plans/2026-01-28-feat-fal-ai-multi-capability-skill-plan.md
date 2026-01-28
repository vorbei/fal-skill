---
title: fal.ai Multi-Capability Skill Implementation
type: feat
date: 2026-01-28
---

# fal.ai Multi-Capability Skill Implementation

## Overview

Create a comprehensive fal.ai skill for Claude Code that supports the essential creative generation categories: image generation, video generation, audio/TTS, music generation, avatar/lipsync, face operations, upscaling, and advanced editing. The skill features intelligent orchestration, adaptive API response parsing, intent detection, and a self-learning system that improves over time.

**Scope**: Support for 12 core fal.ai categories (excluding 3D generation and model training) covering 1,000+ models.
**Excluded**: 3D generation (35 models) and model training/fine-tuning (34 models) - out of scope for initial implementation.

## Problem Statement / Motivation

Claude Code users need a seamless way to leverage fal.ai's powerful AI generation capabilities without:
- Managing API documentation complexity
- Dealing with inconsistent response formats across models
- Manually selecting appropriate models for different tasks
- Writing repetitive API integration code

**Current Gap**: No unified skill exists for fal.ai integration. Users would need to write custom API calls or use disparate tools.

**Value Proposition**: A single, intelligent entry point (`/fal-generate`) that handles intent detection, model selection, prompt optimization, and result parsing automatically.

## Proposed Solution

Implement a **layered skill architecture** with three intelligence tiers:

### Tier 1: High Intelligence (Orchestrator)
- `/fal-generate` - Universal entry point with intent detection and routing

### Tier 2: Medium Intelligence (Specialized Skills)

**Visual Generation:**
- `/fal-generate-image` - Text-to-image (150 models: Flux, Bria, AuraFlow, etc.)
- `/fal-generate-video` - Text/image-to-video (103 text-to-video, 152 image-to-video)
- `/fal-edit-photo` - Image editing (349 models: Fibo Edit suite, inpaint, outpaint)
- `/fal-remove-bg` - Background removal (36 models: Birefnet, Bria RMBG)
- `/fal-upscale` - Image/video upscaling (19 models: Crystal, Clarity, ESRGAN)

**Audio Generation:**
- `/fal-generate-audio` - Text-to-speech (40 TTS models: ElevenLabs, Chatterbox, Kokoro)
- `/fal-generate-music` - Music generation (62 models: Beatoven, CassetteAI)
- `/fal-transcribe` - Speech-to-text (12 ASR models)

**Avatar & Face:**
- `/fal-avatar` - Lipsync avatars (29 models: Argil, Kling AI Avatar, Live Portrait)
- `/fal-face` - Face operations (17 models: face swap, enhancement, portrait generation)

### Tier 3: Low Intelligence (Configuration)
- `/fal-setup` - API key management and initial configuration
- `/fal-update-model` - Model registry management

### Model Catalog Overview

**Source**: fal.ai Model List API (`GET https://api.fal.ai/v1/models`)
**Discovery**: Dynamic model discovery with pagination support
**Total Models**: 1,109+ (as of 2026-01-27, continuously updated)

**Category Breakdown:**
| Category | Count | Key Models |
|----------|-------|------------|
| **imageToImage** | 349 | Fibo Edit suite (colorize, relight, restyle), inpaint, outpaint |
| **textToImage** | 150 | Flux Pro/Dev, Bria, AuraFlow, Bagel, z-image/base |
| **imageToVideo** | 152 | Kling (O1, 1.5-2.6), Animatediff, Seedance |
| **videoToVideo** | 129 | Video transformation, style transfer |
| **textToVideo** | 103 | Kling, Seedance, Animatediff |
| **musicAudio** | 62 | Beatoven, CassetteAI (music + sound effects) |
| **tts** | 40 | ElevenLabs (turbo-v2.5, eleven-v3), Chatterbox, Kokoro (multi-lang) |
| **backgroundRemoval** | 36 | Birefnet v1/v2, Bria RMBG 2.0, video background removal |
| ~~**threeD**~~ | ~~35~~ | ~~Out of scope~~ |
| ~~**training**~~ | ~~34~~ | ~~Out of scope~~ |
| **lipsyncAvatar** | 29 | Argil Avatars, Kling AI Avatar v2, Live Portrait |
| **upscale** | 19 | Crystal (image+video), Clarity, Creative Upscaler, ESRGAN |
| **audioToAudio** | 17 | Voice cloning, audio transformation |
| **face** | 17 | Face swap, Live Portrait, face-to-sticker, headshot generator |
| **asr** | 12 | Speech-to-text, transcription |
| **videoToAudio** | 4 | Audio extraction from video |

**Notable Model Series:**
- **Kling Video**: 23 variants (versions O1, 1.5, 1.6, 2.0, 2.1, 2.5-turbo, 2.6 across Pro/Standard/Master tiers)
- **Flux Models**: 150+ variants for generation, editing, and training
- **Fibo Edit**: 10+ specialized editing operations (add/erase/replace objects, colorize, relight, reseason, restore, restyle)
- **Kokoro TTS**: 9+ language variants (American/British English, Portuguese, French, Hindi, Italian, etc.)

### Core Components

```
User Input
     ↓
┌────────────────────────┐
│  Intent Detection      │ ← Confidence scoring (explicit → context → keywords)
│                        │   Expanded: 16 category detection (image/video/audio/3D/etc)
├────────────────────────┤
│  Model Selection       │ ← Registry lookup by task/cost/speed/quality
│                        │   1,109 models organized by category
├────────────────────────┤
│  Prompt Engineering    │ ← Model-specific optimization
│                        │   Category-specific templates (image vs audio vs video)
├────────────────────────┤
│  fal.ai API Client     │ ← Python script for API calls
│                        │   Handles all 16 categories
├────────────────────────┤
│  Response Adapter      │ ← Self-learning field extraction
│                        │   Category-aware field patterns
└────────────────────────┘
         ↓
    Result + Learning
```

## Technical Considerations

### Architecture

**Directory Structure:**
```
fal-skill/
├── skills/
│   ├── fal-generate/
│   │   ├── SKILL.md              # Main orchestrator
│   │   └── scripts/
│   │       ├── fal_api.py        # API client
│   │       └── lib/
│   │           ├── intent.py     # Intent detection
│   │           ├── adapter.py    # Response parsing
│   │           ├── models.py     # Registry loader (dynamic)
│   │           └── discovery.py  # fal.ai API model discovery
│   ├── fal-setup/
│   │   └── SKILL.md              # Configuration wizard
│   ├── fal-generate-image/
│   │   └── SKILL.md              # Image generation
│   ├── fal-generate-video/
│   │   └── SKILL.md              # Video generation
│   ├── fal-edit-photo/
│   │   └── SKILL.md              # Image editing
│   └── fal-remove-bg/
│       └── SKILL.md              # Background removal
├── models/
│   ├── curated.yaml               # Curated core models (human-selected)
│   └── cache/
│       ├── discovered_models.json # Full model list from API (cached)
│       └── categories.json        # Category index (cached)
├── config/
│   └── response_patterns.yaml     # Learned response paths
└── docs/
    └── workflows.md               # Common pipelines
```

**Model Discovery Strategy**:
- **Dynamic**: Fetch from fal.ai API (`GET /v1/models`) with pagination
- **Caching**: Cache API responses (TTL: 24 hours) to reduce API calls
- **Curated Subset**: Maintain curated.yaml with 50-100 tested, recommended models
- **API Parameters**:
  - `limit=100` for pagination
  - `cursor` for next page
  - `category` filter for specific categories
  - `status=active` to exclude deprecated models
  - `expand=openapi-3.0` to get full schemas (optional, for advanced use)

**Technology Stack:**
- Python 3 (stdlib only) for API client
- YAML for configuration
- Bash for skill orchestration
- JSON for data exchange

### Security Considerations

1. **API Key Storage**: Store in `~/.config/fal-skill/.env` with `chmod 600`
2. **No Logging of Credentials**: Sanitize logs to exclude API keys
3. **Secure Transmission**: Use HTTPS for all API calls (fal.ai default)
4. **Input Validation**: Sanitize user prompts to prevent injection attacks

### Performance Implications

**Latency by Model Type:**
- Fast: z-image/base (~1-2s)
- Medium: Flux Dev (~5-10s)
- Slow: Flux Pro (~15-30s), Kling Video (~30-60s)

**Optimization Strategies:**
- Session context caching (avoid re-parsing previous results)
- Response pattern learning (reduce retry attempts)
- Async API calls for batch operations
- Cost-aware model selection (prefer z-image/base for simple tasks)

### Cost Management

**Tier-Based Pricing:**
- Budget: z-image/base (~$0.01/call)
- Standard: Flux Dev (~$0.05/call)
- Premium: Flux Pro (~$0.25/call)
- Video: Kling (~$1-5/call depending on duration)

**Cost Controls:**
- Display estimated cost for premium operations
- Default to cost-effective models unless quality specified
- Track usage in session (optional user setting)

### Dynamic Model Discovery

**API Endpoint**: `GET https://api.fal.ai/v1/models`

**Implementation Strategy**:

1. **Discovery Module** (`lib/discovery.py`):
```python
def discover_models(
    category: Optional[str] = None,
    status: str = "active",
    limit: int = 100,
    force_refresh: bool = False
) -> List[ModelInfo]:
    """
    Discover models from fal.ai API with intelligent caching.

    Args:
        category: Filter by category (e.g., 'text-to-image')
        status: Filter by status ('active' or 'deprecated')
        limit: Max models per page
        force_refresh: Bypass cache

    Returns:
        List of ModelInfo objects with metadata
    """
    # Check cache first (24-hour TTL)
    if not force_refresh and cache_valid():
        return load_from_cache(category, status)

    # Fetch from API with pagination
    models = []
    cursor = None

    while True:
        response = api_client.get(
            "/v1/models",
            params={
                "category": category,
                "status": status,
                "limit": limit,
                "cursor": cursor
            }
        )

        models.extend(response["models"])

        if not response["has_more"]:
            break

        cursor = response["next_cursor"]

    # Cache results
    save_to_cache(models, category, status)

    return models
```

2. **Cache Strategy**:
   - **Location**: `~/.config/fal-skill/cache/`
   - **Files**:
     - `all_models.json`: Complete model list (refreshed daily)
     - `by_category/{category}.json`: Category-specific caches
     - `metadata.json`: Cache metadata (timestamps, versions)
   - **TTL**: 24 hours (configurable)
   - **Invalidation**: Manual refresh via `/fal-update-model --refresh`

3. **Curated Registry** (`models/curated.yaml`):
```yaml
# Human-curated subset of tested, recommended models
# Used as fallback when API unavailable

version: "1.0"
last_updated: "2026-01-28"

categories:
  text-to-image:
    - endpoint_id: fal-ai/flux/dev
      display_name: FLUX.1 [dev]
      cost_tier: standard
      speed_tier: medium
      quality_tier: high
      recommended: true
      tested: true

    - endpoint_id: z-image/base
      display_name: z-image base
      cost_tier: budget
      speed_tier: fast
      quality_tier: medium
      recommended: true
      tested: true

  background-removal:
    - endpoint_id: fal-ai/birefnet/v2
      display_name: Birefnet v2
      cost_tier: budget
      speed_tier: fast
      quality_tier: high
      recommended: true
      tested: true
```

4. **Model Selection Logic**:
   - **First**: Check curated registry for task
   - **Then**: Query discovered models by category
   - **Filter**: By cost tier, speed, quality based on user intent
   - **Rank**: By recommendation score, test status, popularity

5. **API Response Handling**:
```python
# Example API response structure
{
  "models": [
    {
      "endpoint_id": "fal-ai/flux/dev",
      "metadata": {
        "display_name": "FLUX.1 [dev]",
        "category": "text-to-image",
        "description": "Fast text-to-image generation",
        "status": "active",
        "tags": ["fast", "pro"],
        "updated_at": "2025-01-15T12:00:00Z",
        "thumbnail_url": "https://fal.media/files/example.jpg",
        "model_url": "https://fal.run/fal-ai/flux/dev"
      }
    }
  ],
  "next_cursor": "Mg==",
  "has_more": true
}
```

6. **Error Handling**:
   - **API Unavailable**: Fallback to curated models
   - **Rate Limited**: Use cached results, show warning
   - **Invalid Response**: Log error, use last known good cache
   - **Empty Results**: Check curated registry, warn user

7. **Refresh Strategy**:
   - **Automatic**: Daily background refresh (if skill used)
   - **Manual**: `/fal-update-model --refresh` command
   - **Startup**: Quick cache check (<100ms), async refresh if expired
   - **Fallback**: Always maintain curated list for offline use

**Benefits**:
- ✅ Always up-to-date with latest models
- ✅ No manual JSON file updates needed
- ✅ Intelligent caching reduces API calls
- ✅ Category filtering improves intent detection
- ✅ Curated fallback ensures reliability
- ✅ Metadata enables smart model selection

**Trade-offs**:
- Requires internet for initial discovery
- API rate limits (mitigated by caching)
- Slight startup overhead first time (cached after)

## Acceptance Criteria

### Functional Requirements

- [ ] `/fal-generate` correctly detects intent for image/video/edit tasks with ≥85% accuracy
- [ ] All specialized skills (`/fal-generate-image`, etc.) execute successfully with valid API keys
- [ ] Response Adapter successfully extracts results from at least 5 different fal.ai models
- [ ] Self-learning system persists discovered response paths to registry after 3 successes
- [ ] `/fal-setup` validates API key and guides user through initial configuration
- [ ] Intent detection confidence thresholds work: auto-execute (≥0.8), show reasoning (≥0.6), clarify (<0.6)
- [ ] Session context tracking resolves pronouns ("make it blue" understands last_result)
- [ ] Prompt engineering templates optimize prompts for model-specific formats
- [ ] Dynamic model discovery fetches 1,000+ models from fal.ai API
- [ ] Model discovery caching works with 24-hour TTL
- [ ] Curated fallback registry loads when API unavailable
- [ ] `/fal-update-model --refresh` manually refreshes model cache
- [ ] Model selection prioritizes curated recommended models
- [ ] Category filtering narrows model discovery to relevant categories

### Non-Functional Requirements

- [ ] Average time to result: <30 seconds for image generation
- [ ] First-attempt success rate: >85% for common tasks
- [ ] New model addition time: <30 minutes (no code changes required)
- [ ] Documentation clarity: No setup guide needed for basic use
- [ ] Error messages are actionable (explain what went wrong and how to fix)

### Quality Gates

- [ ] Test coverage: Core Python modules have unit tests
- [ ] Integration tests: Each model in registry tested with real API call
- [ ] Documentation: SKILL.md examples cover all major use cases
- [ ] Code review: Python code follows PEP 8 style guidelines

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal**: Setup infrastructure and configuration system

1. **Directory Structure**
   - Create base fal-skill directory structure
   - Setup Python virtual environment (optional)
   - Initialize model registry YAML with 3 starter models

2. **`/fal-setup` Skill**
   - Implement API key prompt and validation
   - Create config directory: `~/.config/fal-skill/`
   - Test API key with simple fal.ai call
   - Write SKILL.md for configuration workflow

3. **Python API Client Foundation**
   - `scripts/fal_api.py`: CLI entry point
   - `lib/api_client.py`: HTTP wrapper for fal.ai API (generation + discovery)
   - `lib/models.py`: Registry loader (dynamic + curated)
   - `lib/discovery.py`: fal.ai model list API integration
   - Test with one model (z-image/base)

4. **Dynamic Model Discovery** (`lib/discovery.py`)
   - Implement fal.ai `/v1/models` API integration
   - Pagination support (`limit`, `cursor` parameters)
   - Category filtering (`category` parameter)
   - Status filtering (`status=active`)
   - 24-hour cache with expiry (reduce API calls)
   - Fallback to curated models on API failure

**Files Created:**
```
skills/fal-setup/SKILL.md
scripts/fal_api.py
scripts/lib/api_client.py
scripts/lib/models.py
scripts/lib/discovery.py
models/curated.yaml
models/cache/ (directory for cached API responses)
config/response_patterns.yaml (empty template)
```

**Deliverables:**
- Working `/fal-setup` skill
- API calls successfully reaching fal.ai (generation + discovery)
- Dynamic model discovery with caching
- Curated model registry (5 core models)
- Fallback mechanism for API failures

**Success Criteria:**
- User can run `/fal-setup` and validate their API key
- Python script can discover models via fal.ai API
- Model discovery fetches 1,000+ models with pagination
- Cache persists and expires after 24 hours
- Curated models load when API unavailable
- Configuration stored securely in ~/.config/

---

### Phase 2: Core Generation Skills (Week 2)

**Goal**: Implement specialized skills with adaptive response parsing

1. **Response Adapter (`lib/adapter.py`)**
   - Implement 15+ common field path patterns
   - Add user prompt fallback when patterns fail
   - Implement learning mechanism with success/fail tracking
   - Persist learned paths to `config/response_patterns.yaml`

2. **`/fal-generate-image` Skill**
   - SKILL.md with workflow and examples
   - Model selection logic (flux-pro vs flux-dev vs z-image/base)
   - Parameter handling (prompt, negative_prompt, size, guidance_scale)
   - Integration with Response Adapter

3. **`/fal-remove-bg` Skill**
   - Single-purpose background removal
   - Simple workflow (input image → output image with transparent bg)
   - Test with birefnet model

4. **Model Registry Expansion**
   - Add 5-7 core models to registry:
     - fal-ai/flux-pro (premium image)
     - fal-ai/flux-dev (standard image)
     - z-image/base (budget image)
     - birefnet (background removal)
     - kling-v1 (video generation)

**Files Created:**
```
scripts/lib/adapter.py
skills/fal-generate-image/SKILL.md
skills/fal-remove-bg/SKILL.md
```

**Deliverables:**
- Working `/fal-generate-image` with model selection
- Working `/fal-remove-bg` with single-purpose focus
- Response Adapter extracting results from all registry models
- Self-learning persisting successful paths

**Success Criteria:**
- Image generation works with 3 different models
- Response Adapter learns and caches successful paths
- Background removal produces transparent PNG output
- Cost-aware model selection (defaults to z-image/base for simple prompts)

---

### Phase 3: Intelligence Layer (Week 3)

**Goal**: Add intent detection and orchestration to main skill

1. **Intent Detection (`lib/intent.py`)**
   - Stage 1: Explicit command keywords ("generate image", "make video")
   - Stage 2: Context analysis (attachments, pronouns, previous results)
   - Stage 3: Keyword scoring with relevance weighting
   - Confidence calculation and threshold enforcement

2. **Session Context Tracking**
   - Store last 5 operations in memory
   - Enable pronoun resolution ("it", "this", "that")
   - Track last_result for reference in follow-up commands

3. **`/fal-generate` Orchestrator Skill**
   - Main SKILL.md with routing logic
   - Integration with Intent Detection
   - Routing to appropriate specialized skill
   - User confirmation for medium confidence (0.6-0.8)

4. **Prompt Engineering Layer**
   - Model-specific template application from registry
   - Negative prompt injection where supported
   - Parameter optimization per model

**Files Created:**
```
scripts/lib/intent.py
scripts/lib/context.py
skills/fal-generate/SKILL.md
```

**Deliverables:**
- Working `/fal-generate` with intelligent routing
- Intent detection with ≥85% accuracy on test cases
- Session context enabling conversational follow-ups
- Prompt engineering templates applied per model

**Success Criteria:**
- `/fal-generate "cat wizard"` auto-routes to image generation
- `/fal-generate "remove background"` (with attachment) routes to bg removal
- Confidence-based user confirmation works correctly
- Prompts are optimized per model (e.g., "detailed" added for Flux Pro)

---

### Phase 4: Video, Audio & Advanced Editing (Week 4-5)

**Goal**: Add video generation, audio capabilities, avatars, and advanced image editing

1. **`/fal-generate-video` Skill**
   - Text-to-video with Kling models (103 text-to-video models)
   - Image-to-video (152 models including Kling O1, 1.5-2.6 series)
   - Duration parameter handling (gotcha: number not string)
   - Tier selection (Pro/Standard/Master)
   - Async option for long generations
   - Cost warning for expensive operations

2. **`/fal-edit-photo` Skill - Fibo Edit Suite Integration**
   - **Basic operations**: Inpainting, outpainting, image-to-image
   - **Fibo Edit specialized operations** (10+ models):
     - add_object_by_text / erase_by_text / replace_object_by_text
     - colorize, relight, reseason (seasonal changes)
     - blend, restore, restyle
   - Mask handling for targeted edits
   - Intent-based operation selection

3. **`/fal-generate-audio` Skill (TTS)**
   - Text-to-speech with 40 models
   - Model selection: ElevenLabs (turbo-v2.5, eleven-v3, multilingual-v2), Chatterbox, Kokoro
   - Multi-language support (Kokoro: 9+ languages)
   - Voice parameter control (speed, pitch where supported)

4. **`/fal-generate-music` Skill**
   - Music generation with Beatoven, CassetteAI
   - Sound effects generation
   - Genre/mood/duration parameters

5. **`/fal-avatar` Skill (Lipsync Avatars)**
   - Audio-to-video avatars (Argil, Kling AI Avatar)
   - Text-to-video avatars
   - Live Portrait animation
   - Multi-face avatar support

6. **`/fal-face` Skill**
   - Face swapping (image & video)
   - Face-to-sticker conversion
   - Headshot generator, portrait enhancement
   - Face-to-full-portrait generation

7. **`/fal-upscale` Skill**
   - Image upscaling (Crystal, Clarity, Creative, ESRGAN)
   - Video upscaling (Crystal Video, Bytedance)
   - Quality tier selection

8. **Model Registry Expansion**
   - Add video models: Kling (23 variants), Seedance, Animatediff
   - Add editing models: Fibo Edit suite (10+ operations)
   - Add TTS models: ElevenLabs, Kokoro (multi-lang), Chatterbox
   - Add music: Beatoven, CassetteAI
   - Add avatar: Argil, Kling AI Avatar v2, Live Portrait
   - Add face: face swap, enhancement, portrait generators
   - Add upscaling: Crystal, Clarity, ESRGAN
   - Add metadata for duration/cost warnings per category

9. **Workflow Documentation**
   - Document common pipelines:
     - Multi-angle product video (Qwen → Multiple Angles → Kling)
     - Audio-to-video avatars (Audio → Kling AI Avatar)
     - Extended video (Video chaining with last frame)
     - Music video creation (Music gen → Avatar → Video)
     - Face-enhanced portraits (Face → Full Portrait → Upscale)

**Files Created:**
```
skills/fal-generate-video/SKILL.md
skills/fal-edit-photo/SKILL.md
skills/fal-generate-audio/SKILL.md
skills/fal-generate-music/SKILL.md
skills/fal-avatar/SKILL.md
skills/fal-face/SKILL.md
skills/fal-upscale/SKILL.md
docs/workflows.md
docs/fibo-edit-guide.md
```

**Deliverables:**
- Working video generation with Kling series (multiple versions)
- Advanced image editing with Fibo Edit suite (10+ operations)
- Text-to-speech with multi-language support (40 models)
- Music and sound effect generation
- Avatar/lipsync video creation
- Face operations (swap, enhance, portrait)
- Image/video upscaling
- Documented workflows for common pipelines
- Cost warnings for premium operations

**Success Criteria:**
- Video generation produces MP4 output with Kling models
- Fibo Edit operations work (colorize, relight, reseason, etc.)
- TTS generates audio files in multiple languages
- Music generation produces quality audio
- Avatar lipsync correctly matches audio input
- Face swap works for both images and videos
- Upscaling improves image/video quality
- Users receive cost estimate for expensive operations
- Workflow documentation includes working examples for all categories

---

### Phase 5: Polish & Documentation (Week 6)

**Goal**: Testing, optimization, and comprehensive documentation

1. **Testing**
   - Unit tests for intent detection logic
   - Integration tests for each model in registry
   - End-to-end workflow tests
   - Error handling validation

2. **Error Handling Improvements**
   - Graceful API timeout handling
   - Clear error messages with actionable guidance
   - Retry logic for transient failures
   - Fallback to cheaper models on rate limit errors

3. **Documentation**
   - README.md with quick start guide
   - ARCHITECTURE.md explaining design decisions
   - CONTRIBUTING.md for adding new models
   - Troubleshooting guide for common issues

4. **Performance Optimization**
   - Cache successful response patterns
   - Optimize YAML loading (lazy load)
   - Reduce Python startup overhead
   - Profile and optimize slow code paths

**Files Created:**
```
README.md
ARCHITECTURE.md
CONTRIBUTING.md
TROUBLESHOOTING.md
tests/test_intent.py
tests/test_adapter.py
tests/integration/test_models.py
```

**Deliverables:**
- Comprehensive test suite with >80% coverage
- Complete documentation for users and contributors
- Optimized performance (startup time <1s)
- Production-ready error handling

**Success Criteria:**
- All tests pass
- Documentation enables new users to get started without assistance
- Error messages guide users to solutions
- Performance meets non-functional requirements

## Success Metrics

**User Experience Metrics:**
- Time from installation to first successful generation: <5 minutes
- Intent detection accuracy: ≥85% on diverse prompts
- First-attempt success rate: >85% for common tasks
- User satisfaction: Positive feedback on ease of use

**Technical Metrics:**
- Average latency: <30s for image, <60s for video
- Response Adapter learning rate: 3 successes or 5 attempts with >80% accuracy
- Model addition time: <30 minutes (measure time to add new model to registry)
- Code coverage: >80% for core Python modules

**Adoption Metrics:**
- Number of active users
- Number of API calls per user per day
- Most popular models (track usage frequency)
- Workflow adoption (track which pipelines are commonly used)

## Dependencies & Risks

### Dependencies

**External:**
- fal.ai API availability and stability
- Python 3.8+ (should be available on most systems)
- Internet connection for API calls

**Internal:**
- Claude Code skill loading mechanism
- Bash tool for command execution
- Read/Write tools for configuration

### Prerequisites

- User must have fal.ai account and API key
- User must have Claude Code installed
- Network access to fal.ai API endpoint

### Risk Analysis & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **fal.ai API changes break integration** | High | Medium | Version API calls, monitor changelog, implement adapter pattern for flexibility |
| **Response format variations cause failures** | High | High | Self-learning Response Adapter, extensive testing, graceful fallback to user prompt |
| **API costs exceed user expectations** | Medium | Medium | Display cost estimates, default to budget models, track usage |
| **Intent detection accuracy too low** | Medium | Medium | Multi-stage detection, confidence thresholds, user feedback loop |
| **Python dependencies cause setup friction** | Low | Low | Use stdlib only (no external deps), provide clear error messages |
| **API rate limiting blocks users** | Medium | Low | Implement retry with backoff, cache results, show clear error messages |

## Alternative Approaches Considered

### 1. Monolithic Single Skill
**Pros**: Simpler structure, one SKILL.md file
**Cons**: Complex logic in one file, harder to maintain, less flexibility
**Decision**: Rejected - Layered approach provides better separation of concerns

### 2. Hardcoded Response Parsing
**Pros**: Faster initial implementation, no learning system needed
**Cons**: Breaks when API changes, requires code updates for new models
**Decision**: Rejected - Adaptive approach more maintainable long-term

### 3. JavaScript/TypeScript Implementation
**Pros**: Better async handling, more familiar to some developers
**Cons**: Additional dependency, Claude Code ecosystem uses Python for complex skills
**Decision**: Rejected - Python aligns with existing skill patterns (see last30days)

### 4. No Intent Detection (Explicit Commands Only)
**Pros**: Simpler implementation, no confidence scoring needed
**Cons**: Poor UX, users must learn multiple commands
**Decision**: Rejected - Intelligence layer provides significant UX improvement

## Future Considerations

### Extensibility

**Model Marketplace:**
- Support user-contributed model definitions
- Community registry of models and prompts
- Sharing successful prompt templates

**Advanced Workflows:**
- Multi-step pipelines with automatic chaining
- Batch processing support
- Template library for common patterns

**Integration Enhancements:**
- Export to project files (save generations)
- History tracking and regeneration
- Favorites/bookmarks for successful prompts

### Long-Term Vision

**Year 1**: Core functionality stable, 20+ models in registry, 100+ active users
**Year 2**: Community contributions, workflow automation, integration with other skills
**Year 3**: Advanced features (batch processing, workflow studio), enterprise support

## References & Research

### Internal References

**Architecture Documentation:**
- `/Users/cheng/InfQuest/InfProj/fal-skill/brainstorm/ARCHITECTURE-SUMMARY.md` - Quick reference design
- `/Users/cheng/InfQuest/InfProj/fal-skill/brainstorm/2026-01-28-fal-skill-architecture-brainstorm.md` - Full architectural decisions (1400+ lines)

**Best Practices:**
- `/Users/cheng/InfQuest/InfProj/fal-skill/brainstorm/02-fal-ai-best-practices.md` - Platform usage patterns, gotchas
- `/Users/cheng/InfQuest/InfProj/fal-skill/brainstorm/01-fal-ai-overview.md` - Platform capabilities overview

**Reference Skills:**
- `/Users/cheng/.agents/skills/last30days/SKILL.md` - Complex API integration pattern
- `/Users/cheng/.agents/skills/last30days/scripts/last30days.py` - Python script structure example
- `/Users/cheng/.config/opencode/skills/better-icons/SKILL.md` - CLI wrapper pattern
- `/Users/cheng/.config/opencode/skills/here-be-git/SKILL.md` - Simple workflow example

### External References

**fal.ai Platform:**
- Official API Documentation: https://fal.ai/docs
- Model Gallery: https://fal.ai/models
- Playground: https://fal.ai/playground (for testing before automation)

**Best Practices:**
- Test in Playground first before writing code
- Copy working examples from Playground auto-generated code
- Verify parameter types (docs sometimes incorrect - e.g., duration is number not string)

### Related Work

**Existing Integrations:**
- Multiple Angles 2511 → Kling Video pipeline (fashion e-commerce use case)
- Hunyuan 3D → WebGL pipeline (3D creative projects)
- LTX-2 Audio-to-Video (music video generation)

**Similar Projects:**
- ComfyUI workflows (more complex, requires setup)
- Replicate API integrations (different platform, similar orchestration needs)

## MVP Scope

For initial release (Weeks 1-3), include:

### Core Skills
1. `/fal-setup` - Configuration and API key management
2. `/fal-generate-image` - Image generation with 3 models (flux-pro, flux-dev, z-image/base)
3. `/fal-remove-bg` - Background removal (single-purpose)
4. `/fal-generate` - Orchestrator with basic intent detection

### Core Components
- Response Adapter with self-learning
- Model registry with 5 core models
- Intent detection with confidence scoring
- Session context tracking (last 5 operations)

### Documentation
- README with quick start
- SKILL.md for each skill with examples
- Troubleshooting guide for common issues

### Defer to Later
- Video generation (`/fal-generate-video`) - Week 4-5
- Advanced image editing (`/fal-edit-photo` with Fibo Edit suite) - Week 4-5
- Audio generation (`/fal-generate-audio`, `/fal-generate-music`) - Week 4-5
- Avatar/lipsync (`/fal-avatar`) - Week 4-5
- Face operations (`/fal-face`) - Week 4-5
- Upscaling (`/fal-upscale`) - Week 4-5
- Advanced workflows and pipelines - Week 4-5
- Comprehensive test suite - Week 6
- Performance optimization - Week 6

## Example Usage

### Basic Image Generation
```
User: /fal-generate "a wizard cat wearing purple robes"

Claude: Generating image with Flux Dev...
[Image result displayed]

Generated: https://fal.ai/files/...
Model: fal-ai/flux-dev
Cost: ~$0.05
```

### Intent Detection - Background Removal
```
User: /fal-generate "remove the background" [uploads image]

Claude: Detected intent: REMOVE_BACKGROUND (confidence: 0.92)
Processing with birefnet model...
[Image with transparent background displayed]
```

### Model Selection with Cost Awareness
```
User: /fal-generate "quick sketch of a dog"

Claude: Using z-image/base (budget model) for simple request.
[Image result displayed]
Cost: ~$0.01

Want higher quality? Try: /fal-generate-image "quick sketch of a dog" --model flux-pro
```

### Session Context - Follow-up Command
```
User: /fal-generate "sunset over mountains"
Claude: [Generates image]

User: /fal-generate "make it more purple"
Claude: Detected context: Editing previous result (confidence: 0.85)
Applying color adjustment...
[Modified image displayed]
```

### Configuration Setup
```
User: /fal-setup

Claude: Let me help you configure fal.ai integration.

Step 1: Get your API key
Visit: https://fal.ai/dashboard/keys
Create a new API key and paste it here.

[User pastes key]

Validating... ✓ Valid API key

Configuration saved to ~/.config/fal-skill/.env

Ready to generate! Try: /fal-generate "your prompt here"
```

### Text-to-Speech (Multi-Language)
```
User: /fal-generate-audio "Hello, welcome to our service. Thank you for choosing us."

Claude: Generating speech with ElevenLabs turbo-v2.5...
[Audio file created]

Generated: audio_output.mp3
Model: fal-ai/elevenlabs/tts/turbo-v2.5
Duration: 6 seconds

Language options available: Try /fal-generate-audio --language french for French output
```

### Video Generation from Image
```
User: /fal-generate-video [uploads product image]

Claude: Creating video with Kling 2.6...
Duration: 5 seconds (default)
[Processing video - estimated 30s]

Generated: https://fal.ai/files/video_xyz.mp4
Model: fal-ai/kling-video/v2.6/pro/image-to-video
Cost: ~$2.50
```

### Avatar with Lipsync
```
User: /fal-avatar [uploads face photo and audio file]

Claude: Creating lipsync avatar with Kling AI Avatar v2...
[Processing - matching lip movements to audio]

Generated: https://fal.ai/files/avatar_video.mp4
Model: fal-ai/kling-video/ai-avatar/v2/pro
Duration: Based on audio length (15 seconds)
Cost: ~$3.00
```

### Advanced Image Edit - Fibo Relight
```
User: /fal-edit-photo "relight this image" [uploads photo]

Claude: Detected intent: RELIGHT (confidence: 0.89)
Processing with Fibo Edit relight model...
[Image with improved lighting displayed]

Generated: https://fal.ai/files/relit_image.png
Model: bria/fibo-edit/relight
Other Fibo Edit options: colorize, reseason, restyle, restore
```

### Music Generation
```
User: /fal-generate-music "upbeat electronic music, 30 seconds, happy mood"

Claude: Generating music with Beatoven...
[Processing music generation]

Generated: music_output.mp3
Model: beatoven/music-generation
Duration: 30 seconds
Genre: Electronic, Mood: Happy
```

### Face Swap
```
User: /fal-face swap [uploads source face and target image]

Claude: Swapping faces...
[Processing face swap with AI Face Swap model]

Generated: https://fal.ai/files/face_swapped.png
Model: half-moon-ai/ai-face-swap/faceswapimage
Note: Video face swap also available with /fal-face swap-video
```

---

## Enhanced Research Findings (2026-01-28)

### Model Catalog Discovery

**Source**: `/Users/cheng/InfQuest/InfProj/remotion-copy/src/api/fal-models.json`
**Last Updated**: 2026-01-27
**Total Models Discovered**: 1,109 across 16 categories

### Notable Model Series

**Kling Video Ecosystem (23 variants)**:
- Versions: O1, 1.5, 1.6, 2.0, 2.1, 2.5-turbo, 2.6
- Tiers: Pro, Standard, Master
- Capabilities: Text-to-video, image-to-video, AI avatars, elements support
- Most recent: `fal-ai/kling-video/v2.6/pro/image-to-video`

**Flux Model Family (150+ models)**:
- Core: flux-pro, flux-dev (standard generation)
- Budget: z-image/base (~$0.01/call)
- LoRA variants: portrait, kontext, krea trainers
- Editing: Multiple specialized editors

**Fibo Edit Suite (10+ specialized operations)**:
1. `bria/fibo-edit/add_object_by_text` - Add objects to images
2. `bria/fibo-edit/erase_by_text` - Remove objects
3. `bria/fibo-edit/replace_object_by_text` - Swap objects
4. `bria/fibo-edit/colorize` - Add/change colors
5. `bria/fibo-edit/relight` - Adjust lighting
6. `bria/fibo-edit/reseason` - Change seasons (summer→winter, etc.)
7. `bria/fibo-edit/blend` - Blend images
8. `bria/fibo-edit/restore` - Restore/enhance quality
9. `bria/fibo-edit/restyle` - Apply artistic styles
10. `bria/fibo-edit/edit` - General editing

**ElevenLabs TTS Family**:
- `fal-ai/elevenlabs/tts/turbo-v2.5` - Fastest, production-ready
- `fal-ai/elevenlabs/tts/eleven-v3` - Latest quality model
- `fal-ai/elevenlabs/tts/multilingual-v2` - Multi-language support

**Kokoro TTS (9 language variants)**:
- American English, British English
- Brazilian Portuguese, French, Hindi, Italian
- Japanese, Korean, Mandarin Chinese

### Key Capabilities by Priority

**High Priority (MVP + Phase 4)**:
1. Image Generation (150 models) - Core feature
2. Background Removal (36 models) - High demand
3. Text-to-Speech (40 models) - Audio content
4. Video Generation (103 text + 152 image-to-video) - Video content
5. Image Editing (349 models, esp. Fibo Edit) - Advanced editing

**Medium Priority (Phase 4-5)**:
6. Music Generation (62 models) - Creative audio
7. Avatar/Lipsync (29 models) - Interactive content
8. Face Operations (17 models) - Portrait work
9. Upscaling (19 models) - Quality enhancement
10. Speech Recognition (12 ASR models) - Transcription

**Out of Scope (Initial Release)**:
- 3D Generation (35 models) - Complexity + niche use case
- Model Training (34 models) - Advanced users only, requires separate workflow

### Technical Insights

**Cost Tiers Identified**:
- Budget: z-image/base (~$0.01), birefnet (~$0.02)
- Standard: Flux Dev (~$0.05), most editing (~$0.03-0.10)
- Premium: Flux Pro (~$0.25), Kling Pro video (~$2-5)
- Enterprise: Training models (~$10-50)

**Response Format Patterns by Category**:
- Image models: `images[0].url` or `data.images[0]` or `output.url`
- Video models: `video.url` or `data.video` or `result.video_url`
- Audio models: `audio_url` or `output.url` or `data.audio`
- Variation requires adaptive Response Adapter

**Model Versioning Patterns**:
- Most models have `v1`, `v1.5`, `v2` variants
- Some have tier variants: `pro`, `standard`, `lite`, `fast`
- Kling has most extensive versioning (O1, 1.5, 1.6, 2.0, 2.1, 2.5-turbo, 2.6)

### Implementation Priorities

**Week 1-3 (MVP)**:
- Image generation (3 models: flux-pro, flux-dev, z-image/base)
- Background removal (birefnet)
- Basic orchestration

**Week 4-5 (Expanded)**:
- Video generation (Kling series)
- Fibo Edit suite integration (10 operations)
- TTS (ElevenLabs + Kokoro multi-lang)
- Music generation (Beatoven, CassetteAI)
- Avatar lipsync (Kling AI Avatar, Argil)
- Face operations (swap, enhance)
- Upscaling (Crystal, Clarity)

**Week 6 (Polish)**:
- Testing all 12 categories
- Documentation
- Performance optimization

### References

**Model Catalog**:
- Full catalog: `/Users/cheng/InfQuest/InfProj/remotion-copy/src/api/fal-models.json` (1,109 models)
- Category breakdown: 16 categories (12 in scope)
- Last updated: 2026-01-27

**Key Model IDs to Test First**:
```yaml
image_generation:
  - fal-ai/flux-dev  # Standard quality
  - z-image/base     # Budget option

video_generation:
  - fal-ai/kling-video/v2.6/pro/image-to-video  # Latest Kling

text_to_speech:
  - fal-ai/elevenlabs/tts/turbo-v2.5  # Fast TTS
  - fal-ai/kokoro/american-english    # Free alternative

editing:
  - bria/fibo-edit/relight            # Lighting adjustment
  - bria/fibo-edit/colorize           # Color manipulation

background_removal:
  - fal-ai/birefnet/v2                # Latest version

avatar:
  - fal-ai/kling-video/ai-avatar/v2/pro  # Latest avatar

face:
  - half-moon-ai/ai-face-swap/faceswapimage  # Face swapping

upscale:
  - clarityai/crystal-upscaler        # High quality
```

---

**Plan Status**: Ready for implementation (Enhanced with 1,109 model catalog)
**Estimated Effort**: 6 weeks (full-time) or 10-12 weeks (part-time)
**Scope**: 12 categories (excluding 3D and training), 1,000+ models
**Next Step**: Review plan → Run `/deepen-plan` for enhanced research → Start `/workflows:work`