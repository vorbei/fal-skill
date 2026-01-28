"""
Tests for intent detection logic
"""

import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from detect_intent import detect_intent, extract_image_reference, clean_prompt


class TestIntentDetection(unittest.TestCase):
    """Test suite for intent detection"""

    def test_text_to_image_simple(self):
        """Test basic text-to-image intent"""
        result = detect_intent("a wizard cat")
        self.assertEqual(result["skill"], "fal-generate-image")
        self.assertIn("a wizard cat", result["args"][0])

    def test_text_to_image_with_portrait_size(self):
        """Test text-to-image with portrait size hint"""
        result = detect_intent("portrait of a warrior")
        self.assertEqual(result["skill"], "fal-generate-image")
        self.assertIn("portrait_16_9", result["args"][1])

    def test_text_to_image_with_landscape_size(self):
        """Test text-to-image with landscape size hint"""
        result = detect_intent("landscape mountain scene")
        self.assertEqual(result["skill"], "fal-generate-image")
        self.assertIn("landscape_16_9", result["args"][1])

    def test_text_to_image_with_square_size(self):
        """Test text-to-image with square size hint"""
        result = detect_intent("square logo design")
        self.assertEqual(result["skill"], "fal-generate-image")
        self.assertIn("square_hd", result["args"][1])

    def test_background_removal_with_url(self):
        """Test background removal with URL"""
        result = detect_intent("remove background from https://example.com/photo.jpg")
        self.assertEqual(result["skill"], "fal-remove-bg")
        self.assertIn("https://example.com/photo.jpg", result["args"])

    def test_background_removal_with_path(self):
        """Test background removal with file path"""
        result = detect_intent("remove background from ~/photo.png")
        self.assertEqual(result["skill"], "fal-remove-bg")
        self.assertIn("~/photo.png", result["args"])

    def test_background_removal_keywords(self):
        """Test various background removal keywords"""
        test_cases = [
            "make transparent image.jpg",
            "remove bg from photo.png",
            "cut out person.webp"
        ]
        for case in test_cases:
            result = detect_intent(case)
            self.assertEqual(result["skill"], "fal-remove-bg", f"Failed for: {case}")

    def test_quality_hint_fast(self):
        """Test fast quality hint detection"""
        result = detect_intent("quick sketch of a car")
        self.assertIn("fast", result["args"][2])

    def test_quality_hint_high(self):
        """Test high quality detection"""
        result = detect_intent("detailed painting of a landscape")
        self.assertIn("high", result["args"][2])

    def test_quality_hint_balanced_default(self):
        """Test default balanced quality"""
        result = detect_intent("a simple cat")
        self.assertIn("balanced", result["args"][2])


class TestImageReferenceExtraction(unittest.TestCase):
    """Test suite for image reference extraction"""

    def test_extract_url(self):
        """Test URL extraction"""
        text = "remove background from https://example.com/image.jpg"
        url = extract_image_reference(text)
        self.assertEqual(url, "https://example.com/image.jpg")

    def test_extract_file_path_jpg(self):
        """Test JPG file path extraction"""
        text = "make photo.jpg transparent"
        path = extract_image_reference(text)
        self.assertEqual(path, "photo.jpg")

    def test_extract_file_path_png(self):
        """Test PNG file path extraction"""
        text = "remove bg from ~/Downloads/image.png"
        path = extract_image_reference(text)
        self.assertEqual(path, "~/Downloads/image.png")

    def test_extract_file_path_webp(self):
        """Test WEBP file path extraction"""
        text = "cut out person.webp"
        path = extract_image_reference(text)
        self.assertEqual(path, "person.webp")

    def test_no_reference(self):
        """Test when no image reference exists"""
        text = "just some random text"
        ref = extract_image_reference(text)
        self.assertIsNone(ref)


class TestPromptCleaning(unittest.TestCase):
    """Test suite for prompt cleaning"""

    def test_clean_size_hints(self):
        """Test removal of size hints"""
        result = clean_prompt("portrait of a warrior")
        self.assertNotIn("portrait", result.lower())
        self.assertIn("of a warrior", result)

    def test_clean_quality_hints(self):
        """Test removal of quality hints"""
        result = clean_prompt("quick sketch of a car")
        self.assertNotIn("quick", result.lower())
        self.assertIn("sketch of a car", result)

    def test_clean_multiple_hints(self):
        """Test removal of multiple hints"""
        result = clean_prompt("fast landscape painting of mountains")
        self.assertNotIn("fast", result.lower())
        self.assertNotIn("landscape", result.lower())
        self.assertIn("painting of mountains", result)

    def test_clean_preserves_content(self):
        """Test that core content is preserved"""
        result = clean_prompt("a wizard cat wearing purple robes")
        self.assertEqual(result, "a wizard cat wearing purple robes")

    def test_clean_extra_spaces(self):
        """Test that extra spaces are cleaned up"""
        result = clean_prompt("portrait  of  a  warrior")
        self.assertNotIn("  ", result)  # No double spaces


if __name__ == '__main__':
    unittest.main()
