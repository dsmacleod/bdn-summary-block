from __future__ import annotations

import logging
import os
import requests
import trafilatura

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BDNEventTracker/1.0)"
}

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def fetch_page(url: str, timeout: int = 15) -> str | None:
    """Fetch a URL and return clean extracted text, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        text = trafilatura.extract(resp.text)
        return text or resp.text[:5000]
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def search_candidate_events(candidate_name: str, num_results: int = 10) -> list[str]:
    """Search Brave for recent events for a candidate."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        logger.warning("BRAVE_API_KEY not set, skipping search")
        return []

    query = f'"{candidate_name}" Maine 2026 event OR rally OR "town hall" OR appearance OR schedule'
    try:
        resp = requests.get(
            BRAVE_SEARCH_URL,
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            params={"q": query, "count": num_results, "freshness": "pm"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        urls = []
        for result in data.get("web", {}).get("results", []):
            url = result.get("url", "")
            if url:
                urls.append(url)
        logger.info(f"Brave search for {candidate_name}: {len(urls)} results")
        return urls
    except Exception as e:
        logger.warning(f"Brave search failed for {candidate_name}: {e}")
        return []
