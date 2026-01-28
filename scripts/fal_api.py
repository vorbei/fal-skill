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
