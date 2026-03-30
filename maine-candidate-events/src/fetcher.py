from __future__ import annotations

import logging
import requests
import trafilatura
from googlesearch import search

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BDNEventTracker/1.0)"
}

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

def search_candidate_events(candidate_name: str, num_results: int = 5) -> list[str]:
    """Search Google for recent events for a candidate."""
    query = f'"{candidate_name}" Maine 2026 event OR rally OR "town hall" OR appearance'
    try:
        return list(search(query, num_results=num_results))
    except Exception as e:
        logger.warning(f"Google search failed for {candidate_name}: {e}")
        return []
