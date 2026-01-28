import unittest
from unittest.mock import patch, Mock, mock_open
import json
import tempfile
import os
from scripts.lib.api_client import FalAPIClient

class TestFalAPIClient(unittest.TestCase):

    @patch('scripts.lib.api_client.urllib.request.urlopen')
    def test_run_model_success(self, mock_urlopen):
        """Test successful model execution"""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "data": {"images": [{"url": "https://fal.ai/test.png"}]}
        }).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = FalAPIClient(api_key="test_key")
        result = client.run_model("fal-ai/flux-pro", {"prompt": "test"})

        self.assertIn("data", result)
        self.assertIn("images", result["data"])

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

    @patch('scripts.lib.api_client.urllib.request.urlopen')
    def test_run_model_http_error(self, mock_urlopen):
        """Test HTTP error handling"""
        mock_error = Mock()
        mock_error.code = 401
        mock_error.read.return_value = b'Unauthorized'

        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="test", code=401, msg="Unauthorized",
            hdrs=None, fp=mock_error
        )

        client = FalAPIClient(api_key="test_key")

        with self.assertRaises(Exception) as ctx:
            client.run_model("fal-ai/flux-pro", {"prompt": "test"})

        self.assertIn("401", str(ctx.exception))

    @patch('scripts.lib.api_client.urllib.request.urlopen')
    def test_discover_models_success(self, mock_urlopen):
        """Test successful model discovery"""
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

    @patch('scripts.lib.api_client.urllib.request.urlopen')
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

    @patch('scripts.lib.api_client.urllib.request.urlopen')
    def test_validate_key_failure(self, mock_urlopen):
        """Test API key validation with invalid key"""
        mock_urlopen.side_effect = Exception("Network error")

        client = FalAPIClient(api_key="invalid_key")
        is_valid = client.validate_key()

        self.assertFalse(is_valid)

    @patch('scripts.lib.api_client.urllib.request.urlopen')
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

if __name__ == '__main__':
    unittest.main()
