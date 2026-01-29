import os
import tempfile
from typing import Optional


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/fal-skill/.env")


def load_api_key(
    api_key: Optional[str] = None,
    env_var: str = "FAL_KEY",
    config_path: str = DEFAULT_CONFIG_PATH,
) -> str:
    """Load API key from argument, env, or config file."""
    if api_key:
        return api_key

    env_value = os.environ.get(env_var)
    if env_value:
        return env_value

    if not os.path.exists(config_path):
        raise ValueError("API key not found. Run /fal-setup first.")

    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("FAL_KEY="):
                return line.strip().split("=", 1)[1]

    raise ValueError("FAL_KEY not found in config file")


def atomic_write(path: str, data: str, mode: str = "w", encoding: str = "utf-8") -> None:
    """Atomically write text data to a file."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(fd, mode, encoding=encoding) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
