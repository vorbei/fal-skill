import unittest
from unittest.mock import patch, Mock, mock_open, MagicMock
import json
import os
import sys

# Mock fal_client before importing api_client
sys.modules['fal_client'] = MagicMock()

from scripts.lib.api_client import FalAPIClient

class TestFalAPIClient(unittest.TestCase):

    @patch('fal_client.subscribe')
    def test_run_model_success(self, mock_subscribe):
        """Test successful model execution with queue system"""
        mock_subscribe.return_value = {
            "images": [{"url": "https://fal.ai/test.png"}]
        }

        client = FalAPIClient(api_key="test_key")
        result = client.run_model("fal-ai/flux-pro", {"prompt": "test"})

        # Verify subscribe was called
        mock_subscribe.assert_called_once()
        call_args = mock_subscribe.call_args
        self.assertEqual(call_args[0][0], "fal-ai/flux-pro")
        self.assertEqual(call_args[1]["arguments"], {"prompt": "test"})

        # Verify result
        self.assertIn("images", result)

    @patch('fal_client.submit')
    def test_submit_async(self, mock_submit):
        """Test async submission with queue"""
        mock_handler = Mock()
        mock_handler.request_id = "req-123"
        mock_submit.return_value = mock_handler

        client = FalAPIClient(api_key="test_key")
        request_id = client.submit_async("fal-ai/flux-pro", {"prompt": "test"})

        # Verify submit was called
        mock_submit.assert_called_once()
        self.assertEqual(request_id, "req-123")

    @patch('fal_client.result')
    def test_get_result(self, mock_result):
        """Test retrieving result from queue"""
        mock_result.return_value = {
            "images": [{"url": "https://fal.ai/test.png"}]
        }

        client = FalAPIClient(api_key="test_key")
        result = client.get_result("fal-ai/flux-pro", "req-123")

        # Verify result was called with correct parameters
        mock_result.assert_called_once_with("fal-ai/flux-pro", "req-123")
        self.assertIn("images", result)

    @patch('fal_client.status')
    def test_check_status(self, mock_status):
        """Test checking status of queued request"""
        mock_status.return_value = {
            "status": "IN_PROGRESS",
            "logs": []
        }

        client = FalAPIClient(api_key="test_key")
        status = client.check_status("fal-ai/flux-pro", "req-123")

        # Verify status was called with correct parameters
        mock_status.assert_called_once_with(
            "fal-ai/flux-pro", "req-123", with_logs=True
        )
        self.assertEqual(status["status"], "IN_PROGRESS")

    def test_load_api_key_missing_file(self):
        """Test error when config file missing"""
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(ValueError) as ctx:
                FalAPIClient()

            self.assertIn("API key not found", str(ctx.exception))

    def test_load_api_key_success(self):
        """Test successful API key loading"""
        mock_config = "FAL_KEY=test_api_key_12345\nOTHER=value\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_config)):
                client = FalAPIClient()
                self.assertEqual(client.api_key, "test_api_key_12345")

    def test_load_api_key_missing_key(self):
        """Test error when FAL_KEY not in config"""
        mock_config = "OTHER_KEY=value\n"

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_config)):
                with self.assertRaises(ValueError) as ctx:
                    FalAPIClient()

                self.assertIn("FAL_KEY not found", str(ctx.exception))

    @patch('fal_client.subscribe')
    def test_run_model_error(self, mock_subscribe):
        """Test error handling in run_model"""
        mock_subscribe.side_effect = Exception("API Error")

        client = FalAPIClient(api_key="test_key")

        with self.assertRaises(Exception) as ctx:
            client.run_model("fal-ai/flux-pro", {"prompt": "test"})

        self.assertIn("Failed to execute model", str(ctx.exception))

    @patch('urllib.request.urlopen')
    def test_discover_models_success(self, mock_urlopen):
        """Test successful model discovery (still uses direct HTTP)"""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "models": [
                {"id": "fal-ai/flux-pro", "category": "text-to-image"}
            ]
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = FalAPIClient(api_key="test_key")
        result = client.discover_models(category="text-to-image")

        self.assertIn("models", result)
        self.assertEqual(len(result["models"]), 1)

    @patch('urllib.request.urlopen')
    def test_validate_key_success(self, mock_urlopen):
        """Test API key validation with valid key"""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "models": []
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = FalAPIClient(api_key="test_key")
        is_valid = client.validate_key()

        self.assertTrue(is_valid)

    @patch('urllib.request.urlopen')
    def test_validate_key_failure(self, mock_urlopen):
        """Test API key validation with invalid key"""
        mock_urlopen.side_effect = Exception("Network error")

        client = FalAPIClient(api_key="invalid_key")
        is_valid = client.validate_key()

        self.assertFalse(is_valid)

    @patch('urllib.request.urlopen')
    def test_discover_models_with_pagination(self, mock_urlopen):
        """Test model discovery with cursor pagination"""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "models": [{"id": "model1"}],
            "next_cursor": "abc123"
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = FalAPIClient(api_key="test_key")
        result = client.discover_models(cursor="prev_cursor")

        self.assertIn("models", result)
        # Verify Request was called with cursor parameter
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        self.assertIn("cursor=prev_cursor", request_obj.full_url)

    def test_validate_endpoint_id(self):
        """Test endpoint ID validation"""
        client = FalAPIClient(api_key="test_key")

        # Valid endpoint IDs
        valid_ids = [
            "fal-ai/flux/dev",
            "fal-ai/flux-pro",
            "my-org/my-model",
            "test_model-v2"
        ]
        for endpoint_id in valid_ids:
            try:
                client._validate_endpoint_id(endpoint_id)
            except ValueError:
                self.fail(f"Valid endpoint ID rejected: {endpoint_id}")

        # Invalid endpoint IDs
        invalid_ids = [
            "",  # Empty
            "../secret",  # Path traversal
            "fal ai/model",  # Space
            "model<script>",  # Special chars
        ]
        for endpoint_id in invalid_ids:
            with self.assertRaises(ValueError):
                client._validate_endpoint_id(endpoint_id)

if __name__ == '__main__':
    unittest.main()
