# Development Guide

## Package Management

**IMPORTANT: Always use `uv` instead of `pip` for package management.**

`uv` is a fast Python package installer and resolver written in Rust. It's significantly faster than pip and provides better dependency resolution.

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Common Commands

```bash
# Install dependencies
uv pip install -r requirements.txt

# Install a new package
uv pip install package-name

# Run tests
uv run pytest tests/

# Run a specific test file
uv run pytest tests/test_api_client.py -v

# Run a Python script
uv run python scripts/fal_api.py validate
```

### Virtual Environment

The project uses a virtual environment at `.venv/`. With uv, you can:

```bash
# Create venv (if needed)
uv venv

# Install dependencies into venv
uv pip install -r requirements.txt

# Or use uv run to automatically use the venv
uv run python your_script.py
```

## API Client Architecture

The project uses the **official fal_client SDK with queue system** for all API calls:

### Queue System Benefits

1. **Automatic Polling**: No manual status checking needed
2. **Reliability**: Built-in retry logic and error handling
3. **Progress Tracking**: Real-time logs and status updates
4. **Official Support**: Maintained by fal.ai team

### API Methods

#### `run_model()` - Standard Execution
Uses `fal_client.subscribe()` for automatic queue management:

```python
from scripts.lib.api_client import FalAPIClient

client = FalAPIClient()
result = client.run_model("fal-ai/flux/dev", {
    "prompt": "a wizard cat",
    "image_size": "landscape_4_3"
})
```

**What happens internally:**
1. Submits request to queue
2. Polls for completion automatically
3. Returns final result

#### `submit_async()` - Long-Running Jobs
For jobs you want to check later:

```python
request_id = client.submit_async("fal-ai/flux/dev", input_data)
# Later...
result = client.get_result("fal-ai/flux/dev", request_id)
```

#### `check_status()` - Status Monitoring
Check status of a submitted request:

```python
status = client.check_status("fal-ai/flux/dev", request_id)
print(status)  # {'status': 'IN_PROGRESS', 'logs': [...]}
```

## Testing

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Specific Test File
```bash
uv run pytest tests/test_api_client.py -v
```

### Run with Coverage
```bash
uv run pytest tests/ --cov=scripts/lib --cov-report=html
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document all public methods
- Keep functions focused and testable

## Dependencies

Current dependencies (see `requirements.txt`):
- `pyyaml>=6.0` - Configuration and model registry
- `fal-client>=0.5.0` - Official fal.ai SDK with queue support

## Project Structure

```
fal-skill/
├── scripts/
│   ├── lib/
│   │   ├── api_client.py    # FalAPIClient with queue system
│   │   ├── discovery.py     # Model discovery
│   │   ├── models.py        # Model registry
│   │   └── adapter.py       # Response adapter
│   └── fal_api.py           # CLI wrapper
├── tests/                   # Unit tests
├── skills/                  # Claude Code skills
└── models/                  # Model configurations
```

## Migration Notes

### From Raw HTTP to Queue System

The project has been refactored to use the official queue system:

**Before (Raw HTTP):**
```python
# Manual polling, error handling, etc.
response = urllib.request.urlopen(...)
```

**After (Official SDK):**
```python
# Automatic queue management
result = fal_client.subscribe(endpoint_id, arguments=input_data)
```

### Key Changes

1. **No manual polling**: `subscribe()` handles it automatically
2. **Better error handling**: Built-in retry logic
3. **Progress tracking**: Real-time logs via callbacks
4. **Simpler code**: Less boilerplate

## Best Practices

1. **Always use uv**: Faster installs, better dependency resolution
2. **Use queue system**: Let fal_client handle polling
3. **Type hints**: Add type annotations to new code
4. **Test coverage**: Write tests for new features
5. **Error handling**: Use proper exception handling
6. **Logging**: Use the configured logger from `logging_config.py`

## Troubleshooting

### fal_client Import Error
```bash
# Install dependencies
uv pip install -r requirements.txt
```

### API Key Issues
```bash
# Run setup skill
/fal-setup
```

### Test Failures
```bash
# Make sure dependencies are installed
uv pip install -r requirements.txt

# Run specific failing test
uv run pytest tests/test_api_client.py::test_name -v
```

## Contributing

1. Create a new branch for your feature
2. Write tests for new functionality
3. Ensure all tests pass with `uv run pytest`
4. Update documentation as needed
5. Submit a pull request

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [fal.ai Client Documentation](https://docs.fal.ai/client-libraries)
- [fal.ai API Documentation](https://docs.fal.ai/model-apis/model-endpoints)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
