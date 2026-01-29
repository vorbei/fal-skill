#!/usr/bin/env python3
"""
LLM-based intent classification tests

These tests call the Claude API to verify that intent classification
works correctly when Claude reads the SKILL.md instructions.

Usage:
    # Run all LLM tests (costs money!)
    pytest tests/test_llm_intent.py -v

    # Run a subset
    pytest tests/test_llm_intent.py -v -k "test_basic"

    # Skip slow tests
    pytest tests/test_llm_intent.py -v -m "not slow"

Environment:
    ANTHROPIC_API_KEY: Required for Claude API access
"""

import os
import json
import pytest
from pathlib import Path

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


def get_skill_content() -> str:
    """Load the SKILL.md content"""
    skill_path = Path(__file__).parent.parent / "skills" / "fal-generate" / "SKILL.md"
    return skill_path.read_text()


def classify_intent(user_request: str, client) -> dict:
    """
    Ask Claude to classify the intent based on SKILL.md instructions.

    Returns dict with:
        - command: The fal_api.py command (generate, video, tts, etc.)
        - model: The model to use
        - reasoning: Why this classification was chosen
    """
    skill_content = get_skill_content()

    prompt = f"""You are testing intent classification for a media generation skill.

Given the SKILL.md instructions below, classify the user's request and return ONLY a JSON object.

<skill_instructions>
{skill_content}
</skill_instructions>

<user_request>
{user_request}
</user_request>

Respond with ONLY a JSON object (no markdown, no explanation):
{{
    "command": "generate|video|tts|music|avatar|transcribe|upscale|edit|remove-bg",
    "model": "the model endpoint to use",
    "reasoning": "brief explanation of why this classification"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse JSON from response
    text = response.content[0].text.strip()
    # Handle potential markdown code blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


@pytest.fixture(scope="module")
def claude_client():
    """Create Anthropic client for tests"""
    try:
        import anthropic
        return anthropic.Anthropic()
    except ImportError:
        pytest.skip("anthropic package not installed")


# =============================================================================
# Basic Intent Tests
# =============================================================================

class TestBasicIntents:
    """Test basic intent classification"""

    @pytest.mark.parametrize("user_input,expected_cmd", [
        # Image Generation
        ("a wizard cat", "generate"),
        ("帮我画一只猫", "generate"),
        ("create an image of a sunset", "generate"),

        # Video Generation
        ("create a video of ocean waves", "video"),
        ("生成一个猫跳舞的视频", "video"),
        ("animate a flying bird", "video"),

        # Background Removal
        ("remove background from photo.jpg", "remove-bg"),
        ("去背景 image.png", "remove-bg"),
        ("make photo.jpg transparent", "remove-bg"),

        # TTS
        ("speak this: Hello world", "tts"),
        ("朗读：今天天气真好", "tts"),

        # Music
        ("generate background music", "music"),
        ("生成一段轻松的音乐", "music"),

        # Transcribe
        ("transcribe meeting.mp3", "transcribe"),
        ("转文字 audio.wav", "transcribe"),

        # Upscale
        ("upscale image.jpg 4x", "upscale"),
        ("放大这张图 photo.png", "upscale"),

        # Photo Edit
        ("colorize old_photo.jpg", "edit"),
        ("relight portrait.jpg with sunset", "edit"),
    ])
    def test_basic_intent(self, claude_client, user_input, expected_cmd):
        """Test basic intent classification"""
        result = classify_intent(user_input, claude_client)
        assert result["command"] == expected_cmd, \
            f"Expected '{expected_cmd}' but got '{result['command']}'. Reasoning: {result.get('reasoning', 'N/A')}"


# =============================================================================
# Conflict Resolution Tests
# =============================================================================

class TestConflictResolution:
    """Test ambiguous cases where priority rules matter"""

    @pytest.mark.parametrize("user_input,expected_cmd,description", [
        # Background vs Object Removal
        ("remove background from photo.jpg", "remove-bg", "background keyword = bg removal"),
        ("remove the person from photo.jpg", "edit", "remove object = photo edit"),

        # Upscale vs Generate
        ("make the image larger photo.jpg", "upscale", "larger with file = upscale"),
        ("create a larger castle image", "generate", "larger in creative context = generate"),

        # Music vs Video
        ("music video of a band performing", "video", "video keyword takes precedence"),
        ("generate music for my video project", "music", "music is the output"),

        # Enhance ambiguity
        ("enhance photo.jpg", "upscale", "enhance alone = quality improvement"),
        ("enhance the colors in photo.jpg", "edit", "enhance colors = colorize"),
    ])
    def test_conflict_resolution(self, claude_client, user_input, expected_cmd, description):
        """Test priority-based conflict resolution"""
        result = classify_intent(user_input, claude_client)
        assert result["command"] == expected_cmd, \
            f"[{description}] Expected '{expected_cmd}' but got '{result['command']}'. Reasoning: {result.get('reasoning', 'N/A')}"


# =============================================================================
# Bilingual Tests
# =============================================================================

class TestBilingual:
    """Test Chinese and English produce same results"""

    @pytest.mark.parametrize("chinese,english,expected_cmd", [
        ("帮我画一只猫", "draw a cat for me", "generate"),
        ("生成一个视频", "generate a video", "video"),
        ("去背景 photo.jpg", "remove background from photo.jpg", "remove-bg"),
        ("朗读这段文字", "read this text aloud", "tts"),
        ("生成音乐", "generate music", "music"),
        ("转文字 audio.mp3", "transcribe audio.mp3", "transcribe"),
        ("放大图片 4倍", "upscale image 4x", "upscale"),
    ])
    def test_bilingual_equivalence(self, claude_client, chinese, english, expected_cmd):
        """Test Chinese and English requests produce same intent"""
        result_cn = classify_intent(chinese, claude_client)
        result_en = classify_intent(english, claude_client)

        assert result_cn["command"] == expected_cmd, \
            f"Chinese '{chinese}' got '{result_cn['command']}' instead of '{expected_cmd}'"
        assert result_en["command"] == expected_cmd, \
            f"English '{english}' got '{result_en['command']}' instead of '{expected_cmd}'"


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test tricky edge cases"""

    @pytest.mark.parametrize("user_input,expected_cmd,description", [
        # Mixed language
        ("画一个 video of cats", "video", "video keyword wins despite Chinese start"),
        ("remove 背景 from photo.jpg", "remove-bg", "mixed language bg removal"),

        # Implicit intent
        ("cat.jpg -> transparent", "remove-bg", "arrow notation for bg removal"),
        ("photo.jpg 变清晰", "upscale", "Chinese 'make clearer' = upscale"),

        # Multiple files
        ("animate cat.jpg with audio.mp3", "avatar", "image + audio = avatar"),

        # Negation handling
        ("don't remove background, just upscale photo.jpg", "upscale", "negation should be understood"),
    ])
    def test_edge_cases(self, claude_client, user_input, expected_cmd, description):
        """Test edge cases and tricky inputs"""
        result = classify_intent(user_input, claude_client)
        assert result["command"] == expected_cmd, \
            f"[{description}] Expected '{expected_cmd}' but got '{result['command']}'. Reasoning: {result.get('reasoning', 'N/A')}"


# =============================================================================
# Parameter Extraction Tests
# =============================================================================

class TestParameterExtraction:
    """Test that Claude extracts parameters correctly"""

    def test_video_duration_extraction(self, claude_client):
        """Test video duration is extracted"""
        result = classify_intent("create a 10 second video of waves", claude_client)
        assert result["command"] == "video"
        # Check reasoning mentions duration
        assert "10" in result.get("reasoning", "") or "duration" in result.get("reasoning", "").lower()

    def test_aspect_ratio_extraction(self, claude_client):
        """Test aspect ratio hints are understood"""
        result = classify_intent("vertical video for TikTok of a dancer", claude_client)
        assert result["command"] == "video"
        reasoning = result.get("reasoning", "").lower()
        assert any(x in reasoning for x in ["9:16", "vertical", "portrait", "tiktok"])

    def test_upscale_factor_extraction(self, claude_client):
        """Test upscale factor is extracted"""
        result = classify_intent("upscale image.jpg 4x", claude_client)
        assert result["command"] == "upscale"


# =============================================================================
# Batch Test Runner
# =============================================================================

def run_batch_test(test_cases: list, client) -> dict:
    """
    Run a batch of test cases and return results summary.
    Useful for cost-efficient batch testing.
    """
    results = {"passed": 0, "failed": 0, "failures": []}

    for user_input, expected_cmd in test_cases:
        try:
            result = classify_intent(user_input, client)
            if result["command"] == expected_cmd:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "input": user_input,
                    "expected": expected_cmd,
                    "got": result["command"],
                    "reasoning": result.get("reasoning", "N/A")
                })
        except Exception as e:
            results["failed"] += 1
            results["failures"].append({
                "input": user_input,
                "expected": expected_cmd,
                "error": str(e)
            })

    return results


if __name__ == "__main__":
    """Run a quick smoke test"""
    import anthropic

    client = anthropic.Anthropic()

    smoke_tests = [
        ("画一只猫", "generate"),
        ("create a video of waves", "video"),
        ("remove background from photo.jpg", "remove-bg"),
        ("transcribe audio.mp3", "transcribe"),
    ]

    print("Running smoke tests...\n")
    results = run_batch_test(smoke_tests, client)

    print(f"Passed: {results['passed']}/{len(smoke_tests)}")
    if results["failures"]:
        print("\nFailures:")
        for f in results["failures"]:
            print(f"  - {f['input']}: expected '{f['expected']}', got '{f.get('got', f.get('error'))}'")
