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
        project_root = os.path.dirname(os.path.dirname(current_dir))
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
