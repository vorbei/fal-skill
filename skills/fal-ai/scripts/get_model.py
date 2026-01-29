#!/usr/bin/env python3
"""
Get recommended model from curated.yaml by category.

Usage:
    python get_model.py <category> [--list] [--all] [--tier <cost_tier>]

Examples:
    python get_model.py lipsync-avatar              # Get recommended model
    python get_model.py image-editing --list        # List all models in category
    python get_model.py tts --all                   # Get all model details as JSON
    python get_model.py text-to-image --tier premium  # Get premium tier model
"""

import sys
import json
from pathlib import Path

import yaml


def load_curated():
    """Load models.yaml from references directory"""
    script_dir = Path(__file__).parent
    # Try references/models.yaml first (skill package layout)
    curated_path = script_dir.parent / "references" / "models.yaml"

    # Fallback to models/curated.yaml (development layout)
    if not curated_path.exists():
        curated_path = script_dir.parent / "models" / "curated.yaml"

    if not curated_path.exists():
        print(f"Error: models.yaml not found", file=sys.stderr)
        sys.exit(1)

    with open(curated_path) as f:
        return yaml.safe_load(f)


def get_recommended(category: str, data: dict, cost_tier: str = None) -> str:
    """Get the recommended (or first) model for a category, optionally filtered by cost tier"""
    categories = data.get("categories", {})

    if category not in categories:
        print(f"Error: Category '{category}' not found", file=sys.stderr)
        print(f"Available: {', '.join(categories.keys())}", file=sys.stderr)
        sys.exit(1)

    models = categories[category]

    # If cost_tier specified, filter models
    if cost_tier:
        tier_models = [m for m in models if m.get("cost_tier") == cost_tier]
        if tier_models:
            # Return recommended in tier, or first in tier
            for model in tier_models:
                if model.get("recommended", False):
                    return model["endpoint_id"]
            return tier_models[0]["endpoint_id"]

    # Find recommended model
    for model in models:
        if model.get("recommended", False):
            return model["endpoint_id"]

    # Fall back to first model
    if models:
        return models[0]["endpoint_id"]

    print(f"Error: No models in category '{category}'", file=sys.stderr)
    sys.exit(1)


def list_models(category: str, data: dict) -> list:
    """List all model endpoint IDs in a category"""
    categories = data.get("categories", {})

    if category not in categories:
        print(f"Error: Category '{category}' not found", file=sys.stderr)
        sys.exit(1)

    return [m["endpoint_id"] for m in categories[category]]


def get_all_models(category: str, data: dict) -> list:
    """Get all model details in a category"""
    categories = data.get("categories", {})

    if category not in categories:
        print(f"Error: Category '{category}' not found", file=sys.stderr)
        sys.exit(1)

    return categories[category]


def main():
    if len(sys.argv) < 2:
        print("Usage: python get_model.py <category> [--list] [--all] [--tier <cost_tier>]")
        print("\nCategories:")
        data = load_curated()
        for cat in data.get("categories", {}).keys():
            print(f"  {cat}")
        print("\nCost tiers: budget, standard, premium")
        sys.exit(1)

    category = sys.argv[1]
    data = load_curated()

    # Parse --tier option
    cost_tier = None
    if "--tier" in sys.argv:
        tier_idx = sys.argv.index("--tier")
        if tier_idx + 1 < len(sys.argv):
            cost_tier = sys.argv[tier_idx + 1]

    if "--list" in sys.argv:
        models = list_models(category, data)
        for m in models:
            print(m)
    elif "--all" in sys.argv:
        models = get_all_models(category, data)
        print(json.dumps(models, indent=2))
    else:
        model = get_recommended(category, data, cost_tier)
        print(model)


if __name__ == "__main__":
    main()
