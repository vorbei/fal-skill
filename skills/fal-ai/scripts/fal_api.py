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
    Uses queue-based blocking workflow (30-120s)
    """
    from lib.logging_config import setup_logging

    logger = setup_logging(__name__)
    endpoint_id = args.model

    # Build input data
    input_data = {}

    if args.prompt:
        input_data["prompt"] = args.prompt
    if hasattr(args, 'image_url') and args.image_url:
        input_data["image_url"] = args.image_url
    if hasattr(args, 'video_url') and args.video_url:
        input_data["video_url"] = args.video_url
    if hasattr(args, 'first_frame_url') and args.first_frame_url:
        input_data["first_frame_url"] = args.first_frame_url
    if hasattr(args, 'last_frame_url') and args.last_frame_url:
        input_data["last_frame_url"] = args.last_frame_url
    if args.duration:
        input_data["duration"] = args.duration
    if args.aspect_ratio:
        input_data["aspect_ratio"] = args.aspect_ratio
    if args.negative_prompt:
        input_data["negative_prompt"] = args.negative_prompt

    logger.info("⏳ Submitting video generation via queue system")
    result = client.run_model(endpoint_id, input_data)

    # Extract URL with adapter
    adapter = ResponseAdapter()
    video_url = adapter.extract_result(result, endpoint_id)

    if not video_url:
        print(json.dumps({"error": "Could not extract video URL from response"}), file=sys.stderr)
        sys.exit(1)

    logger.info("✅ Video generated")

    # Return structured result
    output = {
        "url": video_url,
        "model": endpoint_id,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio
    }

    print(json.dumps(output))

def handle_video_edit(args, client):
    """
    Handle video editing command (video-to-video or effects)
    Uses queue-based blocking workflow
    """
    endpoint_id = args.model

    input_data = {
        "video_url": args.video_url
    }

    if args.prompt:
        input_data["prompt"] = args.prompt

    result = client.run_model(endpoint_id, input_data)

    adapter = ResponseAdapter()
    video_url = adapter.extract_result(result, endpoint_id)

    if not video_url:
        print(json.dumps({"error": "Could not extract video URL from response"}), file=sys.stderr)
        sys.exit(1)

    output = {
        "url": video_url,
        "model": endpoint_id
    }

    print(json.dumps(output))

def handle_tts(args, client):
    """Handle text-to-speech generation"""
    endpoint_id = args.model

    input_data = {
        "text": args.text
    }

    if args.voice:
        input_data["voice"] = args.voice
    if args.speed is not None:
        input_data["speed"] = args.speed
    if args.language:
        input_data["language"] = args.language
    if args.stability is not None:
        input_data["stability"] = args.stability
    if args.similarity_boost is not None:
        input_data["similarity_boost"] = args.similarity_boost

    result = client.run_model(endpoint_id, input_data)

    adapter = ResponseAdapter()
    audio_url = adapter.extract_result(result, endpoint_id)

    if not audio_url:
        print(json.dumps({"error": "Could not extract audio URL from response"}), file=sys.stderr)
        sys.exit(1)

    output = {
        "url": audio_url,
        "model": endpoint_id,
        "text": args.text
    }

    print(json.dumps(output))

def handle_music(args, client):
    """Handle music or sound effect generation"""
    endpoint_id = args.model

    input_data = {
        "prompt": args.prompt
    }

    if args.duration is not None:
        input_data["duration"] = args.duration
    if args.refinement is not None:
        input_data["refinement"] = args.refinement
    if args.creativity is not None:
        input_data["creativity"] = args.creativity
    if hasattr(args, 'lyrics') and args.lyrics is not None:
        input_data["lyrics_prompt"] = args.lyrics

    result = client.run_model(endpoint_id, input_data)

    adapter = ResponseAdapter()
    audio_url = adapter.extract_result(result, endpoint_id)

    if not audio_url:
        print(json.dumps({"error": "Could not extract audio URL from response"}), file=sys.stderr)
        sys.exit(1)

    output = {
        "url": audio_url,
        "model": endpoint_id,
        "prompt": args.prompt
    }

    print(json.dumps(output))

def handle_avatar(args, client):
    """Handle avatar lipsync generation"""
    endpoint_id = args.model

    input_data = {
        "audio_url": args.audio_url
    }

    if args.image_url:
        input_data["image_url"] = args.image_url
    if args.video_url:
        input_data["video_url"] = args.video_url
    if args.prompt:
        input_data["prompt"] = args.prompt
    if args.sound_volume is not None:
        input_data["sound_volume"] = args.sound_volume

    result = client.run_model(endpoint_id, input_data)

    adapter = ResponseAdapter()
    video_url = adapter.extract_result(result, endpoint_id)

    if not video_url:
        print(json.dumps({"error": "Could not extract video URL from response"}), file=sys.stderr)
        sys.exit(1)

    output = {
        "url": video_url,
        "model": endpoint_id
    }

    print(json.dumps(output))

def handle_transcribe(args, client):
    """Handle speech-to-text transcription"""
    endpoint_id = args.model

    input_data = {
        "audio_url": args.audio_url
    }

    if args.language:
        input_data["language"] = args.language
    if args.task:
        input_data["task"] = args.task
    if args.num_speakers is not None:
        input_data["num_speakers"] = args.num_speakers

    result = client.run_model(endpoint_id, input_data)

    output = {
        "model": endpoint_id,
        "result": result
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

    # Generic parameters
    if hasattr(args, 'prompt') and args.prompt:
        input_data["prompt"] = args.prompt
    if hasattr(args, 'strength') and args.strength is not None:
        input_data["strength"] = args.strength

    # Fibo Edit model-specific required parameters
    if 'colorize' in endpoint_id:
        input_data["color"] = args.color
    elif 'relight' in endpoint_id:
        input_data["light_direction"] = args.light_direction
        input_data["light_type"] = args.light_type
    elif 'reseason' in endpoint_id:
        input_data["season"] = args.season
    elif 'restyle' in endpoint_id:
        input_data["style"] = args.style

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
    Uses queue-based blocking workflow
    """
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

    logger.info("⏳ Submitting upscale via queue system")
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
    video_parser.add_argument('--video-url', help='Video URL for video-to-video')
    video_parser.add_argument('--first-frame-url', help='First frame image URL')
    video_parser.add_argument('--last-frame-url', help='Last frame image URL')
    video_parser.add_argument('--duration', type=int, default=None, choices=[5, 10], help='Video duration in seconds')
    video_parser.add_argument('--aspect-ratio', default=None,
        choices=['16:9', '9:16', '1:1', '4:3', '3:4'], help='Video aspect ratio')
    video_parser.add_argument('--negative-prompt', help='What to avoid in the video')

    # Video edit command
    video_edit_parser = subparsers.add_parser('video-edit', help='Video editing (video-to-video or effects)')
    video_edit_parser.add_argument('--model', required=True, help='Model endpoint ID')
    video_edit_parser.add_argument('--video-url', required=True, help='Video URL to edit')
    video_edit_parser.add_argument('--prompt', help='Editing instruction prompt')

    # TTS command
    tts_parser = subparsers.add_parser('tts', help='Text-to-speech generation')
    tts_parser.add_argument('--model', required=True, help='Model endpoint ID')
    tts_parser.add_argument('--text', required=True, help='Text to speak')
    tts_parser.add_argument('--voice', help='Voice name or ID')
    tts_parser.add_argument('--speed', type=float, help='Speech speed')
    tts_parser.add_argument('--language', help='Language code or name')
    tts_parser.add_argument('--stability', type=float, help='Voice stability (model-specific)')
    tts_parser.add_argument('--similarity-boost', type=float, help='Voice similarity boost (model-specific)')

    # Music command
    music_parser = subparsers.add_parser('music', help='Music or sound effect generation')
    music_parser.add_argument('--model', required=True, help='Model endpoint ID')
    music_parser.add_argument('--prompt', required=True, help='Music prompt')
    music_parser.add_argument('--duration', type=int, help='Duration in seconds')
    music_parser.add_argument('--refinement', type=int, help='Refinement level (model-specific)')
    music_parser.add_argument('--creativity', type=int, help='Creativity level (model-specific)')
    music_parser.add_argument('--lyrics', help='Song lyrics (required for minimax-music)')

    # Avatar command
    avatar_parser = subparsers.add_parser('avatar', help='Avatar lipsync generation')
    avatar_parser.add_argument('--model', required=True, help='Model endpoint ID')
    avatar_parser.add_argument('--audio-url', required=True, help='Audio URL for lipsync')
    avatar_parser.add_argument('--image-url', help='Image URL for avatar')
    avatar_parser.add_argument('--video-url', help='Video URL for avatar')
    avatar_parser.add_argument('--prompt', help='Optional prompt or style')
    avatar_parser.add_argument('--sound-volume', type=float, help='Sound volume (model-specific)')

    # Transcribe command
    transcribe_parser = subparsers.add_parser('transcribe', help='Speech-to-text transcription')
    transcribe_parser.add_argument('--model', required=True, help='Model endpoint ID')
    transcribe_parser.add_argument('--audio-url', required=True, help='Audio URL to transcribe')
    transcribe_parser.add_argument('--task', help='Task type (transcribe/translate)')
    transcribe_parser.add_argument('--language', help='Language hint')
    transcribe_parser.add_argument('--num-speakers', type=int, help='Speaker count for diarization')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Advanced image editing (Fibo Edit suite)')
    edit_parser.add_argument('--model', required=True, help='Model endpoint ID')
    edit_parser.add_argument('--image-url', required=True, help='Image URL to edit')
    edit_parser.add_argument('--operation',
        choices=['colorize', 'relight', 'reseason', 'restore', 'restyle',
                 'inpaint', 'outpaint', 'add-object', 'remove-object'],
        help='Editing operation to perform')
    edit_parser.add_argument('--prompt', help='Editing instruction prompt')
    edit_parser.add_argument('--strength', type=float, help='Effect strength (0-1)')
    # Fibo Edit specific parameters
    edit_parser.add_argument('--color',
        choices=['contemporary color', 'vivid color', 'black and white colors', 'sepia vintage'],
        default='contemporary color', help='Color style for colorize operation')
    edit_parser.add_argument('--light-direction',
        choices=['front', 'side', 'bottom', 'top-down'],
        default='front', help='Light direction for relight operation')
    edit_parser.add_argument('--light-type',
        choices=['midday', 'blue hour light', 'low-angle sunlight', 'sunrise light',
                 'spotlight on subject', 'overcast light', 'soft overcast daylight lighting',
                 'cloud-filtered lighting', 'fog-diffused lighting', 'moonlight lighting',
                 'starlight nighttime', 'soft bokeh lighting', 'harsh studio lighting'],
        default='soft overcast daylight lighting', help='Light type for relight operation')
    edit_parser.add_argument('--season', choices=['spring', 'summer', 'autumn', 'winter'],
        default='winter', help='Target season for reseason operation')
    edit_parser.add_argument('--style',
        choices=['3D Render', 'Cubism', 'Oil Painting', 'Anime', 'Cartoon', 'Coloring Book',
                 'Retro Ad', 'Pop Art Halftone', 'Vector Art', 'Story Board', 'Art Nouveau',
                 'Cross Etching', 'Wood Cut'],
        default='Oil Painting', help='Art style for restyle operation')

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

        if args.command == 'run':
            handle_run(args, client)
        elif args.command == 'generate':
            handle_generate(args, client)
        elif args.command == 'video':
            handle_video(args, client)
        elif args.command == 'video-edit':
            handle_video_edit(args, client)
        elif args.command == 'tts':
            handle_tts(args, client)
        elif args.command == 'music':
            handle_music(args, client)
        elif args.command == 'avatar':
            handle_avatar(args, client)
        elif args.command == 'transcribe':
            handle_transcribe(args, client)
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
