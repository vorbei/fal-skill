import os
import json
import time
from typing import List, Dict, Any, Optional
from .logging_config import setup_logging

logger = setup_logging(__name__)

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

        logger.info("Discovering models from fal.ai API")

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

        logger.info(f"Discovered {len(all_models)} models")

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
