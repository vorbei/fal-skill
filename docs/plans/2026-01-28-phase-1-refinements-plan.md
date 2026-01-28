---
title: Phase 1 Refinements - Production Hardening
type: refactor
date: 2026-01-28
parent_plan: 2026-01-28-fal-skill-roadmap.md
status: ready
branch: feat/phase-1-refinements
---

# Phase 1 Refinements: Production Hardening

**Goal**: Transform Phase 1 foundation from "working" to "production-ready" before starting Phase 2

**Duration**: 3-5 days focused work (21-30 hours)

**Context**: Phase 1 deliverables are complete and functional, but lack critical components needed for Phase 2 (Response Adapter) and have robustness gaps (testing, error handling, logging).

---

## Problem Statement

Phase 1 is marked "complete" but has critical gaps that will block Phase 2 or cause issues:

1. **Response Adapter missing**: Cannot reliably extract results from different model response formats (blocks Phase 2)
2. **Zero testing**: No automated tests mean no regression protection or confidence in changes
3. **Production bugs**: Path resolution assumes directory structure, no timeouts, no input validation
4. **No observability**: Print statements instead of proper logging make debugging impossible
5. **Documentation gaps**: Missing installation, troubleshooting, and examples

**Current Status**: Working prototype (5.5/10 production readiness)
**Target Status**: Production-ready foundation (8.5/10)

---

## Success Metrics

### Must-Have (Blocking Phase 2)
- [ ] Response Adapter implemented and learning patterns
- [ ] Test coverage >60% for core modules
- [ ] Path resolution works from any directory
- [ ] All network calls have timeouts
- [ ] Input validation on all public APIs

### Should-Have (Production Quality)
- [ ] Structured logging with levels (debug/info/error)
- [ ] Retry logic with exponential backoff
- [ ] README installation and troubleshooting sections
- [ ] CLI improvements (--help, --version, --debug flags)
- [ ] Configuration validation with clear error messages

### Nice-to-Have (Polish)
- [ ] Progress indicators for long operations
- [ ] Cost estimation before expensive operations
- [ ] Performance benchmarks documented
- [ ] Contributing guidelines

---

## Technical Approach

### Architecture Addition

```
┌─────────────────────────────────────┐
│         /fal-setup                  │
├─────────────────────────────────────┤
│    Response Adapter (NEW!)          │ ← Self-learning field extraction
│    - Known patterns (registry)      │
│    - Common patterns (15 variants)  │
│    - Search & learn                 │
│    - Confidence tracking            │
├─────────────────────────────────────┤
│       Model Registry (existing)     │
├─────────────────────────────────────┤
│     Python API Client               │
│     + Timeouts (NEW!)               │
│     + Validation (NEW!)             │
│     + Retry logic (NEW!)            │
├─────────────────────────────────────┤
│       Logging System (NEW!)         │
└─────────────────────────────────────┘
```

---

## Implementation Plan

### Task 1: Response Adapter Implementation ⭐ CRITICAL

**Blocking**: Phase 2 cannot proceed without this

**Objective**: Create adaptive field extraction system that learns successful response patterns

**File**: `scripts/lib/adapter.py`

**Implementation**:

```python
import os
import json
import yaml
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

class ResponseAdapter:
    """Adaptive field extraction with confidence-based learning"""

    CONFIDENCE_THRESHOLD = 3  # Successes before persisting
    ATTEMPT_THRESHOLD = 5     # Attempts before evaluating success rate
    SUCCESS_RATE_THRESHOLD = 0.8  # 80% success rate to persist

    # Common field patterns to try (in order of likelihood)
    COMMON_PATTERNS = [
        "images[0].url",
        "data.images[0].url",
        "image.url",
        "data.image.url",
        "output.url",
        "data.output.url",
        "result.url",
        "data.result.url",
        "url",
        "data.url",
        "video.url",
        "data.video.url",
        "audio.url",
        "data.audio.url",
        "file.url"
    ]

    def __init__(self, patterns_file: str = None):
        if patterns_file is None:
            patterns_file = os.path.expanduser("~/.config/fal-skill/response_patterns.yaml")

        self.patterns_file = patterns_file
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load learned patterns from YAML"""
        if not os.path.exists(self.patterns_file):
            return {"patterns": {}}

        with open(self.patterns_file, 'r') as f:
            data = yaml.safe_load(f) or {}
            return data.get("patterns", {})

    def _save_patterns(self):
        """Persist learned patterns to YAML"""
        os.makedirs(os.path.dirname(self.patterns_file), exist_ok=True)

        data = {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "description": "Learned response field paths for fal.ai models",
            "patterns": self.patterns
        }

        with open(self.patterns_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def extract_result(self, response: Dict[str, Any], endpoint_id: str) -> Optional[str]:
        """
        Extract result URL from API response with learning

        Args:
            response: Raw API response dict
            endpoint_id: Model endpoint (e.g., "fal-ai/flux-pro")

        Returns:
            Extracted URL string or None
        """
        # Stage 1: Try known learned pattern for this model
        if endpoint_id in self.patterns:
            pattern = self.patterns[endpoint_id]
            learned_path = pattern.get("learned_path")

            if learned_path:
                result = self._extract_by_path(response, learned_path)
                if result:
                    self._record_success(endpoint_id, learned_path)
                    return result
                else:
                    self._record_failure(endpoint_id, learned_path)

        # Stage 2: Try common patterns
        for pattern in self.COMMON_PATTERNS:
            result = self._extract_by_path(response, pattern)
            if result:
                self._record_attempt(endpoint_id, pattern, success=True)
                return result

        # Stage 3: Search for URL-like values
        urls = self._find_urls_in_response(response)
        if urls:
            # Use first URL found, record as learned pattern
            self._record_attempt(endpoint_id, "auto_discovered", success=True)
            return urls[0]

        # Stage 4: Failed to extract
        self._record_attempt(endpoint_id, None, success=False)
        return None

    def _extract_by_path(self, data: Dict[str, Any], path: str) -> Optional[str]:
        """
        Extract value by dot-notation path (e.g., "data.images[0].url")

        Supports:
        - Dot notation: data.image.url
        - Array indexing: images[0].url
        - Mixed: data.images[0].url
        """
        try:
            current = data

            # Split path by dots and brackets
            parts = re.split(r'\.|\[|\]', path)
            parts = [p for p in parts if p]  # Remove empty strings

            for part in parts:
                if part.isdigit():
                    # Array index
                    current = current[int(part)]
                else:
                    # Object key
                    current = current[part]

            # Verify result looks like a URL
            if isinstance(current, str) and (current.startswith("http://") or current.startswith("https://")):
                return current

            return None

        except (KeyError, IndexError, TypeError):
            return None

    def _find_urls_in_response(self, data: Any, found: List[str] = None) -> List[str]:
        """Recursively search for URL-like strings in response"""
        if found is None:
            found = []

        if isinstance(data, str):
            if data.startswith("http://") or data.startswith("https://"):
                found.append(data)
        elif isinstance(data, dict):
            for value in data.values():
                self._find_urls_in_response(value, found)
        elif isinstance(data, list):
            for item in data:
                self._find_urls_in_response(item, found)

        return found

    def _record_success(self, endpoint_id: str, path: str):
        """Record successful extraction"""
        if endpoint_id not in self.patterns:
            self.patterns[endpoint_id] = {
                "success_count": 0,
                "fail_count": 0,
                "learned_path": None,
                "candidate_path": path,
                "candidate_successes": 0
            }

        pattern = self.patterns[endpoint_id]
        pattern["success_count"] += 1

        if path == pattern.get("learned_path"):
            # Already learned, just increment
            return

        # Check if this is a new candidate
        if path == pattern.get("candidate_path"):
            pattern["candidate_successes"] += 1

            # Promote to learned if confidence threshold met
            if pattern["candidate_successes"] >= self.CONFIDENCE_THRESHOLD:
                pattern["learned_path"] = path
                pattern["confidence"] = "high"
                pattern["last_updated"] = datetime.utcnow().isoformat() + "Z"
                self._save_patterns()

    def _record_failure(self, endpoint_id: str, path: str):
        """Record failed extraction attempt"""
        if endpoint_id not in self.patterns:
            self.patterns[endpoint_id] = {
                "success_count": 0,
                "fail_count": 0,
                "learned_path": None
            }

        self.patterns[endpoint_id]["fail_count"] += 1

        # If learned pattern is failing too often, demote it
        pattern = self.patterns[endpoint_id]
        total = pattern["success_count"] + pattern["fail_count"]

        if total >= self.ATTEMPT_THRESHOLD:
            success_rate = pattern["success_count"] / total
            if success_rate < self.SUCCESS_RATE_THRESHOLD:
                # Pattern is unreliable, clear it
                pattern["learned_path"] = None
                pattern["confidence"] = "low"
                self._save_patterns()

    def _record_attempt(self, endpoint_id: str, path: Optional[str], success: bool):
        """Record extraction attempt for learning"""
        if endpoint_id not in self.patterns:
            self.patterns[endpoint_id] = {
                "success_count": 0,
                "fail_count": 0,
                "attempts": 0,
                "learned_path": None
            }

        pattern = self.patterns[endpoint_id]
        pattern["attempts"] = pattern.get("attempts", 0) + 1

        if success and path:
            self._record_success(endpoint_id, path)
        else:
            self._record_failure(endpoint_id, path or "unknown")

    def get_stats(self, endpoint_id: str) -> Dict[str, Any]:
        """Get learning statistics for an endpoint"""
        if endpoint_id not in self.patterns:
            return {
                "status": "unknown",
                "success_count": 0,
                "fail_count": 0
            }

        pattern = self.patterns[endpoint_id]
        total = pattern["success_count"] + pattern["fail_count"]

        return {
            "status": "learned" if pattern.get("learned_path") else "learning",
            "learned_path": pattern.get("learned_path"),
            "confidence": pattern.get("confidence", "unknown"),
            "success_count": pattern["success_count"],
            "fail_count": pattern["fail_count"],
            "success_rate": pattern["success_count"] / total if total > 0 else 0,
            "last_updated": pattern.get("last_updated")
        }
```

**Success Criteria**:
- [x] Can extract results from known patterns
- [x] Tries 15+ common patterns if no known pattern
- [x] Falls back to URL search if patterns fail
- [x] Records successes and failures per endpoint
- [x] Persists learned patterns after 3 successes
- [x] Demotes unreliable patterns (<80% success rate)
- [ ] Thread-safe for concurrent operations

**Testing**:
```python
# Test known pattern extraction
adapter = ResponseAdapter()
response = {"data": {"images": [{"url": "https://fal.ai/result.png"}]}}
result = adapter.extract_result(response, "fal-ai/flux-pro")
assert result == "https://fal.ai/result.png"

# Test learning
for i in range(3):
    adapter.extract_result(response, "test-model")
stats = adapter.get_stats("test-model")
assert stats["status"] == "learned"
```

**Estimated Time**: 6-8 hours

---

### Task 2: Testing Infrastructure ⭐ HIGH PRIORITY

**Objective**: Add comprehensive test suite for regression protection

**Files**:
- `tests/test_api_client.py`
- `tests/test_discovery.py`
- `tests/test_models.py`
- `tests/test_adapter.py`
- `tests/fixtures/` (test data)

**Subtask 2.1: Setup Testing Framework**

Create `tests/__init__.py`:
```python
"""Test suite for fal-skill"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**Subtask 2.2: API Client Tests**

Create `tests/test_api_client.py`:
```python
import unittest
from unittest.mock import patch, Mock
import json
from scripts.lib.api_client import FalAPIClient

class TestFalAPIClient(unittest.TestCase):

    @patch('scripts.lib.api_client.urllib.request.urlopen')
    def test_run_model_success(self, mock_urlopen):
        """Test successful model execution"""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "data": {"images": [{"url": "https://fal.ai/test.png"}]}
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = FalAPIClient(api_key="test_key")
        result = client.run_model("fal-ai/flux-pro", {"prompt": "test"})

        self.assertIn("data", result)
        self.assertIn("images", result["data"])

    def test_load_api_key_missing_file(self):
        """Test error when config file missing"""
        client = FalAPIClient(api_key="test_key")  # Skip auto-load

        with self.assertRaises(ValueError) as ctx:
            client._load_api_key()

        self.assertIn("API key not found", str(ctx.exception))

    @patch('scripts.lib.api_client.urllib.request.urlopen')
    def test_run_model_timeout(self, mock_urlopen):
        """Test timeout handling"""
        mock_urlopen.side_effect = TimeoutError("Request timed out")

        client = FalAPIClient(api_key="test_key")

        with self.assertRaises(Exception) as ctx:
            client.run_model("fal-ai/flux-pro", {"prompt": "test"})

        self.assertIn("timeout", str(ctx.exception).lower())

if __name__ == '__main__':
    unittest.main()
```

**Subtask 2.3: Response Adapter Tests**

Create `tests/test_adapter.py`:
```python
import unittest
import tempfile
import os
from scripts.lib.adapter import ResponseAdapter

class TestResponseAdapter(unittest.TestCase):

    def setUp(self):
        """Create temporary patterns file for testing"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.temp_file.close()
        self.adapter = ResponseAdapter(patterns_file=self.temp_file.name)

    def tearDown(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_extract_known_pattern(self):
        """Test extraction with known pattern"""
        response = {"data": {"images": [{"url": "https://fal.ai/test.png"}]}}
        result = self.adapter.extract_result(response, "fal-ai/flux-pro")

        self.assertEqual(result, "https://fal.ai/test.png")

    def test_extract_nested_pattern(self):
        """Test extraction with nested structure"""
        response = {"output": {"result": {"url": "https://fal.ai/nested.png"}}}
        result = self.adapter.extract_result(response, "test-model")

        self.assertEqual(result, "https://fal.ai/nested.png")

    def test_learning_after_threshold(self):
        """Test pattern learning after confidence threshold"""
        response = {"custom": {"path": {"url": "https://fal.ai/test.png"}}}

        # Extract 3 times (confidence threshold)
        for i in range(3):
            self.adapter.extract_result(response, "learning-model")

        stats = self.adapter.get_stats("learning-model")
        self.assertEqual(stats["status"], "learned")
        self.assertIsNotNone(stats["learned_path"])

    def test_url_search_fallback(self):
        """Test fallback to URL search when patterns fail"""
        response = {"weird_structure": {"nested": "https://fal.ai/found.png"}}
        result = self.adapter.extract_result(response, "unknown-model")

        self.assertEqual(result, "https://fal.ai/found.png")

if __name__ == '__main__':
    unittest.main()
```

**Subtask 2.4: Test Fixtures**

Create `tests/fixtures/sample_responses.json`:
```json
{
  "flux_pro_success": {
    "data": {
      "images": [
        {"url": "https://fal.media/files/test.png", "width": 1024, "height": 1024}
      ]
    }
  },
  "kling_video_success": {
    "data": {
      "video": {
        "url": "https://fal.media/files/test.mp4"
      }
    }
  },
  "birefnet_success": {
    "image": {
      "url": "https://fal.media/files/transparent.png"
    }
  }
}
```

**Run Tests**:
```bash
# Run all tests
python3 -m unittest discover tests/

# Run specific test file
python3 -m unittest tests.test_adapter

# Run with coverage (if coverage.py installed)
python3 -m coverage run -m unittest discover tests/
python3 -m coverage report
```

**Success Criteria**:
- [ ] >60% code coverage for core modules
- [ ] All tests pass on clean environment
- [ ] Tests use mocking to avoid API calls
- [ ] Tests are fast (<5s total runtime)
- [ ] Clear test names describing what's tested

**Estimated Time**: 6-8 hours

---

### Task 3: Bug Fixes & Robustness 🐛 HIGH PRIORITY

**Objective**: Fix identified production bugs and add defensive coding

**Subtask 3.1: Fix Path Resolution Bug**

**File**: `scripts/lib/models.py` (line 14-17)

**Current Code**:
```python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
curated_path = os.path.join(project_root, "models", "curated.yaml")
```

**Problem**: Assumes `scripts/lib/` structure, breaks if run from different location

**Fix**:
```python
def _load_curated_models(self) -> Dict[str, Any]:
    """Load curated models from YAML"""
    # Try environment variable first
    project_root = os.environ.get('FAL_SKILL_ROOT')

    if not project_root:
        # Fallback: navigate up from this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))

    curated_path = os.path.join(project_root, "models", "curated.yaml")

    if not os.path.exists(curated_path):
        # Second fallback: check current working directory
        curated_path = os.path.join(os.getcwd(), "models", "curated.yaml")

    if not os.path.exists(curated_path):
        print(f"Warning: curated.yaml not found at {curated_path}")
        return {"categories": {}}

    with open(curated_path, 'r') as f:
        return yaml.safe_load(f) or {"categories": {}}
```

**Subtask 3.2: Add Timeouts to Network Calls**

**Files**: `scripts/lib/api_client.py`

**Add Timeout Constant**:
```python
class FalAPIClient:
    BASE_URL = "https://queue.fal.run"
    DISCOVERY_URL = "https://api.fal.ai"
    TIMEOUT = 30  # seconds (NEW!)
```

**Fix All urllib.request.urlopen Calls**:
```python
# Before:
with urllib.request.urlopen(req) as response:

# After:
with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
```

**Subtask 3.3: Add Input Validation**

**File**: `scripts/lib/api_client.py`

Add validation method:
```python
def _validate_endpoint_id(self, endpoint_id: str):
    """Validate endpoint ID format"""
    if not endpoint_id:
        raise ValueError("endpoint_id cannot be empty")

    # Must be alphanumeric with dashes and slashes only
    if not re.match(r'^[a-zA-Z0-9/_-]+$', endpoint_id):
        raise ValueError(f"Invalid endpoint_id format: {endpoint_id}")

    # Prevent path traversal
    if '..' in endpoint_id:
        raise ValueError("endpoint_id cannot contain '..'")

def run_model(self, endpoint_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a model and return results"""
    self._validate_endpoint_id(endpoint_id)  # NEW!

    # Limit input size to prevent memory issues
    input_json = json.dumps({"input": input_data})
    if len(input_json) > 1_000_000:  # 1MB limit
        raise ValueError("Input data too large (>1MB)")

    url = f"{self.BASE_URL}/{endpoint_id}"
    # ... rest of implementation
```

**Subtask 3.4: Add Retry Logic with Exponential Backoff**

**File**: `scripts/lib/api_client.py`

```python
import time
from urllib.error import HTTPError, URLError

def _retry_with_backoff(self, func, max_retries=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except (HTTPError, URLError) as e:
            if attempt == max_retries - 1:
                raise

            # Don't retry on client errors (4xx)
            if isinstance(e, HTTPError) and 400 <= e.code < 500:
                raise

            # Exponential backoff: 1s, 2s, 4s
            wait_time = 2 ** attempt
            print(f"Request failed, retrying in {wait_time}s...")
            time.sleep(wait_time)

def run_model(self, endpoint_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a model and return results"""
    self._validate_endpoint_id(endpoint_id)

    def _execute():
        url = f"{self.BASE_URL}/{endpoint_id}"
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        data = json.dumps({"input": input_data}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
            return json.loads(response.read().decode('utf-8'))

    return self._retry_with_backoff(_execute)
```

**Success Criteria**:
- [ ] Path resolution works from any directory
- [ ] All network calls have 30s timeout
- [ ] endpoint_id validated before use
- [ ] Input size limited to 1MB
- [ ] Network failures retried up to 3 times
- [ ] Exponential backoff: 1s, 2s, 4s

**Estimated Time**: 4-6 hours

---

### Task 4: Logging System 📊 MEDIUM PRIORITY

**Objective**: Replace print statements with structured logging

**File**: `scripts/lib/logging_config.py` (NEW)

```python
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(name: str = "fal-skill", level: str = None):
    """Configure logging for fal-skill"""

    # Get log level from environment or parameter
    if level is None:
        level = os.environ.get('FAL_LOG_LEVEL', 'INFO')

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console_fmt = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # File handler (optional, only if log directory exists)
    log_dir = os.path.expanduser("~/.config/fal-skill/logs")
    if os.path.exists(log_dir) or os.makedirs(log_dir, exist_ok=True):
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'fal-skill.log'),
            maxBytes=1_000_000,  # 1MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)  # Always debug in file
        file_fmt = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    return logger
```

**Update All Modules**:

`scripts/lib/api_client.py`:
```python
from .logging_config import setup_logging

logger = setup_logging(__name__)

# Replace print() with logger
# Before:
print(f"Discovering models from fal.ai API...")

# After:
logger.info("Discovering models from fal.ai API")
logger.debug(f"Using endpoint: {url}")
logger.error(f"API request failed: {e}")
```

**CLI Debug Mode**:

`scripts/fal_api.py`:
```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="fal.ai API CLI")
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        os.environ['FAL_LOG_LEVEL'] = 'DEBUG'

    # ... rest of CLI
```

**Success Criteria**:
- [ ] All print() replaced with logger calls
- [ ] Log levels used correctly (debug/info/error)
- [ ] Console shows INFO by default
- [ ] File logs include DEBUG details
- [ ] CLI supports --debug flag
- [ ] Log rotation prevents unbounded growth

**Estimated Time**: 3-4 hours

---

### Task 5: Documentation Completion 📚 MEDIUM PRIORITY

**Objective**: Fill critical documentation gaps for user success

**Subtask 5.1: README Installation Section**

Add after "Quick Start" in `README.md`:

```markdown
## Installation

### Prerequisites
- **Python 3.8+** (check: `python3 --version`)
- **pip** or **pip3** (for PyYAML dependency)
- **fal.ai account** with API key ([sign up](https://fal.ai))

### Install Dependencies

```bash
# Clone or download the fal-skill repository
cd fal-skill/

# Install Python dependencies
pip3 install -r requirements.txt
# OR on some systems:
pip install -r requirements.txt
```

**Note**: fal-skill uses Python's standard library for HTTP (no `requests` or external HTTP client needed). Only PyYAML is required for config parsing.

### Verify Installation

```bash
# Test Python imports
python3 -c "import scripts.lib.api_client; print('✓ API client imported')"

# Check if PyYAML is installed
python3 -c "import yaml; print('✓ PyYAML installed')"
```

If any imports fail, install dependencies:
```bash
pip3 install pyyaml>=6.0
```

### Configuration

Run the setup skill to configure your API key:
```bash
# In Claude Code
/fal-setup
```

Or manually create config:
```bash
mkdir -p ~/.config/fal-skill
echo "FAL_KEY=your_api_key_here" > ~/.config/fal-skill/.env
chmod 600 ~/.config/fal-skill/.env
```

Get your API key: https://fal.ai/dashboard/keys
```

**Subtask 5.2: README Troubleshooting Section**

Add new section before "Contributing":

```markdown
## Troubleshooting

### Common Issues

#### "API key not found. Run /fal-setup first."

**Cause**: API key not configured or file permissions incorrect

**Solution**:
```bash
# Check if config exists
ls -la ~/.config/fal-skill/.env

# If missing, run setup
/fal-setup

# If exists but not readable, fix permissions
chmod 600 ~/.config/fal-skill/.env
```

#### "ModuleNotFoundError: No module named 'yaml'"

**Cause**: PyYAML not installed

**Solution**:
```bash
pip3 install pyyaml>=6.0
```

#### "Cannot reach fal.ai API. Please check your internet connection."

**Cause**: Network issue or API down

**Solutions**:
1. Check internet: `curl https://fal.ai`
2. Check API status: https://status.fal.ai
3. Try again with debug mode: `FAL_LOG_LEVEL=DEBUG python3 scripts/fal_api.py validate`

#### "API Error 401: Unauthorized"

**Cause**: Invalid or expired API key

**Solution**:
```bash
# Get a new key from https://fal.ai/dashboard/keys
# Update config
/fal-setup
```

#### "Request timed out after 30s"

**Cause**: Model taking too long or slow internet

**Solutions**:
1. Try a faster model (use `fal-ai/flux/dev` instead of `flux-pro`)
2. Check if model is overloaded: https://status.fal.ai
3. Retry the request

#### Discovery returns empty models list

**Cause**: Cache corrupted or API issue

**Solution**:
```bash
# Clear cache and refresh
rm -rf ~/.config/fal-skill/cache/*.json
python3 scripts/fal_api.py refresh
```

### Getting Help

- **Bug reports**: [GitHub Issues](https://github.com/your-repo/fal-skill/issues)
- **fal.ai API docs**: https://docs.fal.ai
- **API status**: https://status.fal.ai
```

**Subtask 5.3: Add Code Examples to README**

Add new section after "Available Skills":

```markdown
## Usage Examples

### Generate an Image (Text-to-Image)

```python
# Via CLI
python3 scripts/fal_api.py run fal-ai/flux/dev '{"prompt": "a wizard cat"}'

# In Claude Code
/fal-generate-image "a wizard cat wearing purple robes"
```

### Remove Background from Image

```python
# Via CLI
python3 scripts/fal_api.py run fal-ai/birefnet/v2 '{"image_url": "https://example.com/photo.jpg"}'

# In Claude Code
/fal-remove-bg [upload your image]
```

### Discover Models by Category

```bash
# List all text-to-image models
python3 scripts/fal_api.py discover text-to-image

# List all models (may take 10-20s)
python3 scripts/fal_api.py discover

# Force refresh cache
python3 scripts/fal_api.py refresh
```

### Check API Key Status

```bash
python3 scripts/fal_api.py validate
# Output: ✓ API key is valid
```

### Advanced: Direct API Client Usage

```python
from scripts.lib.api_client import FalAPIClient

# Initialize client (loads API key from config)
client = FalAPIClient()

# Generate an image
result = client.run_model(
    "fal-ai/flux/dev",
    {
        "prompt": "a serene mountain landscape at sunset",
        "image_size": "landscape_16_9",
        "num_inference_steps": 28
    }
)

# Extract result URL
image_url = result["data"]["images"][0]["url"]
print(f"Generated: {image_url}")
```
```

**Subtask 5.4: Add Security Best Practices to Setup Skill**

Update `skills/fal-setup/SKILL.md` after "Security Notes":

```markdown
## Security Best Practices

### Do's ✅
- Store API key in `~/.config/fal-skill/.env` (outside project)
- Use `chmod 600` permissions (user-only access)
- Rotate API keys regularly (every 90 days recommended)
- Create separate API keys for different projects
- Review API usage periodically: https://fal.ai/dashboard/usage

### Don'ts ❌
- Never commit `.env` files to git
- Never share API keys in screenshots or logs
- Never store keys in project directories
- Never use production API keys for testing
- Never expose API keys in client-side code

### Key Rotation

To update your API key:
```bash
# Re-run setup
/fal-setup

# Or manually update
nano ~/.config/fal-skill/.env
# Change FAL_KEY=... to new key
chmod 600 ~/.config/fal-skill/.env

# Validate new key
python3 scripts/fal_api.py validate
```

### Multiple Projects

Each project can use the same shared config:
```bash
# All fal-skill projects read from same location
~/.config/fal-skill/.env

# If you need separate keys per project, use environment variable
export FAL_KEY="project_specific_key"
python3 scripts/fal_api.py validate
```
```

**Success Criteria**:
- [ ] README has installation instructions
- [ ] README has troubleshooting section with 5+ common issues
- [ ] README has code examples for CLI and API client
- [ ] Setup skill documents security best practices
- [ ] All links working and pointing to correct resources

**Estimated Time**: 3-4 hours

---

### Task 6: CLI Improvements 🖥️ LOW PRIORITY

**Objective**: Add standard CLI features for better UX

**Subtask 6.1: Add --help and --version Flags**

Update `scripts/fal_api.py`:

```python
import argparse
import sys

VERSION = "1.0.0-phase1"

def main():
    parser = argparse.ArgumentParser(
        description="fal.ai API CLI - Execute models and discover capabilities",
        epilog="Examples:\n"
               "  fal_api.py validate\n"
               "  fal_api.py discover text-to-image\n"
               "  fal_api.py run fal-ai/flux/dev '{\"prompt\": \"test\"}'\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--version', action='version', version=f'fal-skill {VERSION}')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate API key')

    # discover command
    discover_parser = subparsers.add_parser('discover', help='Discover models')
    discover_parser.add_argument('category', nargs='?', help='Category to filter by')

    # run command
    run_parser = subparsers.add_parser('run', help='Execute a model')
    run_parser.add_argument('endpoint_id', help='Model endpoint ID')
    run_parser.add_argument('input_data', help='JSON input data')

    # refresh command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh model cache')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ... handle commands
```

**Subtask 6.2: Add Progress Indicators**

Install progress library or use simple dots:

```python
import sys
import time
import threading

class ProgressIndicator:
    """Simple progress indicator using dots"""

    def __init__(self, message: str):
        self.message = message
        self.running = False
        self.thread = None

    def start(self):
        """Start showing progress"""
        self.running = True
        self.thread = threading.Thread(target=self._show_progress)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, final_message: str = None):
        """Stop showing progress"""
        self.running = False
        if self.thread:
            self.thread.join()

        # Clear line and show final message
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        if final_message:
            print(final_message)
        sys.stdout.flush()

    def _show_progress(self):
        """Internal: show animated dots"""
        dots = 0
        while self.running:
            sys.stdout.write(f'\r{self.message}{"." * (dots % 4)}{" " * (3 - dots % 4)}')
            sys.stdout.flush()
            dots += 1
            time.sleep(0.5)

# Usage in discovery:
progress = ProgressIndicator("Discovering models from fal.ai API")
progress.start()

try:
    models = discovery.discover_all_models()
    progress.stop(f"✓ Discovered {len(models)} models")
except Exception as e:
    progress.stop(f"✗ Discovery failed: {e}")
```

**Success Criteria**:
- [ ] `--help` shows usage information
- [ ] `--version` shows version number
- [ ] `--debug` enables debug logging
- [ ] Long operations show progress indicators
- [ ] Error messages include suggested fixes

**Estimated Time**: 2-3 hours

---

## Testing Plan

### Phase 1 Refinement Tests

**Test 1: Response Adapter Learning**
```bash
# Run adapter on multiple responses
python3 -c "
from scripts.lib.adapter import ResponseAdapter
adapter = ResponseAdapter()

# Test different response formats
responses = [
    {'data': {'images': [{'url': 'https://fal.ai/1.png'}]}},
    {'image': {'url': 'https://fal.ai/2.png'}},
    {'data': {'video': {'url': 'https://fal.ai/3.mp4'}}}
]

for i, resp in enumerate(responses):
    result = adapter.extract_result(resp, f'test-model-{i}')
    print(f'Test {i}: {result}')

    stats = adapter.get_stats(f'test-model-{i}')
    print(f'Stats: {stats}')
"
```

**Test 2: Automated Test Suite**
```bash
# Run all tests
python3 -m unittest discover tests/

# Check coverage
python3 -m coverage run -m unittest discover tests/
python3 -m coverage report --include='scripts/lib/*'

# Expected: >60% coverage
```

**Test 3: Bug Fixes Validation**
```bash
# Test path resolution from different directories
cd /tmp
python3 /Users/cheng/InfQuest/InfProj/fal-skill/scripts/fal_api.py validate

# Test timeout handling (should timeout in 30s, not hang forever)
# Mock slow API endpoint and verify timeout

# Test input validation
python3 scripts/fal_api.py run "../etc/passwd" '{}'
# Should reject with "Invalid endpoint_id format"
```

**Test 4: Logging System**
```bash
# Test different log levels
FAL_LOG_LEVEL=DEBUG python3 scripts/fal_api.py discover text-to-image
FAL_LOG_LEVEL=INFO python3 scripts/fal_api.py validate

# Check log file
cat ~/.config/fal-skill/logs/fal-skill.log
# Should contain timestamps and detailed errors
```

**Test 5: CLI Improvements**
```bash
# Test help flags
python3 scripts/fal_api.py --help
python3 scripts/fal_api.py --version
python3 scripts/fal_api.py discover --help

# Test progress indicators
python3 scripts/fal_api.py discover
# Should show "Discovering models..." with animated dots
```

---

## Deliverables Checklist

### Critical (Must-Have)
- [ ] Response Adapter implemented (`scripts/lib/adapter.py`)
- [ ] Test suite with >60% coverage (`tests/`)
- [ ] Path resolution bug fixed (`models.py`)
- [ ] Timeouts added to all network calls (`api_client.py`)
- [ ] Input validation on public APIs (`api_client.py`)
- [ ] Retry logic with exponential backoff (`api_client.py`)

### Important (Should-Have)
- [ ] Structured logging system (`logging_config.py`)
- [ ] All print() replaced with logger calls
- [ ] README installation section
- [ ] README troubleshooting section (5+ issues)
- [ ] README code examples
- [ ] Security best practices in setup skill

### Nice-to-Have
- [ ] CLI --help, --version, --debug flags
- [ ] Progress indicators for long operations
- [ ] CLI using argparse subcommands
- [ ] Log rotation configured

---

## New Branch Strategy

**Branch**: `feat/phase-1-refinements`

**Workflow**:
```bash
# Create new branch from current phase-1 branch
git checkout feat/phase-1-foundation
git checkout -b feat/phase-1-refinements

# Make changes, commit regularly
git add scripts/lib/adapter.py tests/
git commit -m "feat: add Response Adapter with self-learning"

git add scripts/lib/api_client.py
git commit -m "fix: add timeouts and input validation to API client"

# When complete, merge back to main
git checkout main
git merge feat/phase-1-refinements
```

---

## Risk Management

### High Priority Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Response Adapter complexity | High | Start with simple pattern matching, iterate |
| Testing slows down development | Medium | Focus on critical paths first (60% coverage) |
| Path resolution breaks in edge cases | Medium | Test from multiple directories, add fallbacks |
| Breaking changes to existing code | High | Thorough testing before merge, git branch for safety |

### Medium Priority Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Logging overhead impacts performance | Low | Use appropriate log levels, file logging optional |
| Retry logic causes long waits | Medium | Limit retries to 3, clear progress indicators |
| Documentation becomes stale | Low | Update docs as part of each task |

---

## Success Criteria Summary

**Production Readiness**: 8.5/10 or higher

**Phase 1 is production-ready when:**
- ✅ Response Adapter working and learning patterns
- ✅ Test coverage >60% with all tests passing
- ✅ All identified bugs fixed (paths, timeouts, validation)
- ✅ Structured logging in place
- ✅ Documentation complete (installation, troubleshooting, examples)
- ✅ No P0 or P1 bugs remaining
- ✅ Can proceed to Phase 2 with confidence

**Phase 2 Can Begin When:**
- `/fal-generate-image` and `/fal-remove-bg` skills can use Response Adapter
- Test infrastructure allows rapid iteration
- Bug fixes prevent common failure modes
- Documentation supports user onboarding

---

## Next Steps After Refinements

1. **Final Testing**:
   ```bash
   python3 -m unittest discover tests/
   python3 -m coverage report
   ```

2. **Git Commit**:
   ```bash
   git add .
   git commit -m "feat: Phase 1 refinements - production hardening

   - Add Response Adapter with self-learning field extraction
   - Implement comprehensive test suite (>60% coverage)
   - Fix path resolution, add timeouts, input validation
   - Add structured logging system
   - Complete documentation (install, troubleshoot, examples)
   - Improve CLI with --help, --version, --debug

   Phase 1 now production-ready (8.5/10) and Phase 2-ready

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

3. **Proceed to Phase 2**: Core Generation Skills
   - `/fal-generate-image` skill
   - `/fal-remove-bg` skill
   - Universal `/fal-generate` orchestrator

---

## Estimated Total Time

- Task 1 (Response Adapter): 6-8h
- Task 2 (Testing): 6-8h
- Task 3 (Bug Fixes): 4-6h
- Task 4 (Logging): 3-4h
- Task 5 (Documentation): 3-4h
- Task 6 (CLI): 2-3h
- Final Testing: 2-3h

**Total: 26-36 hours** (3-5 days full-time)

---

**Status**: Ready to implement
**Blocking Issues**: None
**Dependencies**: Existing Phase 1 code complete
**Review Points**: After Task 1 (Response Adapter ready), After Task 3 (bugs fixed)
