#!/usr/bin/env python3
"""
Fetch OpenAPI schemas for all curated models
"""

import json
import yaml
from pathlib import Path
from time import sleep
from urllib.request import urlopen
from urllib.error import URLError

def fetch_schema(endpoint_id: str) -> dict:
    """Fetch OpenAPI schema for a model endpoint"""
    url = f"https://fal.ai/api/openapi/queue/openapi.json?endpoint_id={endpoint_id}"
    try:
        with urlopen(url, timeout=30) as response:
            data = response.read()
            return json.loads(data)
    except Exception as e:
        print(f"❌ Failed to fetch schema for {endpoint_id}: {e}")
        return None

def main():
    # Load curated models
    curated_path = Path(__file__).parent.parent / "models" / "curated.yaml"
    with open(curated_path) as f:
        curated = yaml.safe_load(f)

    # Create output directory
    schemas_dir = Path(__file__).parent.parent / "outputs" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    # Collect all endpoint IDs
    endpoints = []
    for category, models in curated.get("categories", {}).items():
        for model in models:
            endpoint_id = model.get("endpoint_id")
            if endpoint_id:
                endpoints.append({
                    "endpoint_id": endpoint_id,
                    "category": category,
                    "display_name": model.get("display_name", "")
                })

    print(f"📥 Fetching schemas for {len(endpoints)} models...")

    # Fetch schemas
    results = {
        "success": [],
        "failed": []
    }

    for i, endpoint in enumerate(endpoints, 1):
        endpoint_id = endpoint["endpoint_id"]
        safe_name = endpoint_id.replace("/", "_")
        output_file = schemas_dir / f"{safe_name}.json"

        print(f"[{i}/{len(endpoints)}] Fetching {endpoint_id}...", end=" ")

        schema = fetch_schema(endpoint_id)
        if schema:
            with open(output_file, "w") as f:
                json.dump(schema, f, indent=2)
            print(f"✅ Saved to {output_file.name}")
            results["success"].append(endpoint)
        else:
            print(f"❌ Failed")
            results["failed"].append(endpoint)

        # Rate limiting
        sleep(0.5)

    # Save summary
    summary_file = schemas_dir / "_summary.json"
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Complete: {len(results['success'])}/{len(endpoints)} succeeded")
    print(f"📁 Schemas saved to: {schemas_dir}")
    if results["failed"]:
        print(f"⚠️  {len(results['failed'])} failed:")
        for ep in results["failed"]:
            print(f"   - {ep['endpoint_id']}")

if __name__ == "__main__":
    main()
