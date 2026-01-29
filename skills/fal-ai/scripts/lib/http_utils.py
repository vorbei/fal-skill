import time
import urllib.error
import urllib.request
from typing import Iterable, Tuple


RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


def urlopen_with_retries(
    request: urllib.request.Request,
    timeout: int = 30,
    retries: int = 3,
    backoff_seconds: float = 0.5,
    retry_statuses: Iterable[int] = RETRY_STATUS_CODES,
):
    """Open URL with basic retry/backoff for transient failures."""
    last_error = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code in retry_statuses and attempt < retries - 1:
                time.sleep(backoff_seconds * (2 ** attempt))
                continue
            raise
        except urllib.error.URLError as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(backoff_seconds * (2 ** attempt))
                continue
            raise

    if last_error:
        raise last_error
