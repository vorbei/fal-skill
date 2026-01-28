import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from detect_intent import (
    detect_intent,
    extract_duration_hint,
    extract_aspect_ratio,
    extract_video_reference,
    extract_scale_hint
)

class TestVideoIntentDetection(unittest.TestCase):
    """Test video generation intent detection"""

    def test_text_to_video_simple(self):
        """Test basic text-to-video intent"""
        result = detect_intent("create a video of a wizard cat")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("wizard cat", result["args"][0])

    def test_text_to_video_with_duration(self):
        """Test text-to-video with duration hint"""
        result = detect_intent("make a 10 second video of fireworks")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("--duration 10", result["args"][1])

    def test_text_to_video_vertical(self):
        """Test text-to-video with vertical aspect ratio"""
        result = detect_intent("create a vertical video for TikTok")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("9:16", result["args"][2])

    def test_image_to_video(self):
        """Test image-to-video with image reference"""
        result = detect_intent("animate this image: cat.jpg")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("cat.jpg", result["args"][1])

    def test_motion_keywords(self):
        """Test motion keywords for video detection"""
        result = detect_intent("create motion graphics")
        self.assertEqual(result["skill"], "fal-generate-video")

class TestEditingIntentDetection(unittest.TestCase):
    """Test photo editing intent detection"""

    def test_colorize_detection(self):
        """Test colorize intent"""
        result = detect_intent("colorize photo.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("colorize", result["args"][1])

    def test_relight_detection(self):
        """Test relight intent"""
        result = detect_intent("relight image.jpg with sunset lighting")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("relight", result["args"][1])

    def test_reseason_detection(self):
        """Test reseason intent"""
        result = detect_intent("change season to winter in landscape.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("reseason", result["args"][1])

    def test_restore_detection(self):
        """Test restore intent"""
        result = detect_intent("restore old photo.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("restore", result["args"][1])

    def test_restyle_detection(self):
        """Test restyle intent"""
        result = detect_intent("restyle portrait.jpg as watercolor")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("restyle", result["args"][1])

    def test_remove_object_detection(self):
        """Test remove object intent"""
        result = detect_intent("remove the person from photo.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("remove-object", result["args"][1])

    def test_add_object_detection(self):
        """Test add object intent"""
        result = detect_intent("add a tree to landscape.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("add-object", result["args"][1])

class TestUpscaleIntentDetection(unittest.TestCase):
    """Test upscale intent detection"""

    def test_image_upscale_2x(self):
        """Test image upscale 2x intent"""
        result = detect_intent("upscale image.jpg 2x")
        self.assertEqual(result["skill"], "fal-upscale")
        self.assertIn("--scale 2", result["args"][1])
        self.assertIn("image", result["args"][2])

    def test_image_upscale_4x(self):
        """Test image upscale 4x intent"""
        result = detect_intent("enhance photo.png 4x")
        self.assertEqual(result["skill"], "fal-upscale")
        self.assertIn("--scale 4", result["args"][1])

    def test_video_upscale(self):
        """Test video upscale intent"""
        result = detect_intent("upscale video.mp4")
        self.assertEqual(result["skill"], "fal-upscale")
        self.assertIn("video.mp4", result["args"][0])
        self.assertIn("video", result["args"][2])

    def test_enhance_quality(self):
        """Test quality enhancement keywords"""
        result = detect_intent("improve quality of image.jpg")
        self.assertEqual(result["skill"], "fal-upscale")

class TestVideoHelpers(unittest.TestCase):
    """Test video-related helper functions"""

    def test_duration_extraction_10_seconds(self):
        """Test 10 second duration extraction"""
        self.assertEqual(extract_duration_hint("10 seconds"), 10)
        self.assertEqual(extract_duration_hint("10s"), 10)
        self.assertEqual(extract_duration_hint("create a 10 second video"), 10)

    def test_duration_extraction_5_seconds(self):
        """Test 5 second duration extraction"""
        self.assertEqual(extract_duration_hint("5 seconds"), 5)
        self.assertEqual(extract_duration_hint("5s video"), 5)

    def test_duration_extraction_default(self):
        """Test default duration when not specified"""
        self.assertEqual(extract_duration_hint("no duration mentioned"), 5)
        self.assertEqual(extract_duration_hint("create a video"), 5)

    def test_aspect_ratio_extraction_16_9(self):
        """Test 16:9 aspect ratio extraction"""
        self.assertEqual(extract_aspect_ratio("widescreen video"), "16:9")
        self.assertEqual(extract_aspect_ratio("landscape"), "16:9")
        self.assertEqual(extract_aspect_ratio("horizontal video"), "16:9")

    def test_aspect_ratio_extraction_9_16(self):
        """Test 9:16 aspect ratio extraction"""
        self.assertEqual(extract_aspect_ratio("vertical video"), "9:16")
        self.assertEqual(extract_aspect_ratio("portrait"), "9:16")
        self.assertEqual(extract_aspect_ratio("TikTok video"), "9:16")

    def test_aspect_ratio_extraction_1_1(self):
        """Test 1:1 aspect ratio extraction"""
        self.assertEqual(extract_aspect_ratio("square video"), "1:1")
        self.assertEqual(extract_aspect_ratio("instagram video"), "1:1")

    def test_aspect_ratio_extraction_default(self):
        """Test default aspect ratio"""
        self.assertEqual(extract_aspect_ratio("no ratio mentioned"), "16:9")

    def test_video_reference_extraction_url(self):
        """Test video URL extraction"""
        result = extract_video_reference("upscale https://example.com/video.mp4")
        self.assertEqual(result, "https://example.com/video.mp4")

    def test_video_reference_extraction_path(self):
        """Test video file path extraction"""
        result = extract_video_reference("enhance ~/videos/clip.mov")
        self.assertEqual(result, "~/videos/clip.mov")

    def test_video_reference_extraction_none(self):
        """Test when no video reference found"""
        result = extract_video_reference("no video here")
        self.assertIsNone(result)

    def test_scale_extraction_2x(self):
        """Test 2x scale extraction"""
        self.assertEqual(extract_scale_hint("upscale 2x"), 2)
        self.assertEqual(extract_scale_hint("double the size"), 2)

    def test_scale_extraction_4x(self):
        """Test 4x scale extraction"""
        self.assertEqual(extract_scale_hint("upscale 4x"), 4)
        self.assertEqual(extract_scale_hint("four times larger"), 4)
        self.assertEqual(extract_scale_hint("quadruple quality"), 4)

    def test_scale_extraction_8x(self):
        """Test 8x scale extraction"""
        self.assertEqual(extract_scale_hint("upscale 8x"), 8)
        self.assertEqual(extract_scale_hint("eight times"), 8)

    def test_scale_extraction_default(self):
        """Test default scale"""
        self.assertEqual(extract_scale_hint("no scale mentioned"), 2)

class TestIntentPriority(unittest.TestCase):
    """Test intent detection priority"""

    def test_video_over_image(self):
        """Test that video keywords take priority over image"""
        result = detect_intent("create a video of a cat")
        self.assertEqual(result["skill"], "fal-generate-video")

    def test_editing_with_image_reference(self):
        """Test editing detection requires image reference"""
        result = detect_intent("colorize this")
        # Without image reference, should default to image generation
        self.assertEqual(result["skill"], "fal-generate-image")

        result = detect_intent("colorize photo.jpg")
        # With image reference, should detect editing
        self.assertEqual(result["skill"], "fal-edit-photo")

    def test_upscale_over_generate(self):
        """Test upscale takes priority when scale mentioned"""
        result = detect_intent("upscale image.jpg 4x")
        self.assertEqual(result["skill"], "fal-upscale")

    def test_background_removal_fallback(self):
        """Test background removal still works"""
        result = detect_intent("remove background from photo.jpg")
        self.assertEqual(result["skill"], "fal-remove-bg")

    def test_default_to_image(self):
        """Test default fallback to image generation"""
        result = detect_intent("a beautiful sunset")
        self.assertEqual(result["skill"], "fal-generate-image")

class TestComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios"""

    def test_vertical_video_tiktok(self):
        """Test vertical video for social media"""
        result = detect_intent("create a 10 second vertical video of a dance")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("--duration 10", result["args"][1])
        self.assertIn("9:16", result["args"][2])

    def test_colorize_old_photo(self):
        """Test colorizing old photos"""
        result = detect_intent("add color to old_bw_photo.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("colorize", result["args"][1])

    def test_video_upscale_from_720p(self):
        """Test upscaling video from 720p"""
        result = detect_intent("upscale 720p_video.mp4 to 1440p")
        self.assertEqual(result["skill"], "fal-upscale")
        self.assertIn("video", result["args"][2])

    def test_animate_portrait(self):
        """Test animating a portrait photo"""
        result = detect_intent("animate portrait.jpg with subtle motion")
        self.assertEqual(result["skill"], "fal-generate-video")
        self.assertIn("portrait.jpg", result["args"][1])

    def test_restore_damaged_photo(self):
        """Test restoring damaged photos"""
        result = detect_intent("fix damaged_photo.jpg")
        self.assertEqual(result["skill"], "fal-edit-photo")
        self.assertIn("restore", result["args"][1])

if __name__ == '__main__':
    unittest.main()
