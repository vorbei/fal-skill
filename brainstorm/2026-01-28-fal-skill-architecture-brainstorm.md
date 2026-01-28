# fal.ai Skills Architecture - Brainstorm Document

**Date:** 2026-01-28
**Status:** Brainstorming
**Type:** System Architecture

---

## What We're Building

A **multi-tiered fal.ai skill system** for Claude Code that provides:

1. **Smart orchestration** - `/fal-generate` detects user intent and selects best model/approach
2. **Specialized commands** - Task-specific skills like `/fal-generate-video`, `/fal-remove-bg`, `/fal-edit-photo`
3. **Adaptive API handling** - Response parsing that adjusts to different fal.ai model API formats
4. **Prompt engineering layer** - Automatic prompt rewriting for optimal model results
5. **Configuration management** - Setup and model preference tracking

**Core principle:** Different granularities for different needs - smart defaults with expert control.

---

## Why This Approach

**Selected: Layered Skills Architecture**

```
┌─────────────────────────────────────────┐
│  /fal-generate (Smart Orchestrator)     │  <- Intent detection + best practices
├─────────────────────────────────────────┤
│  Specialized Skills Layer               │  <- /fal-generate-video, /fal-remove-bg
│  - Task-focused                         │
│  - Model-specific best practices        │
├─────────────────────────────────────────┤
│  Prompt Engineering Layer               │  <- Automatic prompt rewriting
│  - Model-specific optimizations         │
├─────────────────────────────────────────┤
│  Response Adapter Layer                 │  <- Field mapping + fallback logic
│  - Parse different API formats          │
│  - Extract correct fields per model     │
├─────────────────────────────────────────┤
│  Configuration Layer                    │  <- /fal-setup, /fal-update-model
│  - User preferences                     │
│  - Model registry                       │
└─────────────────────────────────────────┘
```

**Rationale:**
- User can start simple (`/fal-generate "make a cat video"`)
- Power users can be explicit (`/fal-generate-video --model flux-pro`)
- System learns from failures and tries alternative field mappings
- Each layer has clear responsibility

---

## Key Decisions

### 1. Skill Hierarchy

| Skill | Purpose | Intelligence Level |
|-------|---------|-------------------|
| `/fal-generate` | Universal entry point | **High** - detects intent (image/video/edit), selects model, applies scenario best practices |
| `/fal-generate-image` | Image generation | **Medium** - model selection within image domain, prompt optimization |
| `/fal-generate-video` | Video generation | **Medium** - video model routing, temporal consistency |
| `/fal-edit-photo` | Image editing | **Medium** - edit-specific models (inpainting, outpainting) |
| `/fal-remove-bg` | Background removal | **Low** - single-purpose, optimized for bg removal |
| `/fal-setup` | Configuration | **Low** - API key setup, preference setting |
| `/fal-update-model` | Model registry | **Low** - add/update model definitions |

**Decision:** Each skill has a dedicated `SKILL.md` that Claude loads when invoked.

---

### 2. Intent Detection Logic (for `/fal-generate`) - Refined

**Goal:** Analyze user prompt + context to determine the correct operation.

**Intent Categories:**
1. `GENERATE_IMAGE` - Create new image from text
2. `GENERATE_VIDEO` - Create new video from text or image
3. `EDIT_IMAGE` - Modify existing image (inpainting, outpainting, style transfer)
4. `REMOVE_BG` - Background removal (special case of edit)
5. `UPSCALE` - Increase image resolution
6. `IMAGE_TO_VIDEO` - Animate a static image

---

#### Detection Algorithm (Multi-Stage)

```python
class IntentDetector:
    def __init__(self):
        self.session_context = {
            "last_operation": None,      # Last completed operation
            "last_result": None,          # Last generated/edited asset
            "last_result_type": None,     # "image" or "video"
            "conversation_history": []    # Recent prompts
        }

    def detect_intent(self, prompt: str, attachments: list = None) -> dict:
        """
        Multi-stage intent detection with context awareness.

        Returns: {
            "intent": Intent enum,
            "confidence": float (0-1),
            "reasoning": str,
            "context_used": dict
        }
        """

        # Stage 1: Explicit Command Detection
        if explicit := self._check_explicit_commands(prompt):
            return {
                "intent": explicit,
                "confidence": 1.0,
                "reasoning": "Explicit command detected",
                "context_used": {}
            }

        # Stage 2: Context Analysis
        context_clues = self._analyze_context(prompt, attachments)

        # Stage 3: Keyword Pattern Matching
        keyword_scores = self._score_keywords(prompt)

        # Stage 4: Combine signals and decide
        return self._combine_and_decide(context_clues, keyword_scores, prompt)

    def _check_explicit_commands(self, prompt: str) -> Optional[Intent]:
        """Check for explicit operation keywords."""
        prompt_lower = prompt.lower().strip()

        # Remove background is very specific
        if any(phrase in prompt_lower for phrase in [
            "remove background", "remove bg", "transparent background",
            "remove the background", "background removal", "no background"
        ]):
            return Intent.REMOVE_BG

        # Upscale is explicit
        if any(word in prompt_lower for word in [
            "upscale", "higher resolution", "increase resolution",
            "make it bigger", "larger size", "4k", "8k"
        ]):
            return Intent.UPSCALE

        return None

    def _analyze_context(self, prompt: str, attachments: list) -> dict:
        """Analyze conversation and file context."""
        clues = {
            "has_attachment": len(attachments) > 0 if attachments else False,
            "attachment_type": None,
            "references_previous": False,
            "previous_result_type": None,
        }

        # Check attachments
        if attachments:
            # Assume attachments are image or video files
            clues["attachment_type"] = self._detect_file_type(attachments[0])

        # Check for pronouns/references to previous work
        reference_patterns = [
            r'\bit\b', r'\bthis\b', r'\bthat\b',
            r'\bthe (image|picture|photo|video)',
            r'\bmy (image|picture|photo|video)',
        ]
        if any(re.search(pattern, prompt.lower()) for pattern in reference_patterns):
            clues["references_previous"] = True
            clues["previous_result_type"] = self.session_context.get("last_result_type")

        return clues

    def _score_keywords(self, prompt: str) -> dict:
        """Score prompt against keyword patterns for each intent."""
        prompt_lower = prompt.lower()
        scores = {}

        # Video generation keywords
        video_keywords = [
            ("video", 3.0), ("animation", 2.5), ("animate", 2.5),
            ("motion", 2.0), ("moving", 2.0), ("movie", 2.0),
            ("clip", 1.5), ("footage", 2.0), ("cinematic", 1.5),
        ]
        scores["video"] = sum(
            weight for word, weight in video_keywords
            if word in prompt_lower
        )

        # Image editing keywords
        edit_keywords = [
            ("edit", 2.5), ("change", 2.0), ("modify", 2.5),
            ("add", 1.5), ("remove", 2.0), ("replace", 2.5),
            ("adjust", 2.0), ("improve", 1.5), ("enhance", 1.5),
            ("fix", 2.0), ("retouch", 2.5), ("inpaint", 3.0),
        ]
        scores["edit"] = sum(
            weight for word, weight in edit_keywords
            if word in prompt_lower
        )

        # Image generation keywords (baseline)
        generate_keywords = [
            ("generate", 2.0), ("create", 2.0), ("make", 1.0),
            ("draw", 1.5), ("design", 1.5), ("picture", 1.0),
            ("image", 1.0), ("photo", 1.0),
        ]
        scores["generate"] = sum(
            weight for word, weight in generate_keywords
            if word in prompt_lower
        )

        # Image-to-video keywords
        i2v_keywords = [
            ("animate this", 3.0), ("bring to life", 2.5),
            ("make it move", 2.5), ("motion from", 2.0),
        ]
        scores["image_to_video"] = sum(
            weight for phrase, weight in i2v_keywords
            if phrase in prompt_lower
        )

        return scores

    def _combine_and_decide(self, context: dict, keyword_scores: dict, prompt: str) -> dict:
        """Combine all signals to make final decision."""

        # Rule 1: Attachment + reference suggests edit
        if context["has_attachment"] or context["references_previous"]:
            # Check if it's image-to-video
            if keyword_scores.get("video", 0) > 2.0:
                return {
                    "intent": Intent.IMAGE_TO_VIDEO,
                    "confidence": 0.85,
                    "reasoning": "Attachment/reference + video keywords → animate image",
                    "context_used": context
                }

            # Otherwise it's likely an edit
            if keyword_scores.get("edit", 0) > keyword_scores.get("generate", 0):
                return {
                    "intent": Intent.EDIT_IMAGE,
                    "confidence": 0.8,
                    "reasoning": "Attachment + edit keywords → modify image",
                    "context_used": context
                }

        # Rule 2: Strong video signals
        if keyword_scores.get("video", 0) > 3.0:
            return {
                "intent": Intent.GENERATE_VIDEO,
                "confidence": 0.9,
                "reasoning": "Strong video keywords detected",
                "context_used": context
            }

        # Rule 3: Edit keywords without attachment might need clarification
        if keyword_scores.get("edit", 0) > 3.0 and not context["has_attachment"]:
            # Check conversation history for recent image generation
            if self.session_context.get("last_result_type") == "image":
                return {
                    "intent": Intent.EDIT_IMAGE,
                    "confidence": 0.75,
                    "reasoning": "Edit keywords + recent image in context → edit last image",
                    "context_used": {**context, "assumed_target": "last_result"}
                }

        # Rule 4: Default to image generation
        return {
            "intent": Intent.GENERATE_IMAGE,
            "confidence": 0.6,
            "reasoning": "No strong signals for other intents → generate new image",
            "context_used": context
        }

    def update_context(self, operation: str, result_type: str, result: Any):
        """Update session context after successful operation."""
        self.session_context["last_operation"] = operation
        self.session_context["last_result"] = result
        self.session_context["last_result_type"] = result_type
        self.session_context["conversation_history"].append({
            "operation": operation,
            "result_type": result_type,
            "timestamp": current_timestamp()
        })

        # Keep only last 5 operations in history
        if len(self.session_context["conversation_history"]) > 5:
            self.session_context["conversation_history"].pop(0)
```

---

#### Example Intent Detection Scenarios

**Scenario 1: New Image Generation**
```
User: "a cat wearing a wizard hat"
Attachments: None
Context: No previous operations

Detection:
- Explicit commands: None
- Context: No attachment, no reference
- Keywords: generate=1.0 (make implied)
- Decision: GENERATE_IMAGE (confidence: 0.6)
```

**Scenario 2: Video Generation**
```
User: "create an animation of a cat running"
Attachments: None
Context: None

Detection:
- Explicit commands: None
- Context: No special context
- Keywords: video=2.5 (animation), generate=2.0 (create)
- Decision: GENERATE_VIDEO (confidence: 0.9)
```

**Scenario 3: Image Edit with Attachment**
```
User: "make this more colorful"
Attachments: [image.png]
Context: Has attachment (type: image)

Detection:
- Explicit commands: None
- Context: has_attachment=True, references_previous=True (this)
- Keywords: edit=1.0 (make implied edit)
- Decision: EDIT_IMAGE (confidence: 0.8)
```

**Scenario 4: Edit Previous Result**
```
User: "make it more colorful"
Attachments: None
Context: Last operation was GENERATE_IMAGE

Detection:
- Explicit commands: None
- Context: references_previous=True (it), previous_result_type=image
- Keywords: edit=1.0 (make implied)
- Decision: EDIT_IMAGE (confidence: 0.75)
  Note: Will use last_result from session context
```

**Scenario 5: Animate Image**
```
User: "animate this image"
Attachments: [photo.jpg]
Context: Has attachment

Detection:
- Explicit commands: None
- Context: has_attachment=True
- Keywords: video=2.5 (animate), i2v=3.0 (animate this)
- Decision: IMAGE_TO_VIDEO (confidence: 0.85)
```

**Scenario 6: Ambiguous Case**
```
User: "improve this"
Attachments: None
Context: Last operation was GENERATE_VIDEO

Detection:
- Explicit commands: None
- Context: references_previous=True (this), previous_result_type=video
- Keywords: edit=1.5 (improve)
- Decision: EDIT_IMAGE (confidence: 0.5) ⚠️ Low confidence!

Action: Show clarification prompt
  "Did you mean:
   1. Edit the video from earlier
   2. Generate a new improved version
   3. Something else"
```

---

#### Confidence Thresholds

```python
CONFIDENCE_THRESHOLDS = {
    "high": 0.8,      # Proceed without confirmation
    "medium": 0.6,    # Proceed but show reasoning
    "low": 0.5,       # Ask for clarification
}

def handle_detection_result(detection: dict):
    confidence = detection["confidence"]

    if confidence >= CONFIDENCE_THRESHOLDS["high"]:
        # High confidence - proceed directly
        execute_intent(detection["intent"])

    elif confidence >= CONFIDENCE_THRESHOLDS["medium"]:
        # Medium confidence - show reasoning and proceed
        print(f"🤔 I think you want to {detection['intent'].value}")
        print(f"   Reasoning: {detection['reasoning']}")
        execute_intent(detection["intent"])

    else:
        # Low confidence - ask user
        ask_user_to_clarify(detection)
```

---

#### Session Context Management

```python
# Example session state during conversation

# After: User: "/fal-generate 'a cat'"
session_context = {
    "last_operation": "GENERATE_IMAGE",
    "last_result": "https://fal.ai/files/cat.png",
    "last_result_type": "image",
    "conversation_history": [
        {
            "operation": "GENERATE_IMAGE",
            "result_type": "image",
            "timestamp": "2026-01-28T10:30:00Z"
        }
    ]
}

# User: "make it blue"
# → Detects EDIT_IMAGE (confidence: 0.75)
# → Uses last_result as source image

# After edit:
session_context = {
    "last_operation": "EDIT_IMAGE",
    "last_result": "https://fal.ai/files/cat-blue.png",
    "last_result_type": "image",
    "conversation_history": [
        {"operation": "GENERATE_IMAGE", ...},
        {
            "operation": "EDIT_IMAGE",
            "result_type": "image",
            "timestamp": "2026-01-28T10:31:00Z",
            "source": "last_result"
        }
    ]
}
```

---

**Implementation:** Intent detection lives in `/fal-generate` SKILL.md with decision tree and session context tracking.

---

### 3. Prompt Engineering Layer

**Challenge:** Different fal.ai models respond better to different prompt styles.

**Solution:** Model-specific prompt templates and rewriting rules.

**Example:**
```yaml
# Model: flux-pro
prompt_template: |
  {base_prompt}, highly detailed, 8k resolution, professional photography
negative_prompt: |
  blurry, low quality, distorted

# Model: multiple-angles
prompt_template: |
  {base_prompt}, camera angle: {angle}, {lighting_keywords}
angle_keywords: ["front view", "side view", "top view", "low angle"]

# Model: ltx-video
prompt_template: |
  {base_prompt}, smooth motion, cinematic, temporal coherence
```

**Implementation:**
- Each specialized skill includes its model's prompt guidelines
- `/fal-generate` delegates to specialized skill after intent detection

---

### 4. Response Adapter Layer (Refined)

**Problem:** Different fal.ai models return results in different JSON structures.

**Example differences:**
```javascript
// Model A (flux-pro):
{ "images": [{ "url": "...", "width": 1024, "content_type": "image/png" }] }

// Model B (kling-video):
{ "output": { "video_url": "...", "thumbnail": "...", "duration": 5.2 } }

// Model C (remove-bg):
{ "result": { "image": "https://...", "removed_pixels": 12540 } }

// Model D (unknown new model):
{ "data": [{ "content": { "url": "..." } }] }
```

---

#### Strategy: Hybrid Auto-Try + User Confirmation

**Step 1: Model-Specific Extraction (if known)**
```yaml
# From model registry
response_format:
  primary_path: images[0].url  # Known from registry
  confidence: high             # Based on past successes
  last_verified: 2026-01-28
```

**Step 2: Automatic Fallback Chain (if primary fails)**
```python
COMMON_FIELD_PATTERNS = [
    # Direct fields
    "url", "image_url", "video_url", "result_url",

    # Nested single-level
    "result", "output", "data", "response",
    "result.url", "output.url", "data.url",
    "result.image", "output.image", "data.image",

    # Array access
    "images[0]", "results[0]", "outputs[0]",
    "images[0].url", "results[0].url", "data[0].url",

    # Deep nested
    "data.result.url", "output.result.image",
    "data[0].content.url", "output.images[0].url",
]

def try_extraction(response: dict) -> Optional[str]:
    for pattern in COMMON_FIELD_PATTERNS:
        if value := extract_by_pattern(response, pattern):
            if is_valid_url(value) or is_valid_data_uri(value):
                return value, pattern
    return None, None
```

**Step 3: User Confirmation (if all auto-tries fail)**
```python
# Claude shows user the response and asks
if extracted_value is None:
    print_formatted_json(response)
    print("\nCouldn't automatically find the result.")
    print("Please help identify the correct field:")

    # Extract all URL-like values from response
    candidates = find_url_like_values(response)

    if candidates:
        print("Found these possible URLs:")
        for i, (path, value) in enumerate(candidates):
            print(f"{i+1}. {path}: {value[:50]}...")

        choice = ask_user_choice(1, len(candidates))
        learned_path = candidates[choice - 1][0]
    else:
        # Ask user to specify path
        learned_path = ask_user_input("Enter the JSON path (e.g., 'result.url'): ")

    # Track this discovery
    track_field_discovery(model_id, learned_path, response)
```

**Step 4: Confidence-Based Persistence**
```python
# Track field discoveries in memory
field_usage_tracker = {
    "fal-ai/flux-pro": {
        "images[0].url": {
            "success_count": 15,
            "fail_count": 0,
            "last_used": "2026-01-28",
            "confidence": "high"
        }
    },
    "fal-ai/new-model": {
        "data.result.url": {
            "success_count": 2,  # Not enough yet
            "fail_count": 0,
            "first_seen": "2026-01-28",
            "confidence": "medium"
        }
    }
}

def should_persist_to_registry(model_id: str, field_path: str) -> bool:
    tracker = field_usage_tracker.get(model_id, {}).get(field_path, {})

    # Require 3 successes with no failures
    if tracker.get("success_count", 0) >= 3 and tracker.get("fail_count", 0) == 0:
        return True

    # Or 5 successes with <20% failure rate
    total = tracker.get("success_count", 0) + tracker.get("fail_count", 0)
    if total >= 5 and tracker.get("success_count", 0) / total > 0.8:
        return True

    return False

# When threshold met, update model registry
if should_persist_to_registry(model_id, discovered_path):
    update_model_registry(
        model_id,
        response_format={
            "primary_path": discovered_path,
            "confidence": "high",
            "last_verified": current_date(),
            "auto_learned": True
        }
    )
    notify_user(f"✓ Learned response format for {model_id}")
```

---

#### Implementation in SKILL.md

**Each skill includes response handling instructions:**

```markdown
## Response Handling

### Expected Response Format
(from model registry, if confidence=high)

### Extraction Logic
1. Try primary_path from registry
2. If fails, try common patterns (images[0].url, output.url, etc.)
3. If all fail, show response to user
4. Track successful extractions
5. Update registry when confidence threshold met (3+ successes)

### Fallback Behavior
- Show formatted JSON to user
- Extract all URL-like values as candidates
- Let user select or specify path
- Remember choice for future attempts
```

---

#### Advantages of This Approach

1. **Fast for known models** - Direct path extraction, no trial needed
2. **Self-healing** - Adapts to API changes automatically
3. **User-friendly** - Clear prompts when help is needed
4. **Safe learning** - Requires multiple confirmations before persisting
5. **Transparent** - User can see what was learned and when

---

#### Model Registry Schema (Updated)

```yaml
model_id: fal-ai/flux-pro
api_format:
  response_format:
    primary_path: images[0].url
    alternative_paths:  # Optional fallbacks
      - output.url
      - result.image_url
    confidence: high      # high, medium, low
    last_verified: 2026-01-28
    auto_learned: false  # true if discovered by system
    success_count: 15    # Track reliability
    fail_count: 0
```

---

#### Session State Tracking

During a conversation, maintain:

```python
session_field_discoveries = {
    "fal-ai/experimental-model": {
        "attempted_paths": [
            ("images[0].url", False),
            ("output.url", False),
            ("data.result.url", True)  # This worked!
        ],
        "confirmed_path": "data.result.url",
        "attempts_count": 1  # Will increment with each success
    }
}
```

---

**Implementation:**
- Each SKILL.md includes expected response format
- Common fallback patterns in shared instruction block
- Confidence tracking in session memory
- Persistent updates to model registry after threshold met

---

### 5. Configuration Management

**User preferences to track:**

```yaml
# ~/.fal-skill-config.yaml
api_key: sk-...
default_models:
  image: flux-dev  # or flux-pro
  video: kling-v1
  edit: flux-dev-inpainting
preferences:
  image_size: 1024x1024
  video_duration: 5s
  quality_priority: speed  # or quality
model_history:
  flux-pro:
    last_used: 2026-01-28
    success_rate: 0.95
  flux-dev:
    last_used: 2026-01-27
    success_rate: 0.88
```

**Skills needed:**
- `/fal-setup` - Initial configuration wizard
- `/fal-update-model` - Add/edit model definitions
- `/fal-preferences` - Update user preferences

---

### 6. Model Registry Structure

**Each model entry includes:**

```yaml
model_id: fal-ai/flux-pro
metadata:
  category: image-generation
  cost_tier: premium  # free, standard, premium
  speed_tier: slow    # fast, medium, slow
  quality_tier: highest
api_format:
  endpoint: /fal-ai/flux-pro
  request_fields:
    - prompt: required, string, max_length=1000
    - image_size: optional, enum=[512x512, 1024x1024]
    - num_images: optional, int, default=1
  response_format:
    type: nested
    path: images[0].url
prompt_engineering:
  template: "{prompt}, highly detailed, professional"
  negative_prompt: "blurry, low quality"
  best_practices:
    - Use detailed descriptions
    - Specify art style
    - Include quality keywords
use_cases:
  - final production images
  - high-quality assets
  - commercial use
```

**Storage:** Could be JSON/YAML in `~/.claude-code/skills/fal-skill/models/`

---

## Proposed Skill Structure

```
~/.claude-code/skills/fal-skill/
├── SKILL.md                    # Main orchestrator: /fal-generate
├── skills/
│   ├── generate-image/
│   │   └── SKILL.md           # /fal-generate-image
│   ├── generate-video/
│   │   └── SKILL.md           # /fal-generate-video
│   ├── edit-photo/
│   │   └── SKILL.md           # /fal-edit-photo
│   ├── remove-bg/
│   │   └── SKILL.md           # /fal-remove-bg
│   ├── setup/
│   │   └── SKILL.md           # /fal-setup
│   └── update-model/
│       └── SKILL.md           # /fal-update-model
├── models/
│   ├── image-models.yaml      # Image generation models
│   ├── video-models.yaml      # Video generation models
│   └── editing-models.yaml    # Image editing models
├── prompts/
│   └── templates.yaml         # Prompt templates per model
└── docs/
    ├── architecture.md        # This document
    └── model-guide.md         # Model selection guide
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Create base skill structure
2. Implement `/fal-setup` for configuration
3. Create model registry with 3-5 core models
4. Build response adapter utilities

### Phase 2: Basic Generation Skills
1. `/fal-generate-image` - Flux Pro/Dev support
2. `/fal-generate-video` - Basic video generation
3. `/fal-remove-bg` - Single-purpose skill

### Phase 3: Orchestration Layer
1. `/fal-generate` - Intent detection
2. Prompt engineering layer integration
3. Best practices routing

### Phase 4: Advanced Features
1. `/fal-edit-photo` - Inpainting, outpainting
2. Response adapter learning from failures
3. User preference learning

---

## Example User Flows

### Flow 1: Beginner User
```
User: /fal-generate "a cat wearing a wizard hat"

Claude:
1. Loads /fal-generate skill
2. Detects intent: IMAGE_GENERATION
3. Routes to /fal-generate-image internally
4. Checks user config: no preference set
5. Selects flux-dev (good quality/speed balance)
6. Applies prompt template: "a cat wearing a wizard hat, highly detailed, 8k"
7. Calls fal.ai API
8. Uses response adapter to extract image URL
9. Returns result to user with image preview
```

### Flow 2: Power User
```
User: /fal-generate-video --model kling-v1 --duration 10s "cat wizard casting spell"

Claude:
1. Loads /fal-generate-video skill (skips intent detection)
2. Uses explicit model: kling-v1
3. Applies video-specific prompt template
4. Sets duration parameter
5. Calls API
6. Extracts video URL
7. Returns result
```

### Flow 3: Error Recovery
```
User: /fal-generate "remove background from image.png"

Claude:
1. Detects intent: REMOVE_BG
2. Routes to /fal-remove-bg
3. First attempt: tries common response field "output.url"
4. Field not found
5. Tries fallback: "result.image_url"
6. Success! Logs this model's format for future
7. Returns result
```

---

## Detailed Design: Response Adapter

### Complete Field Extraction Algorithm

```python
def extract_result(response: dict, model_id: str, model_registry: dict) -> tuple[Any, str]:
    """
    Extract result from API response with fallback and learning.

    Returns: (extracted_value, field_path_used)
    """

    # Phase 1: Try known path from registry
    if model_config := model_registry.get(model_id):
        if response_format := model_config.get("api_format", {}).get("response_format"):
            primary_path = response_format.get("primary_path")

            if value := extract_by_path(response, primary_path):
                track_success(model_id, primary_path)
                return value, primary_path

            # Primary path failed - track failure
            track_failure(model_id, primary_path)

    # Phase 2: Try common patterns
    for pattern in COMMON_FIELD_PATTERNS:
        if value := extract_by_path(response, pattern):
            if is_valid_result(value):
                track_discovery(model_id, pattern, success=True)
                return value, pattern

    # Phase 3: Ask user for help
    return ask_user_to_identify_field(response, model_id)


def extract_by_path(data: dict, path: str) -> Optional[Any]:
    """
    Extract value from nested dict/list using path notation.

    Examples:
        data = {"images": [{"url": "..."}]}
        extract_by_path(data, "images[0].url") -> "..."
    """
    try:
        # Parse path: "images[0].url" -> ["images", 0, "url"]
        parts = parse_path(path)

        value = data
        for part in parts:
            if isinstance(part, int):
                value = value[part]
            else:
                value = value[part]

        return value if value is not None else None
    except (KeyError, IndexError, TypeError):
        return None


def is_valid_result(value: Any) -> bool:
    """Check if extracted value looks like a valid result."""
    if isinstance(value, str):
        # Check if URL
        if value.startswith(("http://", "https://", "data:")):
            return True
        # Check if file path
        if value.endswith((".png", ".jpg", ".jpeg", ".mp4", ".webm", ".gif")):
            return True

    if isinstance(value, dict):
        # Check if contains URL-like keys
        url_keys = {"url", "image_url", "video_url", "file_url", "download_url"}
        if any(key in value for key in url_keys):
            return True

    return False


def find_url_like_values(data: Any, path: str = "") -> list[tuple[str, Any]]:
    """
    Recursively find all URL-like values in response.

    Returns: [(json_path, value), ...]
    """
    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            if is_valid_result(value):
                results.append((new_path, value))
            results.extend(find_url_like_values(value, new_path))

    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            if is_valid_result(item):
                results.append((new_path, item))
            results.extend(find_url_like_values(item, new_path))

    return results


def ask_user_to_identify_field(response: dict, model_id: str) -> tuple[Any, str]:
    """
    Show response to user and ask them to identify result field.
    """
    print(f"\n❌ Couldn't automatically extract result from {model_id}")
    print("\n📋 API Response:")
    print_formatted_json(response)

    candidates = find_url_like_values(response)

    if candidates:
        print(f"\n🔍 Found {len(candidates)} possible result(s):")
        for i, (path, value) in enumerate(candidates, 1):
            preview = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
            print(f"  {i}. {path}")
            print(f"     → {preview}")

        print(f"\n  {len(candidates) + 1}. None of these (I'll specify manually)")

        choice = ask_user_choice(1, len(candidates) + 1)

        if choice <= len(candidates):
            field_path, value = candidates[choice - 1]
        else:
            field_path = ask_user_input("Enter the JSON path (e.g., 'result.url'): ")
            value = extract_by_path(response, field_path)

    else:
        print("\n❓ No obvious URL-like values found.")
        field_path = ask_user_input("Enter the JSON path to the result: ")
        value = extract_by_path(response, field_path)

    # Track this discovery
    track_discovery(model_id, field_path, success=True, user_confirmed=True)

    print(f"\n✓ Using field: {field_path}")

    return value, field_path
```

---

### Tracking and Persistence

```python
class FieldTracker:
    """Tracks field path discoveries and manages persistence."""

    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.session_stats = {}  # In-memory during conversation

    def track_success(self, model_id: str, field_path: str):
        """Record successful extraction."""
        if model_id not in self.session_stats:
            self.session_stats[model_id] = {}

        if field_path not in self.session_stats[model_id]:
            self.session_stats[model_id][field_path] = {
                "success_count": 0,
                "fail_count": 0,
                "first_used": current_timestamp(),
            }

        self.session_stats[model_id][field_path]["success_count"] += 1
        self.session_stats[model_id][field_path]["last_success"] = current_timestamp()

        # Check if should persist
        if self._should_persist(model_id, field_path):
            self._update_registry(model_id, field_path)

    def track_failure(self, model_id: str, field_path: str):
        """Record failed extraction."""
        if model_id not in self.session_stats:
            self.session_stats[model_id] = {}

        if field_path not in self.session_stats[model_id]:
            self.session_stats[model_id][field_path] = {
                "success_count": 0,
                "fail_count": 0,
            }

        self.session_stats[model_id][field_path]["fail_count"] += 1

    def _should_persist(self, model_id: str, field_path: str) -> bool:
        """Determine if field path should be saved to registry."""
        stats = self.session_stats.get(model_id, {}).get(field_path, {})
        success = stats.get("success_count", 0)
        failure = stats.get("fail_count", 0)

        # Strategy: Confidence-based persistence
        # Require 3 consecutive successes with 0 failures
        if success >= 3 and failure == 0:
            return True

        # Or 5 total attempts with >80% success rate
        total = success + failure
        if total >= 5 and success / total > 0.8:
            return True

        return False

    def _update_registry(self, model_id: str, field_path: str):
        """Update model registry with confirmed field path."""
        registry = load_model_registry(self.registry_path)

        if model_id not in registry:
            print(f"⚠️  Model {model_id} not in registry, skipping persistence")
            return

        stats = self.session_stats[model_id][field_path]

        registry[model_id]["api_format"]["response_format"] = {
            "primary_path": field_path,
            "confidence": "high",
            "auto_learned": True,
            "learned_date": current_timestamp(),
            "success_count": stats["success_count"],
            "fail_count": stats["fail_count"],
        }

        save_model_registry(self.registry_path, registry)

        print(f"\n✅ Learned response format for {model_id}:")
        print(f"   Field path: {field_path}")
        print(f"   Confidence: high (based on {stats['success_count']} successes)")
```

---

### Example Scenario Walkthrough

**Scenario:** User tries a brand new fal.ai model that's not in registry.

```
User: /fal-generate-image --model fal-ai/experimental-flux "a cat"

Claude:
1. Loads /fal-generate-image skill
2. Checks model registry: fal-ai/experimental-flux not found
3. Creates API request
4. Receives response:
   {
     "status": "completed",
     "data": {
       "output_images": [
         {
           "content": "https://fal.ai/files/abc123.png",
           "format": "png",
           "size": 1024
         }
       ]
     }
   }
5. Response adapter runs:
   - No primary_path (model not in registry)
   - Tries common patterns:
     * "url" -> Not found
     * "image_url" -> Not found
     * "images[0].url" -> Not found
     * "result.url" -> Not found
     * ... (tries all COMMON_FIELD_PATTERNS)
     * None match!

6. Asks user:
   ❌ Couldn't automatically extract result from fal-ai/experimental-flux

   📋 API Response:
   {
     "status": "completed",
     "data": {
       "output_images": [
         {
           "content": "https://fal.ai/files/abc123.png",
           "format": "png",
           "size": 1024
         }
       ]
     }
   }

   🔍 Found 1 possible result(s):
     1. data.output_images[0].content
        → https://fal.ai/files/abc123.png

     2. None of these (I'll specify manually)

   Choose option (1-2):

User: 1

Claude:
   ✓ Using field: data.output_images[0].content
   [Shows the image]

   (Tracks: fal-ai/experimental-flux -> data.output_images[0].content, 1 success)

--- User tries same model again ---

User: /fal-generate-image --model fal-ai/experimental-flux "a dog"

Claude:
7. Tries primary_path: None (still not persisted, only 1 success)
8. Tries common patterns + remembered path from session
9. Tries: data.output_images[0].content -> Success!
10. (Tracks: 2nd success)

--- User tries third time ---

User: /fal-generate-image --model fal-ai/experimental-flux "a bird"

Claude:
11. Tries data.output_images[0].content -> Success!
12. (Tracks: 3rd success, 0 failures)
13. Threshold met! Updates registry:

    ✅ Learned response format for fal-ai/experimental-flux:
       Field path: data.output_images[0].content
       Confidence: high (based on 3 successes)

--- Future uses are instant ---

User: /fal-generate-image --model fal-ai/experimental-flux "a fish"

Claude:
14. Loads model from registry, sees primary_path: data.output_images[0].content
15. Tries that path first -> Success!
16. No fallback needed, instant extraction
```

---

## Open Questions

### 1. How to handle model API format changes?

**Options:**
- **A)** Version the model definitions (flux-pro-v1, flux-pro-v2)
- **B)** Dynamic schema detection (inspect actual response)
- **C)** Fallback chain + user notification

**Lean toward:** B + C - Try to adapt, but notify user if format changed

### 2. Where to store user configuration?

**Options:**
- **A)** `~/.fal-skill-config.yaml` (global)
- **B)** `.fal-skill.yaml` in project root (per-project)
- **C)** Both (project overrides global)

**Lean toward:** C - Maximum flexibility

### 3. How to handle prompt rewriting visibility?

**Options:**
- **A)** Always show user the rewritten prompt
- **B)** Only show on request (--show-prompt flag)
- **C)** Silent rewriting, log to debug file

**Lean toward:** B - Don't overwhelm, but allow inspection

### 4. Should skills call fal.ai directly or via helper script?

**Options:**
- **A)** Skills include Python/JS code to call API directly
- **B)** Skills invoke a CLI tool (e.g., `fal-cli generate ...`)
- **C)** Skills use Claude's WebFetch or Bash tools

**Lean toward:** A for flexibility, with C as fallback

---

## Success Criteria

This skill system succeeds if:

1. **Beginner-friendly:** User can generate content with just `/fal-generate "prompt"`
2. **Expert-accessible:** Power users can control every detail
3. **Self-healing:** System adapts to API changes with minimal manual updates
4. **Learnable:** System improves from usage patterns and failures
5. **Maintainable:** Adding new models is straightforward (<30 min per model)

**Metrics:**
- Time from prompt to result: <30 seconds (including API call)
- Success rate on first attempt: >85%
- Time to add new model: <30 minutes
- User satisfaction: Can accomplish task without reading docs

---

## Next Steps

1. **Create base skill structure** - Set up directory hierarchy
2. **Implement `/fal-setup`** - Configuration wizard
3. **Build model registry** - Start with 3 models (flux-pro, flux-dev, kling-v1)
4. **Create first specialized skill** - `/fal-generate-image` as reference implementation
5. **Test response adapter** - Verify fallback logic works
6. **Implement `/fal-generate`** - Orchestration layer with intent detection

**Estimated effort:**
- Phase 1: 4-6 hours
- Phase 2: 6-8 hours
- Phase 3: 4-6 hours
- Phase 4: 8-10 hours

Total: ~24-30 hours for full implementation

---

## Related Documents

- `2026-01-28-fal-ai-best-practices-brainstorm.md` - Reference documentation approach
- `brainstorm/01-fal-ai-overview.md` - fal.ai platform overview
- `brainstorm/02-fal-ai-best-practices.md` - Usage patterns and recommendations

---

## Comparison: remotion-best-practices vs fal-skill Approach

### remotion-best-practices pattern:
- **Style:** Inline guidance that Claude follows when writing Remotion code
- **Trigger:** Automatic detection when working with Remotion
- **Format:** Instructions for Claude on best practices
- **User interaction:** Transparent - user doesn't invoke directly

### fal-skill approach (this design):
- **Style:** Task-oriented commands user invokes explicitly
- **Trigger:** User runs `/fal-generate`, `/fal-generate-video`, etc.
- **Format:** Skill instructions + model registry + prompt templates
- **User interaction:** Explicit - user chooses when to use fal.ai

**Why different?**
- remotion is a framework (detect and guide automatically)
- fal.ai is a service (user decides when to generate content)
- Our approach is more like `/commit` or `/review-pr` - user-initiated actions

---

## Technical Architecture Notes

### Claude's Role in Each Layer

**Layer 1: Intent Detection**
- Claude analyzes user prompt
- Uses SKILL.md decision tree
- Selects appropriate specialized skill

**Layer 2: Specialized Skills**
- Claude loads specific SKILL.md
- Applies model-specific best practices
- Constructs API request

**Layer 3: Prompt Engineering**
- Claude rewrites user prompt using templates
- Adds quality keywords
- Formats for specific model

**Layer 4: Response Adapter**
- Claude receives API response
- Uses field extraction logic from SKILL.md
- Falls back to generic patterns if needed

**Layer 5: Configuration**
- Claude reads/writes config files
- Remembers user preferences
- Tracks model performance

---

## Alternative Considered: Single Monolithic Skill

**Structure:**
```
/fal-generate [--type image|video|edit] [--model MODEL_ID] "prompt"
```

**Pros:**
- Single skill to maintain
- Simpler structure

**Cons:**
- Skill file becomes very large (>2000 lines)
- Harder to add new capabilities
- All logic in one place
- Less clear separation of concerns

**Decision:** Rejected in favor of layered architecture for maintainability.

---

## Inspiration from Existing Skills

From your system's available skills:

1. **frontend-design** - Task-oriented, creates something new
2. **pdf / pptx** - File operations with specific formats
3. **commit / review-pr** - Git workflow automation
4. **agent-browser** - External service interaction

Our approach is closest to **agent-browser** - interacting with external service (fal.ai) via commands with different granularities.

---

## Final Architecture Diagram

```
User Input
    ↓
┌─────────────────────────────────────┐
│   /fal-generate                     │ ← Smart router
│   (Intent Detection)                │
└─────────────────────────────────────┘
    ↓ ↓ ↓
┌──────────┬──────────────┬──────────┐
│ /fal-    │ /fal-        │ /fal-    │ ← Specialized
│ generate-│ generate-    │ edit-    │   commands
│ image    │ video        │ photo    │
└──────────┴──────────────┴──────────┘
    ↓
┌─────────────────────────────────────┐
│   Prompt Engineering                │ ← Model-specific
│   (Template Application)            │   optimization
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   fal.ai API Call                   │ ← Actual generation
│   (HTTP Request)                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   Response Adapter                  │ ← Field extraction
│   (Parse & Extract)                 │   + fallback
└─────────────────────────────────────┘
    ↓
Result to User
```

