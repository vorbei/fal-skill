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
            return {}

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
                "candidate_path": None,
                "candidate_successes": 0
            }

        pattern = self.patterns[endpoint_id]
        pattern["success_count"] += 1

        if path == pattern.get("learned_path"):
            # Already learned, just increment
            return

        # Check if this is a new candidate or set new candidate
        if pattern.get("candidate_path") is None:
            # First time seeing a pattern for this endpoint
            pattern["candidate_path"] = path
            pattern["candidate_successes"] = 1
        elif path == pattern.get("candidate_path"):
            # Same candidate path, increment
            pattern["candidate_successes"] += 1

            # Promote to learned if confidence threshold met
            if pattern["candidate_successes"] >= self.CONFIDENCE_THRESHOLD:
                pattern["learned_path"] = path
                pattern["confidence"] = "high"
                pattern["last_updated"] = datetime.utcnow().isoformat() + "Z"
                self._save_patterns()
        else:
            # Different path than candidate - restart with new candidate
            pattern["candidate_path"] = path
            pattern["candidate_successes"] = 1

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
