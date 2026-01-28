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

def handle_video(args, client):
    """
    Handle video generation command (text-to-video or image-to-video)
    Uses async workflow for long operations (30-120s)
    """
    import time
    from lib.logging_config import setup_logging

    logger = setup_logging(__name__)
    endpoint_id = args.model

    # Build input data
    input_data = {}

    if args.prompt:
        input_data["prompt"] = args.prompt
    if hasattr(args, 'image_url') and args.image_url:
        input_data["image_url"] = args.image_url
    if args.duration:
        input_data["duration"] = args.duration
    if args.aspect_ratio:
        input_data["aspect_ratio"] = args.aspect_ratio
    if args.negative_prompt:
        input_data["negative_prompt"] = args.negative_prompt

    # Video generation is slow (30-120s), use async workflow
    logger.info(f"⏳ Submitting video generation (ETA: 30-120s)")
    request_id = client.submit_async(endpoint_id, input_data)

    logger.info(f"📋 Request ID: {request_id}")
    logger.info(f"⏳ Generating video... (this may take 1-2 minutes)")

    # Poll for status with progress indication
    start_time = time.time()
    max_wait_time = 180  # 3 minutes timeout

    while time.time() - start_time < max_wait_time:
        status = client.check_status(endpoint_id, request_id)

        if status.get("status") == "COMPLETED":
            break
        elif status.get("status") == "FAILED":
            error = status.get("error", "Unknown error")
            print(json.dumps({"error": f"Video generation failed: {error}"}), file=sys.stderr)
            sys.exit(1)

        elapsed = int(time.time() - start_time)
        logger.info(f"⏳ Status: {status.get('status', 'IN_QUEUE')} ({elapsed}s elapsed)")

        # Log any progress messages
        for log in status.get("logs", []):
            if "message" in log:
                logger.info(f"📝 {log['message']}")

        time.sleep(5)  # Check every 5 seconds

    if time.time() - start_time >= max_wait_time:
        print(json.dumps({"error": "Video generation timed out after 3 minutes"}), file=sys.stderr)
        sys.exit(1)

    # Retrieve final result
    result = client.get_result(endpoint_id, request_id)

    # Extract URL with adapter
    adapter = ResponseAdapter()
    video_url = adapter.extract_result(result, endpoint_id)

    if not video_url:
        print(json.dumps({"error": "Could not extract video URL from response"}), file=sys.stderr)
        sys.exit(1)

    generation_time = int(time.time() - start_time)
    logger.info(f"✅ Video generated in {generation_time}s")

    # Return structured result
    output = {
        "url": video_url,
        "model": endpoint_id,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "generation_time": generation_time
    }

    print(json.dumps(output))

def handle_edit(args, client):
    """
    Handle image editing command (Fibo Edit suite)
    Fast operations, uses blocking mode
    """
    endpoint_id = args.model

    # Build input data
    input_data = {
        "image_url": args.image_url
    }

    if hasattr(args, 'prompt') and args.prompt:
        input_data["prompt"] = args.prompt
    if hasattr(args, 'strength') and args.strength is not None:
        input_data["strength"] = args.strength

    # Add operation-specific parameters
    if hasattr(args, 'lighting_prompt') and args.lighting_prompt:
        input_data["lighting_prompt"] = args.lighting_prompt
    if hasattr(args, 'season') and args.season:
        input_data["season"] = args.season
    if hasattr(args, 'style_prompt') and args.style_prompt:
        input_data["style_prompt"] = args.style_prompt

    # Editing is fast (<10s), use blocking mode
    result = client.run_model(endpoint_id, input_data)

    # Extract URL with adapter
    adapter = ResponseAdapter()
    image_url = adapter.extract_result(result, endpoint_id)

    if not image_url:
        print(json.dumps({"error": "Could not extract image URL from response"}), file=sys.stderr)
        sys.exit(1)

    # Return structured result
    output = {
        "url": image_url,
        "model": endpoint_id,
        "operation": args.operation if hasattr(args, 'operation') else None
    }

    print(json.dumps(output))

def handle_upscale(args, client):
    """
    Handle upscale command for images or videos
    Video upscaling uses async workflow (30-60s)
    """
    import time
    from lib.logging_config import setup_logging

    logger = setup_logging(__name__)
    endpoint_id = args.model

    # Build input data
    input_data = {}

    if hasattr(args, 'image_url') and args.image_url:
        input_data["image_url"] = args.image_url
    if hasattr(args, 'video_url') and args.video_url:
        input_data["video_url"] = args.video_url
    if args.scale:
        input_data["scale"] = args.scale
    if hasattr(args, 'creativity') and args.creativity is not None:
        input_data["creativity"] = args.creativity

    # Video upscaling is slow, use async
    if args.video_url:
        logger.info(f"⏳ Submitting video upscale (ETA: 30-60s)")
        request_id = client.submit_async(endpoint_id, input_data)

        start_time = time.time()
        max_wait_time = 180  # 3 minutes timeout

        while time.time() - start_time < max_wait_time:
            status = client.check_status(endpoint_id, request_id)

            if status.get("status") == "COMPLETED":
                break
            elif status.get("status") == "FAILED":
                error = status.get("error", "Unknown error")
                print(json.dumps({"error": f"Upscale failed: {error}"}), file=sys.stderr)
                sys.exit(1)

            elapsed = int(time.time() - start_time)
            logger.info(f"⏳ Upscaling ({elapsed}s elapsed)")
            time.sleep(5)

        if time.time() - start_time >= max_wait_time:
            print(json.dumps({"error": "Upscale timed out after 3 minutes"}), file=sys.stderr)
            sys.exit(1)

        result = client.get_result(endpoint_id, request_id)
        logger.info(f"✅ Video upscaled in {int(time.time() - start_time)}s")
    else:
        # Image upscaling is faster, blocking is fine
        result = client.run_model(endpoint_id, input_data)

    # Extract URL with adapter
    adapter = ResponseAdapter()
    result_url = adapter.extract_result(result, endpoint_id)

    if not result_url:
        print(json.dumps({"error": "Could not extract URL from response"}), file=sys.stderr)
        sys.exit(1)

    # Return structured result
    output = {
        "url": result_url,
        "model": endpoint_id,
        "scale": args.scale,
        "type": "video" if args.video_url else "image"
    }

    print(json.dumps(output))

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

    # Video command
    video_parser = subparsers.add_parser('video', help='Video generation (text-to-video or image-to-video)')
    video_parser.add_argument('--model', required=True, help='Model endpoint ID')
    video_parser.add_argument('--prompt', help='Text prompt for text-to-video')
    video_parser.add_argument('--image-url', help='Image URL for image-to-video')
    video_parser.add_argument('--duration', type=int, default=5, choices=[5, 10], help='Video duration in seconds')
    video_parser.add_argument('--aspect-ratio', default='16:9',
        choices=['16:9', '9:16', '1:1', '4:3', '3:4'], help='Video aspect ratio')
    video_parser.add_argument('--negative-prompt', help='What to avoid in the video')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Advanced image editing (Fibo Edit suite)')
    edit_parser.add_argument('--model', required=True, help='Model endpoint ID')
    edit_parser.add_argument('--image-url', required=True, help='Image URL to edit')
    edit_parser.add_argument('--operation', required=True,
        choices=['colorize', 'relight', 'reseason', 'restore', 'restyle',
                 'inpaint', 'outpaint', 'add-object', 'remove-object'],
        help='Editing operation to perform')
    edit_parser.add_argument('--prompt', help='Editing instruction prompt')
    edit_parser.add_argument('--strength', type=float, default=0.8, help='Effect strength (0-1)')
    edit_parser.add_argument('--lighting-prompt', help='Lighting description for relight operation')
    edit_parser.add_argument('--season', choices=['spring', 'summer', 'fall', 'winter'],
        help='Target season for reseason operation')
    edit_parser.add_argument('--style-prompt', help='Style description for restyle operation')

    # Upscale command
    upscale_parser = subparsers.add_parser('upscale', help='Image or video upscaling')
    upscale_parser.add_argument('--model', required=True, help='Model endpoint ID')
    upscale_parser.add_argument('--image-url', help='Image URL to upscale')
    upscale_parser.add_argument('--video-url', help='Video URL to upscale')
    upscale_parser.add_argument('--scale', type=int, default=2, choices=[2, 4, 8],
        help='Upscale factor')
    upscale_parser.add_argument('--creativity', type=float, default=0.35,
        help='AI enhancement level (0-1)')

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
        elif args.command == 'video':
            handle_video(args, client)
        elif args.command == 'edit':
            handle_edit(args, client)
        elif args.command == 'upscale':
            handle_upscale(args, client)
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
