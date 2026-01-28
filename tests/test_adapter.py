import unittest
import tempfile
import os
from scripts.lib.adapter import ResponseAdapter

class TestResponseAdapter(unittest.TestCase):

    def setUp(self):
        """Create temporary patterns file for testing"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.temp_file.close()
        self.adapter = ResponseAdapter(patterns_file=self.temp_file.name)

    def tearDown(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_extract_known_pattern(self):
        """Test extraction with known pattern"""
        response = {"data": {"images": [{"url": "https://fal.ai/test.png"}]}}
        result = self.adapter.extract_result(response, "fal-ai/flux-pro")

        self.assertEqual(result, "https://fal.ai/test.png")

    def test_extract_nested_pattern(self):
        """Test extraction with nested structure"""
        response = {"output": {"result": {"url": "https://fal.ai/nested.png"}}}
        result = self.adapter.extract_result(response, "test-model")

        self.assertEqual(result, "https://fal.ai/nested.png")

    def test_learning_after_threshold(self):
        """Test pattern learning after confidence threshold"""
        response = {"custom": {"path": {"url": "https://fal.ai/test.png"}}}

        # Extract 3 times (confidence threshold)
        for i in range(3):
            self.adapter.extract_result(response, "learning-model")

        stats = self.adapter.get_stats("learning-model")
        self.assertEqual(stats["status"], "learned")
        self.assertIsNotNone(stats["learned_path"])

    def test_url_search_fallback(self):
        """Test fallback to URL search when patterns fail"""
        response = {"weird_structure": {"nested": "https://fal.ai/found.png"}}
        result = self.adapter.extract_result(response, "unknown-model")

        self.assertEqual(result, "https://fal.ai/found.png")

    def test_multiple_patterns(self):
        """Test trying multiple common patterns"""
        # Test image.url pattern
        response1 = {"image": {"url": "https://fal.ai/image.png"}}
        result1 = self.adapter.extract_result(response1, "model1")
        self.assertEqual(result1, "https://fal.ai/image.png")

        # Test video.url pattern
        response2 = {"video": {"url": "https://fal.ai/video.mp4"}}
        result2 = self.adapter.extract_result(response2, "model2")
        self.assertEqual(result2, "https://fal.ai/video.mp4")

    def test_no_url_found(self):
        """Test when no URL exists in response"""
        response = {"data": {"value": 42, "text": "no url here"}}
        result = self.adapter.extract_result(response, "no-url-model")

        self.assertIsNone(result)

    def test_pattern_persistence(self):
        """Test that learned patterns are saved to file"""
        response = {"data": {"images": [{"url": "https://fal.ai/test.png"}]}}

        # Learn pattern
        for i in range(3):
            self.adapter.extract_result(response, "persist-model")

        # Create new adapter with same file - should load learned pattern
        adapter2 = ResponseAdapter(patterns_file=self.temp_file.name)
        stats = adapter2.get_stats("persist-model")

        self.assertEqual(stats["status"], "learned")
        self.assertEqual(stats["learned_path"], "data.images[0].url")

    def test_pattern_demotion(self):
        """Test that unreliable patterns are demoted"""
        response_success = {"data": {"url": "https://fal.ai/success.png"}}
        response_fail = {"different": {"structure": "no url"}}

        # Record 3 successes to learn pattern
        for i in range(3):
            self.adapter.extract_result(response_success, "demote-model")

        # Verify learned
        stats = self.adapter.get_stats("demote-model")
        self.assertEqual(stats["status"], "learned")

        # Now fail multiple times to trigger demotion
        # Need total >= ATTEMPT_THRESHOLD (5) and success_rate < 0.8
        # Currently: 3 success, need 2 more attempts with failures
        for i in range(3):
            self.adapter.extract_result(response_fail, "demote-model")

        # Now: 3 success, 3 fail = 50% success rate, should be demoted
        stats = self.adapter.get_stats("demote-model")
        self.assertEqual(stats["confidence"], "low")
        self.assertIsNone(stats["learned_path"])

if __name__ == '__main__':
    unittest.main()
