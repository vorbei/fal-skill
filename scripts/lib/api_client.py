import os
import re
from typing import Dict, Any, Optional
from .logging_config import setup_logging

logger = setup_logging(__name__)

class FalAPIClient:
    """Official fal_client wrapper for fal.ai API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self._configure_fal_client()

    def _load_api_key(self) -> str:
        """Load API key from config file"""
        config_path = os.path.expanduser("~/.config/fal-skill/.env")
        if not os.path.exists(config_path):
            raise ValueError("API key not found. Run /fal-setup first.")

        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('FAL_KEY='):
                    return line.strip().split('=', 1)[1]

        raise ValueError("FAL_KEY not found in config file")

    def _configure_fal_client(self):
        """Configure fal_client with API key"""
        os.environ['FAL_KEY'] = self.api_key

    def _validate_endpoint_id(self, endpoint_id: str):
        """Validate endpoint ID format"""
        if not endpoint_id:
            raise ValueError("endpoint_id cannot be empty")

        # Must be alphanumeric with dashes and slashes only
        if not re.match(r'^[a-zA-Z0-9/_-]+$', endpoint_id):
            raise ValueError(f"Invalid endpoint_id format: {endpoint_id}")

        # Prevent path traversal
        if '..' in endpoint_id:
            raise ValueError("endpoint_id cannot contain '..'")

    def run_model(self, endpoint_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a model using official queue system with fal_client.subscribe()

        This method uses the official fal_client SDK which automatically:
        - Submits the request to the queue
        - Polls for completion
        - Returns the final result

        Args:
            endpoint_id: Model endpoint ID (e.g., 'fal-ai/flux/dev')
            input_data: Model input parameters

        Returns:
            Model output as dictionary
        """
        self._validate_endpoint_id(endpoint_id)

        # Import fal_client here to avoid import at module level
        try:
            import fal_client
        except ImportError:
            raise ImportError(
                "fal_client is not installed. "
                "Please run: uv pip install -r requirements.txt"
            )

        logger.info(f"Submitting request to {endpoint_id} via queue system")

        def on_queue_update(update):
            """Handle queue status updates"""
            if isinstance(update, fal_client.InProgress):
                # Log any progress messages
                for log in update.logs:
                    logger.info(f"Progress: {log.get('message', '')}")

        try:
            # Use subscribe() which handles queue submission, polling, and result retrieval
            result = fal_client.subscribe(
                endpoint_id,
                arguments=input_data,
                with_logs=True,
                on_queue_update=on_queue_update
            )

            logger.info("Request completed successfully")
            return result

        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            raise Exception(f"Failed to execute model {endpoint_id}: {str(e)}")

    def submit_async(self, endpoint_id: str, input_data: Dict[str, Any], webhook_url: Optional[str] = None) -> str:
        """
        Submit a request to the queue and return request_id for later retrieval

        This is useful for long-running jobs where you want to submit and check later.

        Args:
            endpoint_id: Model endpoint ID
            input_data: Model input parameters
            webhook_url: Optional webhook URL for completion notification

        Returns:
            request_id: Unique identifier for tracking the request
        """
        self._validate_endpoint_id(endpoint_id)

        try:
            import fal_client
        except ImportError:
            raise ImportError(
                "fal_client is not installed. "
                "Please run: uv pip install -r requirements.txt"
            )

        logger.info(f"Submitting async request to {endpoint_id}")

        try:
            handler = fal_client.submit(
                endpoint_id,
                arguments=input_data,
                webhook_url=webhook_url
            )

            request_id = handler.request_id
            logger.info(f"Request submitted with ID: {request_id}")
            return request_id

        except Exception as e:
            logger.error(f"Submit Error: {str(e)}")
            raise Exception(f"Failed to submit request to {endpoint_id}: {str(e)}")

    def get_result(self, endpoint_id: str, request_id: str) -> Dict[str, Any]:
        """
        Retrieve the result of a previously submitted request

        Args:
            endpoint_id: Model endpoint ID
            request_id: Request ID from submit_async()

        Returns:
            Model output as dictionary
        """
        self._validate_endpoint_id(endpoint_id)

        try:
            import fal_client
        except ImportError:
            raise ImportError(
                "fal_client is not installed. "
                "Please run: uv pip install -r requirements.txt"
            )

        logger.info(f"Fetching result for request {request_id}")

        try:
            result = fal_client.result(endpoint_id, request_id)
            logger.info("Result retrieved successfully")
            return result

        except Exception as e:
            logger.error(f"Result Error: {str(e)}")
            raise Exception(f"Failed to get result for {request_id}: {str(e)}")

    def check_status(self, endpoint_id: str, request_id: str) -> Dict[str, Any]:
        """
        Check the status of a previously submitted request

        Args:
            endpoint_id: Model endpoint ID
            request_id: Request ID from submit_async()

        Returns:
            Status information as dictionary
        """
        self._validate_endpoint_id(endpoint_id)

        try:
            import fal_client
        except ImportError:
            raise ImportError(
                "fal_client is not installed. "
                "Please run: uv pip install -r requirements.txt"
            )

        try:
            status = fal_client.status(endpoint_id, request_id, with_logs=True)
            return status

        except Exception as e:
            logger.error(f"Status Error: {str(e)}")
            raise Exception(f"Failed to check status for {request_id}: {str(e)}")

    def discover_models(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover models from fal.ai API with pagination support

        Note: This still uses direct HTTP as fal_client doesn't provide a discovery API
        """
        import json
        import urllib.request
        import urllib.parse

        params = {
            "status": status,
            "limit": str(limit)
        }

        if category:
            params["category"] = category

        if cursor:
            params["cursor"] = cursor

        query_string = urllib.parse.urlencode(params)
        url = f"https://api.fal.ai/v1/models?{query_string}"

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(url, headers=headers, method='GET')

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"API Discovery Error {e.code}: {error_body}")

    def validate_key(self) -> bool:
        """Test if API key is valid by making a simple discovery request"""
        try:
            result = self.discover_models(limit=1)
            return "models" in result
        except Exception:
            return False
