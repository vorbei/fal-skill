#!/usr/bin/env python3
"""
fal.ai API CLI wrapper
Handles model execution and discovery
"""

import sys
import json
import argparse
from lib.api_client import FalAPIClient
from lib.discovery import ModelDiscovery
from lib.models import ModelRegistry
from lib.adapter import ResponseAdapter

def handle_run(args, client):
    """Handle run command"""
    endpoint_id = args.endpoint_id
    input_data = json.loads(args.input_json)

    result = client.run_model(endpoint_id, input_data)
    print(json.dumps(result, indent=2))

def handle_generate(args, client):
    """Handle generate command - simplified interface for image generation"""
    endpoint_id = args.model

    # Build input from args
    input_data = {
        "prompt": args.prompt,
        "image_size": args.size,
        "num_inference_steps": args.steps,
        "guidance_scale": args.guidance,
        "num_images": 1
    }

    # Remove None values
    input_data = {k: v for k, v in input_data.items() if v is not None}

    # Execute via API client
    result = client.run_model(endpoint_id, input_data)

    # Extract URL with adapter
    adapter = ResponseAdapter()
    url = adapter.extract_result(result, endpoint_id)

    if not url:
        print(json.dumps({"error": "Could not extract URL from response"}), file=sys.stderr)
        sys.exit(1)

    # Return structured result
    output = {
        "url": url,
        "model": endpoint_id,
        "prompt": input_data.get("prompt")
    }

    print(json.dumps(output))

def handle_discover(args, discovery):
    """Handle discover command"""
    if args.category:
        models = discovery.discover_by_category(args.category)
    else:
        models = discovery.discover_all_models()

    print(json.dumps(models, indent=2))

def handle_refresh(args, discovery):
    """Handle refresh command"""
    print("Refreshing model cache...")
    models = discovery.discover_all_models(force_refresh=True)
    print(f"Refreshed cache with {len(models)} models")

def handle_validate(args, client):
    """Handle validate command"""
    if client.validate_key():
        print("✓ API key is valid")
        sys.exit(0)
    else:
        print("✗ API key is invalid")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='fal.ai API CLI wrapper')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Execute a model with raw JSON input')
    run_parser.add_argument('endpoint_id', help='Model endpoint ID (e.g., fal-ai/flux/dev)')
    run_parser.add_argument('input_json', help='JSON input data')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate image with simplified interface')
    generate_parser.add_argument('--model', required=True, help='Model endpoint ID')
    generate_parser.add_argument('--prompt', required=True, help='Text prompt for image generation')
    generate_parser.add_argument('--size', default='square_hd', help='Image size (default: square_hd)')
    generate_parser.add_argument('--steps', type=int, help='Number of inference steps')
    generate_parser.add_argument('--guidance', type=float, help='Guidance scale')

    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover available models')
    discover_parser.add_argument('category', nargs='?', help='Model category to filter by')

    # Refresh command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh model cache')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate API key')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = FalAPIClient()
        discovery = ModelDiscovery(client)
        registry = ModelRegistry(discovery)

        if args.command == 'run':
            handle_run(args, client)
        elif args.command == 'generate':
            handle_generate(args, client)
        elif args.command == 'discover':
            handle_discover(args, discovery)
        elif args.command == 'refresh':
            handle_refresh(args, discovery)
        elif args.command == 'validate':
            handle_validate(args, client)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
