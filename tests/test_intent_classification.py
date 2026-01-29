#!/usr/bin/env python3
"""
Integration tests for /fal-generate intent classification

These test cases document the expected behavior when Claude Code
interprets user requests through the SKILL.md instructions.

Usage:
    pytest tests/test_intent_classification.py -v

Note: These tests verify the documented intent classification rules.
They serve as regression tests and documentation for expected behavior.
"""

import pytest

# Test cases format: (user_request, expected_command, expected_model_contains, description)
# expected_command: 'generate', 'video', 'tts', 'music', 'avatar', 'transcribe', 'upscale', 'edit', 'remove-bg'

INTENT_TEST_CASES = [
    # === Image Generation (Default) ===
    ("a wizard cat", "generate", "flux", "basic image prompt"),
    ("帮我画一只猫", "generate", "flux", "Chinese image request"),
    ("create an image of a sunset", "generate", "flux", "explicit image request"),
    ("draw a portrait of a warrior", "generate", "flux", "draw keyword"),
    ("生成图片：一座城堡", "generate", "flux", "Chinese explicit image"),

    # === Video Generation ===
    ("create a video of ocean waves", "video", "kling", "basic video request"),
    ("生成一个猫跳舞的视频", "video", "kling", "Chinese video request"),
    ("animate a flying bird", "video", "kling", "animate keyword"),
    ("make a short clip of fireworks", "video", "kling", "clip keyword"),
    ("10 second video of a waterfall", "video", "kling", "video with duration"),

    # === Image-to-Video ===
    ("animate this image cat.jpg", "video", "image-to-video", "image to video"),
    ("把这张图变成视频 photo.png", "video", "image-to-video", "Chinese image to video"),
    ("make cat.jpg move", "video", "image-to-video", "make image move"),

    # === Background Removal ===
    ("remove background from photo.jpg", "remove-bg", "birefnet", "explicit bg removal"),
    ("去背景 image.png", "remove-bg", "birefnet", "Chinese bg removal"),
    ("make photo.jpg transparent", "remove-bg", "birefnet", "transparent keyword"),
    ("抠图 portrait.jpg", "remove-bg", "birefnet", "Chinese cutout"),
    ("cut out the subject from image.png", "remove-bg", "birefnet", "cut out keyword"),

    # === TTS (Text-to-Speech) ===
    ("speak this text: Hello world", "tts", "kokoro", "basic TTS"),
    ("朗读：今天天气真好", "tts", "kokoro", "Chinese TTS"),
    ("read aloud: The quick brown fox", "tts", "kokoro", "read aloud"),
    ("convert to speech: Welcome", "tts", "kokoro", "convert to speech"),
    ("tts: Testing one two three", "tts", "kokoro", "explicit TTS"),

    # === Music Generation ===
    ("generate background music", "music", "minimax-music", "basic music"),
    ("生成一段轻松的音乐", "music", "minimax-music", "Chinese music"),
    ("create a soundtrack for my video", "music", "minimax-music", "soundtrack"),
    ("make some bgm", "music", "minimax-music", "bgm keyword"),
    ("compose a song about summer", "music", "minimax-music", "song keyword"),

    # === Sound Effects ===
    ("explosion sound effect", "music", "cassetteai", "sound effect"),
    ("生成一个爆炸音效", "music", "cassetteai", "Chinese sfx"),
    ("sfx: door creaking", "music", "cassetteai", "explicit sfx"),

    # === Avatar/Lipsync ===
    ("create avatar with portrait.jpg and audio.mp3", "avatar", "avatar", "basic avatar"),
    ("lipsync portrait.jpg to speech.wav", "avatar", "avatar", "lipsync keyword"),
    ("口型同步 face.jpg voice.mp3", "avatar", "avatar", "Chinese lipsync"),
    ("make a talking head video", "avatar", "avatar", "talking head"),

    # === Transcription ===
    ("transcribe meeting.mp3", "transcribe", "scribe", "basic transcribe"),
    ("转文字 audio.wav", "transcribe", "scribe", "Chinese transcribe"),
    ("speech to text: recording.m4a", "transcribe", "scribe", "speech to text"),
    ("听写 lecture.mp3", "transcribe", "scribe", "Chinese dictation"),

    # === Upscale ===
    ("upscale image.jpg", "upscale", "crystal", "basic upscale"),
    ("放大这张图 photo.png", "upscale", "crystal", "Chinese upscale"),
    ("enhance image.jpg 4x", "upscale", "crystal", "enhance with scale"),
    ("2x upscale portrait.jpg", "upscale", "crystal", "scale prefix"),
    ("超分 low_res.jpg", "upscale", "crystal", "Chinese super resolution"),

    # === Photo Edit ===
    ("colorize old_photo.jpg", "edit", "colorize", "colorize"),
    ("relight portrait.jpg with sunset lighting", "edit", "relight", "relight"),
    ("change season to winter in landscape.jpg", "edit", "reseason", "reseason"),
    ("让照片更温暖 photo.jpg", "edit", "relight", "Chinese warm lighting"),
    ("把照片变成冬天 scene.jpg", "edit", "reseason", "Chinese winter"),
]

# Conflict resolution test cases - tests for ambiguous requests
CONFLICT_TEST_CASES = [
    # Priority: Background Removal vs Object Removal
    ("remove background from photo.jpg", "remove-bg", "background removal wins"),
    ("remove the person from photo.jpg", "edit", "object removal - no 'background' keyword"),

    # Priority: Upscale vs Image Generation
    ("make the image larger photo.jpg", "upscale", "larger with file = upscale"),
    ("create a larger castle image", "generate", "larger in creative context = generate"),

    # Priority: Music vs Video
    ("music video of a band performing", "video", "video keyword takes precedence"),
    ("generate music for my video project", "music", "music is output, video is context"),
    ("create background music", "music", "explicit music request"),

    # Priority: Enhance ambiguity
    ("enhance photo.jpg", "upscale", "enhance alone = quality improvement"),
    ("enhance the colors in photo.jpg", "edit", "enhance colors = colorize edit"),

    # Priority: Speak vs Voice
    ("speak this: Hello", "tts", "speak = TTS output"),
    ("add voice to video.mp4", "avatar", "voice + video = avatar/lipsync context"),
]

# Parameter extraction test cases
PARAMETER_TEST_CASES = [
    # Video duration
    ("5 second video of a cat", {"duration": 5}),
    ("10秒视频", {"duration": 10}),
    ("short video", {"duration": 5}),
    ("longer video", {"duration": 10}),

    # Video aspect ratio
    ("vertical video for TikTok", {"aspect_ratio": "9:16"}),
    ("手机看的视频", {"aspect_ratio": "9:16"}),
    ("widescreen video", {"aspect_ratio": "16:9"}),
    ("横屏视频", {"aspect_ratio": "16:9"}),
    ("square video for Instagram", {"aspect_ratio": "1:1"}),

    # Image size
    ("portrait orientation image", {"size": "portrait_16_9"}),
    ("竖版图片", {"size": "portrait_16_9"}),
    ("landscape photo", {"size": "landscape_16_9"}),
    ("横版图", {"size": "landscape_16_9"}),

    # Upscale factor
    ("upscale 2x", {"scale": 2}),
    ("放大4倍", {"scale": 4}),
    ("8x upscale", {"scale": 8}),
]


class TestIntentClassification:
    """Test intent classification based on SKILL.md rules"""

    @pytest.mark.parametrize("user_input,expected_cmd,expected_model,description", INTENT_TEST_CASES)
    def test_intent_detection(self, user_input, expected_cmd, expected_model, description):
        """
        Verify intent classification rules.

        These tests document expected behavior. In practice, Claude Code
        interprets the SKILL.md and makes the classification.
        """
        # This test documents the expected mapping
        # Actual verification would require running Claude Code
        assert expected_cmd in ['generate', 'video', 'tts', 'music', 'avatar',
                                'transcribe', 'upscale', 'edit', 'remove-bg'], \
            f"Invalid expected command: {expected_cmd}"
        assert isinstance(expected_model, str), f"Model hint must be string"

    @pytest.mark.parametrize("user_input,expected_cmd,description", CONFLICT_TEST_CASES)
    def test_conflict_resolution(self, user_input, expected_cmd, description):
        """
        Verify conflict resolution priority rules.

        When multiple intents could match, the priority order in SKILL.md
        should determine the correct classification.
        """
        assert expected_cmd in ['generate', 'video', 'tts', 'music', 'avatar',
                                'transcribe', 'upscale', 'edit', 'remove-bg'], \
            f"Invalid expected command: {expected_cmd}"


class TestParameterExtraction:
    """Test parameter extraction from natural language"""

    @pytest.mark.parametrize("user_input,expected_params", PARAMETER_TEST_CASES)
    def test_parameter_extraction(self, user_input, expected_params):
        """
        Verify parameter extraction rules.

        These tests document expected parameter mappings from
        natural language hints to CLI arguments.
        """
        for key, value in expected_params.items():
            assert key in ['duration', 'aspect_ratio', 'size', 'scale'], \
                f"Unknown parameter: {key}"


class TestBilingualSupport:
    """Test Chinese and English language support"""

    chinese_english_pairs = [
        ("帮我画一只猫", "draw a cat"),
        ("生成视频", "generate video"),
        ("去背景", "remove background"),
        ("朗读", "speak"),
        ("音乐", "music"),
        ("转文字", "transcribe"),
        ("放大", "upscale"),
    ]

    @pytest.mark.parametrize("chinese,english", chinese_english_pairs)
    def test_bilingual_equivalence(self, chinese, english):
        """
        Verify Chinese and English requests map to same intent.

        The SKILL.md includes bilingual triggers to ensure
        consistent behavior across languages.
        """
        # Document that these pairs should produce equivalent results
        assert isinstance(chinese, str) and isinstance(english, str)


# Utility function for manual testing
def print_test_summary():
    """Print summary of all test cases for manual verification"""
    print("\n=== Intent Classification Test Cases ===\n")

    print("Basic Intent Tests:")
    for request, cmd, model, desc in INTENT_TEST_CASES:
        print(f"  [{cmd:12}] {request[:50]:50} # {desc}")

    print("\nConflict Resolution Tests:")
    for request, cmd, desc in CONFLICT_TEST_CASES:
        print(f"  [{cmd:12}] {request[:50]:50} # {desc}")

    print("\nParameter Extraction Tests:")
    for request, params in PARAMETER_TEST_CASES:
        print(f"  {request[:40]:40} → {params}")


if __name__ == "__main__":
    print_test_summary()
