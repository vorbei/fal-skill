import os
import json
import urllib.request
import urllib.parse
import re
import time
from urllib.error import HTTPError, URLError
from typing import Dict, Any, Optional

class FalAPIClient:
    """HTTP client for fal.ai API (generation + discovery)"""

    BASE_URL = "https://queue.fal.run"
    DISCOVERY_URL = "https://api.fal.ai"
    TIMEOUT = 30  # seconds

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

        # Limit input size to prevent memory issues
        input_json = json.dumps({"input": input_data})
        if len(input_json) > 1_000_000:  # 1MB limit
            raise ValueError("Input data too large (>1MB)")

        def _execute():
            url = f"{self.BASE_URL}/{endpoint_id}"
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            data = input_json.encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')

            try:
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
                    return json.loads(response.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                raise Exception(f"API Error {e.code}: {error_body}")

        return self._retry_with_backoff(_execute)

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

        def _execute():
            try:
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as response:
                    return json.loads(response.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                raise Exception(f"API Discovery Error {e.code}: {error_body}")

        return self._retry_with_backoff(_execute)

    def validate_key(self) -> bool:
        """Test if API key is valid by making a simple discovery request"""
        try:
            result = self.discover_models(limit=1)
            return "models" in result
        except Exception:
            return False
