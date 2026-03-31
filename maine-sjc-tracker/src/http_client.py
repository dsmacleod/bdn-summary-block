"""HTTP client with rate limiting and retries."""

import time
import requests

DELAY_SECONDS = 1.0
MAX_RETRIES = 3

_last_request_time = 0.0


def _rate_limit():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < DELAY_SECONDS:
        time.sleep(DELAY_SECONDS - elapsed)
    _last_request_time = time.time()


def fetch_page(url: str) -> str:
    """Fetch a page with rate limiting and retries. Returns HTML string."""
    for attempt in range(MAX_RETRIES):
        _rate_limit()
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.text
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
    raise Exception(f"Failed to fetch {url} after {MAX_RETRIES} attempts (status {resp.status_code})")


def check_url_exists(url: str) -> bool:
    """HEAD request to check if a URL exists. Returns True/False."""
    _rate_limit()
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException:
        return False
