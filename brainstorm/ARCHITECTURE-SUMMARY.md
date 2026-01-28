# fal-skill Architecture Summary

**Quick reference for the fal.ai skill system design.**

---

## System Overview

```
User Command
     ↓
┌────────────────────────┐
│  /fal-generate         │ ← Smart orchestrator (intent detection)
├────────────────────────┤
│  Specialized Skills    │ ← /fal-generate-image, /fal-generate-video
├────────────────────────┤
│  Prompt Engineering    │ ← Model-specific optimization
├────────────────────────┤
│  fal.ai API            │ ← HTTP request
├────────────────────────┤
│  Response Adapter      │ ← Field extraction + learning
└────────────────────────┘
     ↓
   Result
```

---

## Core Components

### 1. Intent Detection (Multi-Stage)

**Stages:**
1. **Explicit commands** - "remove background" → REMOVE_BG
2. **Context analysis** - Attachments, previous results, pronouns
3. **Keyword scoring** - Weight words by relevance
4. **Decision** - Combine signals with confidence score

**Context Awareness:**
- Tracks last 5 operations in conversation
- Understands "it", "this", "that" references
- Uses previous result as implicit input when appropriate

**Confidence Thresholds:**
- High (≥0.8): Execute immediately
- Medium (≥0.6): Show reasoning and execute
- Low (<0.6): Ask user for clarification

### 2. Response Adapter (Self-Learning)

**Extraction Strategy:**
1. Try primary_path from model registry (if known)
2. Try 15+ common field patterns
3. Find all URL-like values and show to user
4. Let user select or specify path

**Learning Mechanism:**
- Track success/fail per model per field path
- Persist to registry after 3 successes OR 5 attempts with >80% success
- Session memory: immediate use of discovered paths
- Prevents false positives from one-off API quirks

**Example:**
```yaml
# After learning
response_format:
  primary_path: data.output_images[0].content
  confidence: high
  auto_learned: true
  success_count: 5
  fail_count: 0
```

### 3. Model Registry

**Structure:**
```yaml
model_id: fal-ai/flux-pro
metadata:
  category: image-generation
  cost_tier: premium
  speed_tier: slow
  quality_tier: highest
api_format:
  endpoint: /fal-ai/flux-pro
  request_fields: [...]
  response_format:
    primary_path: images[0].url
    confidence: high
prompt_engineering:
  template: "{prompt}, highly detailed"
  negative_prompt: "blurry"
use_cases: [...]
```

### 4. Skill Hierarchy

| Skill | Purpose | Intelligence |
|-------|---------|--------------|
| `/fal-generate` | Universal entry | **High** - intent detection |
| `/fal-generate-image` | Image generation | **Medium** - model selection |
| `/fal-generate-video` | Video generation | **Medium** - video routing |
| `/fal-edit-photo` | Image editing | **Medium** - edit models |
| `/fal-remove-bg` | Background removal | **Low** - single purpose |
| `/fal-setup` | Configuration | **Low** - setup wizard |

---

## Key Decisions Made

### Intent Detection
- ✅ Smart context analysis (not just keywords)
- ✅ Session-aware (track last 5 operations)
- ✅ Confidence-based execution or clarification

### Response Adapter
- ✅ Hybrid auto-try + user confirmation
- ✅ Confidence-based persistence (3 successes)
- ✅ Session memory for immediate reuse

### Architecture
- ✅ Layered skills (not monolithic)
- ✅ Explicit commands for power users
- ✅ Model registry with learning capability

---

## Example User Flows

### Flow 1: First-Time User
```
User: /fal-generate "a cat"
→ Intent: GENERATE_IMAGE (0.6 confidence)
→ Model: flux-dev (default)
→ API call
→ Extract: images[0].url
→ Show result
```

### Flow 2: Conversational Edit
```
User: /fal-generate "a cat"
[Image generated]

User: "make it blue"
→ Intent: EDIT_IMAGE (0.75 confidence)
→ Source: last_result (from session)
→ Model: flux-dev-inpainting
→ Show edited image
```

### Flow 3: New Model Learning
```
User: /fal-generate-image --model new-model "test"
→ API response: {data: {outputs: [{url: "..."}]}}
→ Try common patterns: all fail
→ Show user: Found 1 URL at data.outputs[0].url
→ User: 1 (confirm)
→ Track: 1 success

[After 2 more uses]
→ Threshold met (3 successes)
→ Update registry: primary_path = data.outputs[0].url
→ Notify: ✅ Learned response format
```

---

## File Structure

```
~/.claude-code/skills/fal-skill/
├── SKILL.md                    # /fal-generate
├── skills/
│   ├── generate-image/SKILL.md
│   ├── generate-video/SKILL.md
│   ├── edit-photo/SKILL.md
│   ├── remove-bg/SKILL.md
│   ├── setup/SKILL.md
│   └── update-model/SKILL.md
├── models/
│   ├── image-models.yaml
│   ├── video-models.yaml
│   └── editing-models.yaml
├── prompts/
│   └── templates.yaml
└── docs/
    ├── architecture.md
    └── model-guide.md
```

---

## Implementation Phases

### Phase 1: Core (4-6 hours)
- [ ] Directory structure
- [ ] `/fal-setup` for configuration
- [ ] Model registry with 3 core models
- [ ] Response adapter utilities

### Phase 2: Basic Skills (6-8 hours)
- [ ] `/fal-generate-image`
- [ ] `/fal-generate-video`
- [ ] `/fal-remove-bg`

### Phase 3: Orchestration (4-6 hours)
- [ ] `/fal-generate` with intent detection
- [ ] Prompt engineering integration
- [ ] Session context tracking

### Phase 4: Advanced (8-10 hours)
- [ ] `/fal-edit-photo`
- [ ] Response adapter learning
- [ ] User preference system

---

## Success Criteria

1. **Beginner-friendly** - Works with just `/fal-generate "prompt"`
2. **Expert-accessible** - Full control when needed
3. **Self-healing** - Adapts to API changes
4. **Learnable** - Improves from usage
5. **Maintainable** - <30min to add new model

**Target Metrics:**
- Time to result: <30s
- First-attempt success: >85%
- New model setup: <30min
- User satisfaction: No docs needed for basic use

---

## Related Documents

- `2026-01-28-fal-skill-architecture-brainstorm.md` - Full design
- `2026-01-28-fal-ai-best-practices-brainstorm.md` - Reference docs
- `brainstorm/01-fal-ai-overview.md` - Platform overview
- `brainstorm/02-fal-ai-best-practices.md` - Usage patterns
