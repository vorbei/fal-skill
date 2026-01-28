---
title: Phase 1 Foundation Implementation Plan
type: feat
date: 2026-01-28
parent_plan: 2026-01-28-feat-fal-ai-multi-capability-skill-plan.md
status: ready
---

# Phase 1: Foundation Implementation Plan

**Goal**: Setup infrastructure and configuration system for fal.ai skill

**Duration**: Week 1 (5-7 days estimated)

**Prerequisites**:
- ✅ Git repository initialized
- ✅ Planning and architecture complete
- ✅ Brainstorming documents available
- [ ] fal.ai API key available for testing

---

## Overview

This phase establishes the foundational infrastructure for the fal-skill project:
- Directory structure
- Configuration system
- Python API client with both generation and discovery capabilities
- Dynamic model discovery from fal.ai API
- Setup skill for user onboarding

## Task Breakdown

### Task 1: Directory Structure Setup

**Objective**: Create complete project directory structure

**Files to Create**:
```
fal-skill/
├── skills/
│   └── fal-setup/
│       └── SKILL.md
├── scripts/
│   ├── fal_api.py
│   └── lib/
│       ├── __init__.py
│       ├── api_client.py
│       ├── models.py
│       └── discovery.py
├── models/
│   ├── curated.yaml
│   └── cache/
│       └── .gitkeep
├── config/
│   └── response_patterns.yaml
├── .gitignore
└── README.md
```

**Implementation Steps**:
1. Create directory tree
2. Add `.gitkeep` files for empty directories
3. Create `.gitignore` for Python cache, API keys, model cache
4. Initialize README with project description

**Success Criteria**:
- [ ] All directories exist
- [ ] .gitignore covers `.pyc`, `__pycache__`, `.env`, `cache/*.json`
- [ ] README has project title and brief description

**Estimated Time**: 15 minutes

---

### Task 2: API Client Foundation

**Objective**: Create Python API client for both fal.ai generation and model discovery APIs

**Files**:
- `scripts/fal_api.py` - CLI entry point
- `scripts/lib/api_client.py` - HTTP wrapper for fal.ai API
- `scripts/lib/models.py` - Model registry loader
- `scripts/lib/discovery.py` - Model discovery from API

#### Subtask 2.1: `scripts/lib/api_client.py`

**Purpose**: Low-level HTTP client for fal.ai API (generation + discovery)

**Key Features**:
- Load API key from `~/.config/fal-skill/.env`
- Make authenticated requests to fal.ai
- Support both generation (`/run`, `/subscribe`) and discovery (`/v1/models`) endpoints
- Handle errors gracefully
- Pagination support for model discovery

**Implementation**:
```python
import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

class FalAPIClient:
    """HTTP client for fal.ai API (generation + discovery)"""

    BASE_URL = "https://queue.fal.run"
    DISCOVERY_URL = "https://api.fal.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()

    def _load_api_key(self) -> str:
        """Load API key from config file"""
        config_path = os.path.expanduser("~/.config/fal-skill/.env")
        if not os.path.exists(config_path):
            raise ValueError("API key not found. Run /fal-setup first.")

        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('FAL_KEY='):
                    return line.strip().split('=', 1)[1]

        raise ValueError("FAL_KEY not found in config file")

    def run_model(self, endpoint_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a model and return results"""
        url = f"{self.BASE_URL}/{endpoint_id}"

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }

        data = json.dumps({"input": input_data}).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"API Error {e.code}: {error_body}")

    def discover_models(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Discover models from fal.ai API with pagination support"""
        params = {
            "status": status,
            "limit": str(limit)
        }

        if category:
            params["category"] = category

        if cursor:
            params["cursor"] = cursor

        query_string = urllib.parse.urlencode(params)
        url = f"{self.DISCOVERY_URL}/v1/models?{query_string}"

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(url, headers=headers, method='GET')

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"API Discovery Error {e.code}: {error_body}")

    def validate_key(self) -> bool:
        """Test if API key is valid by making a simple discovery request"""
        try:
            result = self.discover_models(limit=1)
            return "models" in result
        except Exception:
            return False
```

**Success Criteria**:
- [ ] Can load API key from config
- [ ] Can make authenticated generation requests
- [ ] Can discover models from `/v1/models` endpoint
- [ ] Pagination support with cursor parameter
- [ ] Proper error handling for HTTP errors

**Estimated Time**: 45 minutes

#### Subtask 2.2: `scripts/lib/discovery.py`

**Purpose**: Intelligent model discovery with caching

**Key Features**:
- Fetch models from fal.ai API with pagination
- Cache results with 24-hour TTL
- Category filtering
- Fallback to curated models

**Implementation**:
```python
import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class ModelDiscovery:
    """Model discovery with intelligent caching"""

    CACHE_DIR = os.path.expanduser("~/.config/fal-skill/cache")
    CACHE_TTL = 24 * 60 * 60  # 24 hours in seconds

    def __init__(self, api_client):
        self.api_client = api_client
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def discover_all_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Discover all models with caching"""
        cache_file = os.path.join(self.CACHE_DIR, "all_models.json")

        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_file):
            return self._load_cache(cache_file)

        # Fetch from API with pagination
        all_models = []
        cursor = None

        print("Discovering models from fal.ai API...")

        while True:
            response = self.api_client.discover_models(
                status="active",
                limit=100,
                cursor=cursor
            )

            all_models.extend(response.get("models", []))

            if not response.get("has_more", False):
                break

            cursor = response.get("next_cursor")

        print(f"Discovered {len(all_models)} models")

        # Save to cache
        self._save_cache(cache_file, all_models)

        return all_models

    def discover_by_category(
        self,
        category: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Discover models by category with caching"""
        cache_file = os.path.join(self.CACHE_DIR, f"{category}.json")

        # Check cache first
        if not force_refresh and self._is_cache_valid(cache_file):
            return self._load_cache(cache_file)

        # Fetch from API
        all_models = []
        cursor = None

        while True:
            response = self.api_client.discover_models(
                category=category,
                status="active",
                limit=100,
                cursor=cursor
            )

            all_models.extend(response.get("models", []))

            if not response.get("has_more", False):
                break

            cursor = response.get("next_cursor")

        # Save to cache
        self._save_cache(cache_file, all_models)

        return all_models

    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache exists and is not expired"""
        if not os.path.exists(cache_file):
            return False

        file_time = os.path.getmtime(cache_file)
        age = time.time() - file_time

        return age < self.CACHE_TTL

    def _load_cache(self, cache_file: str) -> List[Dict[str, Any]]:
        """Load models from cache"""
        with open(cache_file, 'r') as f:
            return json.load(f)

    def _save_cache(self, cache_file: str, models: List[Dict[str, Any]]):
        """Save models to cache"""
        with open(cache_file, 'w') as f:
            json.dump(models, f, indent=2)
```

**Success Criteria**:
- [ ] Discovers all models via API with pagination
- [ ] Caches results to `~/.config/fal-skill/cache/`
- [ ] Cache expires after 24 hours
- [ ] Category filtering works
- [ ] Force refresh bypasses cache

**Estimated Time**: 45 minutes

#### Subtask 2.3: `scripts/lib/models.py`

**Purpose**: Model registry loader (curated + discovered)

**Key Features**:
- Load curated models from YAML
- Integrate discovered models
- Model selection logic
- Fallback mechanism

**Implementation**:
```python
import os
import yaml
from typing import Dict, List, Optional, Any

class ModelRegistry:
    """Model registry combining curated and discovered models"""

    def __init__(self, discovery_service):
        self.discovery = discovery_service
        self.curated_models = self._load_curated_models()

    def _load_curated_models(self) -> Dict[str, Any]:
        """Load curated models from YAML"""
        # Get the project root (3 levels up from lib/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        curated_path = os.path.join(project_root, "models", "curated.yaml")

        if not os.path.exists(curated_path):
            return {"categories": {}}

        with open(curated_path, 'r') as f:
            return yaml.safe_load(f) or {"categories": {}}

    def get_model_by_category(
        self,
        category: str,
        prefer_curated: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get best model for a category"""

        # First check curated models
        if prefer_curated and category in self.curated_models.get("categories", {}):
            category_models = self.curated_models["categories"][category]

            # Find recommended model
            for model in category_models:
                if model.get("recommended", False):
                    return model

            # Return first model if no recommendation
            if category_models:
                return category_models[0]

        # Fallback to discovered models
        try:
            discovered = self.discovery.discover_by_category(category)
            if discovered:
                return self._convert_discovered_to_model(discovered[0])
        except Exception as e:
            print(f"Warning: Could not discover models for {category}: {e}")

        return None

    def _convert_discovered_to_model(self, discovered_model: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API response format to internal model format"""
        metadata = discovered_model.get("metadata", {})

        return {
            "endpoint_id": discovered_model.get("endpoint_id"),
            "display_name": metadata.get("display_name", "Unknown"),
            "category": metadata.get("category", "unknown"),
            "description": metadata.get("description", ""),
            "cost_tier": "standard",  # Default, could be inferred
            "speed_tier": "medium",
            "quality_tier": "medium",
            "recommended": False,
            "tested": False
        }
```

**Success Criteria**:
- [ ] Loads curated models from YAML
- [ ] Can query models by category
- [ ] Prioritizes curated recommended models
- [ ] Falls back to discovered models
- [ ] Handles missing files gracefully

**Estimated Time**: 30 minutes

#### Subtask 2.4: `scripts/fal_api.py`

**Purpose**: CLI entry point for API operations

**Implementation**:
```python
#!/usr/bin/env python3
"""
fal.ai API CLI wrapper
Handles model execution and discovery
"""

import sys
import json
from lib.api_client import FalAPIClient
from lib.discovery import ModelDiscovery
from lib.models import ModelRegistry

def main():
    if len(sys.argv) < 2:
        print("Usage: fal_api.py <command> [args...]")
        print("Commands:")
        print("  run <endpoint_id> <json_input>")
        print("  discover [category]")
        print("  refresh")
        print("  validate")
        sys.exit(1)

    command = sys.argv[1]

    try:
        client = FalAPIClient()
        discovery = ModelDiscovery(client)
        registry = ModelRegistry(discovery)

        if command == "run":
            if len(sys.argv) < 4:
                print("Usage: fal_api.py run <endpoint_id> <json_input>")
                sys.exit(1)

            endpoint_id = sys.argv[2]
            input_data = json.loads(sys.argv[3])

            result = client.run_model(endpoint_id, input_data)
            print(json.dumps(result, indent=2))

        elif command == "discover":
            category = sys.argv[2] if len(sys.argv) > 2 else None

            if category:
                models = discovery.discover_by_category(category)
            else:
                models = discovery.discover_all_models()

            print(json.dumps(models, indent=2))

        elif command == "refresh":
            print("Refreshing model cache...")
            models = discovery.discover_all_models(force_refresh=True)
            print(f"Refreshed cache with {len(models)} models")

        elif command == "validate":
            if client.validate_key():
                print("✓ API key is valid")
                sys.exit(0)
            else:
                print("✗ API key is invalid")
                sys.exit(1)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Success Criteria**:
- [ ] Can run models via `fal_api.py run <endpoint> <json>`
- [ ] Can discover models via `fal_api.py discover [category]`
- [ ] Can refresh cache via `fal_api.py refresh`
- [ ] Can validate API key via `fal_api.py validate`

**Estimated Time**: 30 minutes

---

### Task 3: Curated Model Registry

**Objective**: Create initial curated model registry with 5 core models

**File**: `models/curated.yaml`

**Implementation**:
```yaml
version: "1.0"
last_updated: "2026-01-28"
description: "Curated subset of tested, recommended fal.ai models"

categories:
  text-to-image:
    - endpoint_id: fal-ai/flux/dev
      display_name: FLUX.1 [dev]
      description: "Fast text-to-image generation with good quality"
      cost_tier: standard
      speed_tier: medium
      quality_tier: high
      recommended: true
      tested: true
      params:
        prompt: "string (required)"
        image_size: "string (optional, default: landscape_4_3)"
        num_inference_steps: "int (optional, default: 28)"
        guidance_scale: "float (optional, default: 3.5)"
        num_images: "int (optional, default: 1)"

    - endpoint_id: z-image/base
      display_name: z-image base
      description: "Budget-friendly fast generation, lower quality"
      cost_tier: budget
      speed_tier: fast
      quality_tier: medium
      recommended: false
      tested: true
      params:
        prompt: "string (required)"
        negative_prompt: "string (optional)"

    - endpoint_id: fal-ai/flux-pro
      display_name: FLUX.1 [pro]
      description: "Highest quality text-to-image, slower and more expensive"
      cost_tier: premium
      speed_tier: slow
      quality_tier: highest
      recommended: false
      tested: true
      params:
        prompt: "string (required)"
        image_size: "string (optional)"
        num_inference_steps: "int (optional)"
        guidance_scale: "float (optional)"

  background-removal:
    - endpoint_id: fal-ai/birefnet/v2
      display_name: Birefnet v2
      description: "High-quality background removal"
      cost_tier: budget
      speed_tier: fast
      quality_tier: high
      recommended: true
      tested: true
      params:
        image_url: "string (required)"
        model: "string (optional, default: General Use (Light))"

  text-to-video:
    - endpoint_id: fal-ai/kling-video/v1/standard/text-to-video
      display_name: Kling Video v1 Standard
      description: "Text-to-video generation, 5-10 second clips"
      cost_tier: premium
      speed_tier: slow
      quality_tier: high
      recommended: true
      tested: false
      params:
        prompt: "string (required)"
        duration: "number (optional, default: 5, max: 10)"
        aspect_ratio: "string (optional, default: 16:9)"
```

**Success Criteria**:
- [ ] YAML is valid and parseable
- [ ] Contains 5 core models (3 image, 1 bg removal, 1 video)
- [ ] Each model has required fields: endpoint_id, display_name, cost/speed/quality tiers
- [ ] Recommended models marked
- [ ] Parameter documentation included

**Estimated Time**: 30 minutes

---

### Task 4: Configuration Files

**Objective**: Create empty configuration templates

#### Subtask 4.1: `config/response_patterns.yaml`

**Purpose**: Template for learned response patterns (empty initially)

**Implementation**:
```yaml
version: "1.0"
last_updated: "2026-01-28"
description: "Learned response field paths for fal.ai models"

# This file is auto-populated as the system learns successful response patterns
# Format:
# model_endpoint_id:
#   success_count: int
#   fail_count: int
#   learned_paths:
#     - path: "string (e.g., images[0].url)"
#       success_rate: float
#       last_seen: "ISO timestamp"

patterns: {}
```

**Estimated Time**: 5 minutes

#### Subtask 4.2: `.gitignore`

**Purpose**: Prevent committing sensitive files

**Implementation**:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/

# API keys and secrets
.env
*.key

# Model cache (large files)
models/cache/*.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

**Estimated Time**: 5 minutes

---

### Task 5: `/fal-setup` Skill

**Objective**: Create setup skill for API key configuration

**File**: `skills/fal-setup/SKILL.md`

**Implementation**:
```markdown
# fal-setup Skill

Configure fal.ai API key and initialize the skill system.

## Usage

```
/fal-setup
```

## What it does

1. Prompts user for fal.ai API key
2. Validates the key by testing API connection
3. Saves key securely to `~/.config/fal-skill/.env`
4. Tests model discovery
5. Creates initial model cache

## Instructions

When this skill is invoked:

1. **Check for existing configuration**:
   ```bash
   ls -la ~/.config/fal-skill/.env 2>/dev/null
   ```

2. **If config exists**, ask user:
   > "API key already configured. Would you like to update it? (yes/no)"

3. **If no config or user wants to update**:
   - Display instructions:
   ```
   Let me help you configure fal.ai integration.

   Step 1: Get your API key
   Visit: https://fal.ai/dashboard/keys
   Create a new API key and paste it here.

   (Your API key should start with something like "abc123-...")
   ```

4. **Get API key from user** using AskUserQuestion tool:
   - Question: "Please paste your fal.ai API key:"
   - Single text input
   - Store in variable: `api_key`

5. **Create config directory and save key**:
   ```bash
   mkdir -p ~/.config/fal-skill
   echo "FAL_KEY=${api_key}" > ~/.config/fal-skill/.env
   chmod 600 ~/.config/fal-skill/.env
   ```

6. **Validate the key**:
   ```bash
   python3 scripts/fal_api.py validate
   ```

7. **If validation succeeds**:
   - Display: "✓ Valid API key configured successfully!"
   - Initialize model cache:
   ```bash
   python3 scripts/fal_api.py discover > /tmp/fal_initial_discovery.json
   wc -l /tmp/fal_initial_discovery.json
   ```
   - Display: "✓ Discovered X models from fal.ai"

8. **If validation fails**:
   - Display: "✗ API key validation failed. Please check your key and try again."
   - Remove invalid config:
   ```bash
   rm ~/.config/fal-skill/.env
   ```
   - Suggest: "Get a valid key from https://fal.ai/dashboard/keys"

9. **Show next steps**:
   ```
   Configuration complete! 🎉

   Try these commands:
   - /fal-generate "a wizard cat"          # Generate an image
   - /fal-generate-image "sunset"          # Image generation
   - /fal-remove-bg [image]                # Remove background

   Model registry location: models/curated.yaml
   Cache location: ~/.config/fal-skill/cache/
   ```

## Error Handling

- **No internet connection**: "Cannot reach fal.ai API. Please check your internet connection."
- **Invalid API key format**: "API key format looks incorrect. It should be a long alphanumeric string."
- **Permission errors**: "Cannot write to ~/.config/fal-skill/. Please check file permissions."

## Security Notes

- API key stored in `~/.config/fal-skill/.env` with `chmod 600` (user-only access)
- Never log or display the full API key
- Key is never committed to git (in .gitignore)
```

**Success Criteria**:
- [ ] Clear step-by-step instructions for Claude Code
- [ ] Validates API key before saving
- [ ] Saves key securely with correct permissions
- [ ] Tests model discovery
- [ ] Provides helpful next steps
- [ ] Error handling for common issues

**Estimated Time**: 45 minutes

---

### Task 6: README.md

**Objective**: Create project README with quick start

**File**: `README.md`

**Implementation**:
```markdown
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
- 🚧 **Phase 1**: Foundation (In Progress)
  - [x] Git repository initialized
  - [ ] Directory structure
  - [ ] API client with discovery
  - [ ] Setup skill
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
```

**Estimated Time**: 20 minutes

---

## Testing Phase 1

### Test 1: Directory Structure
```bash
# Verify all directories exist
ls -la skills/fal-setup/
ls -la scripts/lib/
ls -la models/cache/
ls -la config/

# Verify .gitignore works
touch models/cache/test_models.json
git status  # Should not show test_models.json
```

### Test 2: API Client
```bash
# Test validation (will fail without key)
python3 scripts/fal_api.py validate

# Test discovery (will fail without key)
python3 scripts/fal_api.py discover
```

### Test 3: Full Setup Flow
1. Run `/fal-setup` skill
2. Enter a valid fal.ai API key
3. Verify key validation succeeds
4. Check cache directory for `all_models.json`
5. Verify file contains 1000+ models

### Test 4: Model Discovery
```bash
# Discover all models
python3 scripts/fal_api.py discover > /tmp/all_models.json
wc -l /tmp/all_models.json  # Should be ~1000+ lines

# Discover by category
python3 scripts/fal_api.py discover text-to-image > /tmp/image_models.json
cat /tmp/image_models.json | grep endpoint_id | wc -l  # Should be 150+
```

---

## Deliverables Checklist

- [ ] Directory structure complete
- [ ] `.gitignore` configured
- [ ] `scripts/fal_api.py` CLI working
- [ ] `scripts/lib/api_client.py` with generation + discovery
- [ ] `scripts/lib/discovery.py` with caching
- [ ] `scripts/lib/models.py` registry loader
- [ ] `models/curated.yaml` with 5 core models
- [ ] `config/response_patterns.yaml` template
- [ ] `skills/fal-setup/SKILL.md` complete
- [ ] `README.md` with quick start
- [ ] API key validation working
- [ ] Model discovery fetching 1000+ models
- [ ] Cache persisting with 24h TTL
- [ ] Fallback to curated models on API failure

---

## Next Steps After Phase 1

Once Phase 1 is complete and all tests pass:

1. **Git Commit**:
   ```bash
   git add .
   git commit -m "feat: Phase 1 foundation - setup, API client, model discovery

   - Initialize project structure
   - Add API client with generation and discovery
   - Implement model discovery with caching
   - Create /fal-setup skill
   - Add curated model registry

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

2. **Proceed to Phase 2**: Core Generation Skills
   - `/fal-generate-image` skill
   - `/fal-remove-bg` skill
   - Response Adapter with self-learning

## Estimated Total Time

- Task 1: 15 min
- Task 2: 2h 30min (all subtasks)
- Task 3: 30 min
- Task 4: 10 min
- Task 5: 45 min
- Task 6: 20 min
- Testing: 30 min

**Total**: ~5 hours of focused work

---

**Status**: Ready to implement
**Blocking Issues**: None (API key can be tested during Task 5)
**Next Review**: After Task 2.4 completion (API client ready)
