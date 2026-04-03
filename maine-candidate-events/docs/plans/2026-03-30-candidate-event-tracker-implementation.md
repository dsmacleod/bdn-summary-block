# Maine Candidate Event Tracker — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a daily Python scraper that finds public events for Maine 2026 candidates and populates an Airtable table.

**Architecture:** Python script fetches candidate campaign sites, Facebook pages, party calendars, and Google results. Raw text is sent to Claude Haiku for structured event extraction. New events are deduplicated and pushed to Airtable. Runs daily via GitHub Actions.

**Tech Stack:** Python 3.11+, requests, trafilatura, googlesearch-python, anthropic, pyairtable, pyyaml, thefuzz

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `candidates.yaml`
- Create: `src/__init__.py`
- Create: `.github/workflows/scrape.yml`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
venv/
.venv/
```

**Step 2: Create `requirements.txt`**

```
requests>=2.31
trafilatura>=1.8
googlesearch-python>=1.2
anthropic>=0.40
pyairtable>=2.3
pyyaml>=6.0
thefuzz>=0.22
python-Levenshtein>=0.25
```

**Step 3: Create `candidates.yaml`**

```yaml
# Maine 2026 Candidate Registry
# Update this file as candidates declare or withdraw

senate:
  - name: Susan Collins
    party: Republican
    sources:
      - https://www.collins.senate.gov/
      - https://www.facebook.com/susancollins
  - name: Janet Mills
    party: Democratic
    sources:
      - https://janetmills.com/
      - https://www.facebook.com/JanetMillsMaine
  - name: Graham Platner
    party: Democratic
    sources:
      - https://www.facebook.com/GrahamPlatnerForMaine
  - name: David Costello
    party: Democratic
    sources: []
  - name: Ethan Alcorn
    party: Independent
    sources: []
  - name: Timothy Rich
    party: Independent
    sources: []
  - name: David Evans
    party: Independent
    sources:
      - https://davidevansforsenate.com/

governor:
  # Democrats
  - name: Shenna Bellows
    party: Democratic
    sources:
      - https://www.facebook.com/ShennaBellows
  - name: Troy Jackson
    party: Democratic
    sources:
      - https://www.facebook.com/SenatorTroyJackson
  - name: Angus King III
    party: Democratic
    sources: []
  - name: Hannah Pingree
    party: Democratic
    sources:
      - https://www.facebook.com/HannahPingree
  - name: Nirav Shah
    party: Democratic
    sources: []
  # Republicans
  - name: Jonathan Bush
    party: Republican
    sources: []
  - name: Bobby Charles
    party: Republican
    sources: []
  - name: David Jones
    party: Republican
    sources: []
  - name: James Libby
    party: Republican
    sources: []
  - name: Garrett Mason
    party: Republican
    sources: []
  - name: Owen McCarthy
    party: Republican
    sources: []
  - name: Ben Midgley
    party: Republican
    sources: []
  - name: Robert Wessels
    party: Republican
    sources: []
  # Independents
  - name: Richard Bennett
    party: Independent
    sources:
      - https://bennettforgovernor.com/
  - name: W. Edward Crockett
    party: Independent
    sources: []
  - name: John Glowa
    party: Independent
    sources:
      - https://johnglowaforgovernor.com/
  - name: Derek Levasseur
    party: Independent
    sources: []
  - name: Alexander Murchison
    party: Independent
    sources: []

cd1:
  - name: Chellie Pingree
    party: Democratic
    sources:
      - https://www.pingree.house.gov/
      - https://www.facebook.com/RepChelliePingree
  - name: Joshua Pietrowicz
    party: Republican
    sources: []
  - name: Ronald Russell
    party: Republican
    sources: []

cd2:
  - name: Joe Baldacci
    party: Democratic
    sources: []
  - name: Matthew Dunlap
    party: Democratic
    sources: []
  - name: Paige Loud
    party: Democratic
    sources: []
  - name: Jordan Wood
    party: Democratic
    sources: []
  - name: Paul LePage
    party: Republican
    sources:
      - https://www.facebook.com/PaulLePage
```

**Step 4: Create GitHub Actions workflow `.github/workflows/scrape.yml`**

```yaml
name: Scrape Candidate Events

on:
  schedule:
    - cron: '0 12 * * *'  # Daily at 8am ET
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python -m src.scraper
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          AIRTABLE_API_KEY: ${{ secrets.AIRTABLE_API_KEY }}
          AIRTABLE_BASE_ID: ${{ secrets.AIRTABLE_BASE_ID }}
```

**Step 5: Create empty `src/__init__.py`**

**Step 6: Commit**

```bash
git add -A && git commit -m "feat: project scaffold with candidate registry and CI"
```

---

### Task 2: Airtable Table Setup

**Files:**
- Create: `src/airtable_setup.py`

**Step 1: Write script to create the Airtable table**

```python
"""One-time script to create the Candidate Events table in Airtable."""

import os
from pyairtable import Api
from pyairtable.models.schema import FieldSchema

def create_table():
    api = Api(os.environ["AIRTABLE_API_KEY"])
    base = api.base(os.environ["AIRTABLE_BASE_ID"])

    # We'll create the table via the Airtable MCP tool instead,
    # since pyairtable doesn't support table creation directly.
    # This file documents the schema for reference.
    print("Create table 'Candidate Events' with these fields:")
    print("- Candidate (Single Select)")
    print("- Race (Single Select: Senate, Governor, CD-1, CD-2)")
    print("- Event Type (Single Select: Town Hall, Rally, Debate, Fundraiser, Press Conference, Campaign Stop, Forum, Other)")
    print("- Date & Time (Date with time)")
    print("- Location (Single Line Text)")
    print("- Source URL (URL)")
    print("- Source (Single Select: Campaign Website, Facebook, Party Calendar, News, Other)")
    print("- Last Verified (Date)")

if __name__ == "__main__":
    create_table()
```

**Step 2: Create the table using the Airtable MCP tools**

Use `mcp__claude_ai_Airtable__create_table` on base `appwkB7dSz28n4knq` to create "Candidate Events" with all fields.

**Step 3: Commit**

```bash
git add src/airtable_setup.py && git commit -m "feat: airtable schema reference"
```

---

### Task 3: Web Fetcher Module

**Files:**
- Create: `src/fetcher.py`
- Create: `tests/test_fetcher.py`

**Step 1: Write failing test**

```python
# tests/test_fetcher.py
from unittest.mock import patch, MagicMock
from src.fetcher import fetch_page, search_candidate_events

def test_fetch_page_returns_text():
    with patch("src.fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, text="<html><body>Event on March 5</body></html>"
        )
        result = fetch_page("https://example.com")
        assert result is not None
        assert len(result) > 0

def test_fetch_page_handles_failure():
    with patch("src.fetcher.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")
        result = fetch_page("https://example.com")
        assert result is None

def test_search_candidate_events_returns_urls():
    with patch("src.fetcher.search") as mock_search:
        mock_search.return_value = ["https://example.com/event1", "https://example.com/event2"]
        urls = search_candidate_events("Susan Collins")
        assert len(urls) == 2
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_fetcher.py -v
```

**Step 3: Implement fetcher**

```python
# src/fetcher.py
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_fetcher.py -v
```

**Step 5: Commit**

```bash
git add src/fetcher.py tests/test_fetcher.py && git commit -m "feat: web fetcher module with Google search"
```

---

### Task 4: Claude Event Extraction Module

**Files:**
- Create: `src/extractor.py`
- Create: `tests/test_extractor.py`

**Step 1: Write failing test**

```python
# tests/test_extractor.py
import json
from unittest.mock import patch, MagicMock
from src.extractor import extract_events

SAMPLE_TEXT = """
Join Senator Collins for a Town Hall at the Bangor Civic Center
on April 15, 2026 at 6:00 PM. Open to all constituents.
Also appearing at the Portland Press Club on April 20 at noon.
"""

def test_extract_events_returns_list():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps([
        {
            "event_type": "Town Hall",
            "date_time": "2026-04-15T18:00:00",
            "location": "Bangor Civic Center, Bangor",
            "source_url": "https://example.com"
        },
        {
            "event_type": "Campaign Stop",
            "date_time": "2026-04-20T12:00:00",
            "location": "Portland Press Club, Portland",
            "source_url": "https://example.com"
        }
    ]))]

    with patch("src.extractor.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        events = extract_events("Susan Collins", SAMPLE_TEXT, "https://example.com")
        assert len(events) == 2
        assert events[0]["event_type"] == "Town Hall"
        assert events[1]["location"] == "Portland Press Club, Portland"

def test_extract_events_handles_no_events():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="[]")]

    with patch("src.extractor.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        events = extract_events("Susan Collins", "No events here.", "https://example.com")
        assert events == []
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_extractor.py -v
```

**Step 3: Implement extractor**

```python
# src/extractor.py
import json
import logging
import anthropic

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract all upcoming political campaign events from the following text for the candidate "{candidate_name}".

For each event, return a JSON object with:
- event_type: one of "Town Hall", "Rally", "Debate", "Fundraiser", "Press Conference", "Campaign Stop", "Forum", "Other"
- date_time: ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If no time is given, use T00:00:00.
- location: venue name and city/town (e.g., "Bangor Civic Center, Bangor")
- source_url: "{source_url}"

Return ONLY a JSON array. If no events are found, return [].
Do NOT include past events (before today's date).
Do NOT hallucinate events — only extract events explicitly mentioned in the text.

Text:
{text}
"""

def extract_events(
    candidate_name: str, text: str, source_url: str
) -> list[dict]:
    """Use Claude to extract structured events from raw text."""
    if not text or not text.strip():
        return []

    client = anthropic.Anthropic()
    prompt = EXTRACTION_PROMPT.format(
        candidate_name=candidate_name,
        source_url=source_url,
        text=text[:8000],  # Limit input size
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        events = json.loads(raw)
        return events if isinstance(events, list) else []
    except Exception as e:
        logger.warning(f"Extraction failed for {candidate_name}: {e}")
        return []
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_extractor.py -v
```

**Step 5: Commit**

```bash
git add src/extractor.py tests/test_extractor.py && git commit -m "feat: Claude-powered event extraction"
```

---

### Task 5: Airtable Client Module

**Files:**
- Create: `src/airtable_client.py`
- Create: `tests/test_airtable_client.py`

**Step 1: Write failing test**

```python
# tests/test_airtable_client.py
from unittest.mock import patch, MagicMock
from src.airtable_client import AirtableClient

def test_get_existing_events_returns_set():
    mock_table = MagicMock()
    mock_table.all.return_value = [
        {"fields": {"Candidate": "Susan Collins", "Date & Time": "2026-04-15T18:00:00.000Z", "Location": "Bangor Civic Center, Bangor"}},
        {"fields": {"Candidate": "Susan Collins", "Date & Time": "2026-04-20T12:00:00.000Z", "Location": "Portland Press Club, Portland"}},
    ]

    with patch("src.airtable_client.Api") as MockApi:
        MockApi.return_value.table.return_value = mock_table
        client = AirtableClient("fake_key", "fake_base", "fake_table")
        existing = client.get_existing_events()
        assert len(existing) == 2

def test_is_duplicate_detects_match():
    with patch("src.airtable_client.Api") as MockApi:
        MockApi.return_value.table.return_value = MagicMock()
        client = AirtableClient("fake_key", "fake_base", "fake_table")
        client._existing = {
            ("susan collins", "2026-04-15", "bangor civic center bangor"),
        }
        assert client.is_duplicate("Susan Collins", "2026-04-15T18:00:00", "Bangor Civic Center, Bangor")

def test_is_duplicate_fuzzy_location():
    with patch("src.airtable_client.Api") as MockApi:
        MockApi.return_value.table.return_value = MagicMock()
        client = AirtableClient("fake_key", "fake_base", "fake_table")
        client._existing = {
            ("susan collins", "2026-04-15", "bangor civic center bangor"),
        }
        assert client.is_duplicate("Susan Collins", "2026-04-15T18:00:00", "Bangor Civic Ctr, Bangor ME")
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_airtable_client.py -v
```

**Step 3: Implement Airtable client**

```python
# src/airtable_client.py
import logging
import re
from pyairtable import Api
from thefuzz import fuzz

logger = logging.getLogger(__name__)

def _normalize_location(loc: str) -> str:
    """Normalize location for comparison."""
    return re.sub(r"[^a-z0-9 ]", "", loc.lower()).strip()

class AirtableClient:
    def __init__(self, api_key: str, base_id: str, table_name: str):
        api = Api(api_key)
        self.table = api.table(base_id, table_name)
        self._existing: set[tuple[str, str, str]] = set()

    def get_existing_events(self) -> set[tuple[str, str, str]]:
        """Load existing events as (candidate, date, normalized_location) tuples."""
        records = self.table.all()
        self._existing = set()
        for r in records:
            f = r.get("fields", {})
            candidate = (f.get("Candidate") or "").lower()
            dt = (f.get("Date & Time") or "")[:10]
            loc = _normalize_location(f.get("Location") or "")
            self._existing.add((candidate, dt, loc))
        return self._existing

    def is_duplicate(self, candidate: str, date_time: str, location: str) -> bool:
        """Check if an event already exists, with fuzzy location matching."""
        cand = candidate.lower()
        dt = date_time[:10]
        loc = _normalize_location(location)

        for ex_cand, ex_dt, ex_loc in self._existing:
            if ex_cand == cand and ex_dt == dt:
                if fuzz.ratio(loc, ex_loc) > 80:
                    return True
        return False

    def add_event(self, event: dict) -> None:
        """Add a new event record to Airtable."""
        self.table.create(event)
        # Update local cache
        cand = (event.get("Candidate") or "").lower()
        dt = (event.get("Date & Time") or "")[:10]
        loc = _normalize_location(event.get("Location") or "")
        self._existing.add((cand, dt, loc))
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_airtable_client.py -v
```

**Step 5: Commit**

```bash
git add src/airtable_client.py tests/test_airtable_client.py && git commit -m "feat: Airtable client with fuzzy deduplication"
```

---

### Task 6: Main Scraper Orchestrator

**Files:**
- Create: `src/scraper.py`
- Create: `tests/test_scraper.py`

**Step 1: Write failing test**

```python
# tests/test_scraper.py
from unittest.mock import patch, MagicMock
from src.scraper import process_candidate

def test_process_candidate_finds_and_adds_events():
    candidate = {
        "name": "Susan Collins",
        "party": "Republican",
        "sources": ["https://example.com/events"],
    }
    mock_client = MagicMock()
    mock_client.is_duplicate.return_value = False

    with patch("src.scraper.fetch_page", return_value="Town hall April 15 at Bangor Civic Center"):
        with patch("src.scraper.search_candidate_events", return_value=["https://news.example.com"]):
            with patch("src.scraper.extract_events", return_value=[{
                "event_type": "Town Hall",
                "date_time": "2026-04-15T18:00:00",
                "location": "Bangor Civic Center, Bangor",
                "source_url": "https://example.com/events",
            }]):
                added = process_candidate(candidate, "Senate", mock_client)
                assert added == 1
                mock_client.add_event.assert_called_once()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scraper.py -v
```

**Step 3: Implement scraper**

```python
# src/scraper.py
"""Main scraper orchestrator for Maine candidate events."""

import logging
import os
from datetime import date

import yaml

from src.fetcher import fetch_page, search_candidate_events
from src.extractor import extract_events
from src.airtable_client import AirtableClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RACE_LABELS = {
    "senate": "Senate",
    "governor": "Governor",
    "cd1": "CD-1",
    "cd2": "CD-2",
}

SOURCE_MAP = {
    "facebook.com": "Facebook",
    "gop.com": "Party Calendar",
    "mainedems.org": "Party Calendar",
    "senate.gov": "Campaign Website",
    "house.gov": "Campaign Website",
}

def classify_source(url: str) -> str:
    """Classify a URL into a source category."""
    url_lower = url.lower()
    for domain, label in SOURCE_MAP.items():
        if domain in url_lower:
            return label
    if any(kw in url_lower for kw in ["campaign", "com/events", "forsenate", "forgovernor", "forcongress"]):
        return "Campaign Website"
    return "News"

def process_candidate(
    candidate: dict, race: str, client: AirtableClient
) -> int:
    """Scrape and process events for one candidate. Returns count of new events added."""
    name = candidate["name"]
    sources = candidate.get("sources", [])
    all_texts: list[tuple[str, str]] = []  # (text, source_url)

    # Fetch direct sources
    for url in sources:
        text = fetch_page(url)
        if text:
            all_texts.append((text, url))

    # Google search
    search_urls = search_candidate_events(name)
    for url in search_urls:
        if url not in sources:
            text = fetch_page(url)
            if text:
                all_texts.append((text, url))

    # Extract events from all collected text
    added = 0
    for text, source_url in all_texts:
        events = extract_events(name, text, source_url)
        for event in events:
            dt = event.get("date_time", "")
            location = event.get("location", "")
            if not dt or not location:
                continue
            if client.is_duplicate(name, dt, location):
                logger.debug(f"Skipping duplicate: {name} on {dt} at {location}")
                continue

            record = {
                "Candidate": name,
                "Race": race,
                "Event Type": event.get("event_type", "Other"),
                "Date & Time": dt,
                "Location": location,
                "Source URL": event.get("source_url", source_url),
                "Source": classify_source(source_url),
                "Last Verified": date.today().isoformat(),
            }
            client.add_event(record)
            added += 1
            logger.info(f"Added: {name} - {event.get('event_type')} on {dt} at {location}")

    return added

def main():
    config_path = os.path.join(os.path.dirname(__file__), "..", "candidates.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    client = AirtableClient(
        api_key=os.environ["AIRTABLE_API_KEY"],
        base_id=os.environ["AIRTABLE_BASE_ID"],
        table_name="Candidate Events",
    )
    client.get_existing_events()

    total = 0
    for race_key, race_label in RACE_LABELS.items():
        candidates = config.get(race_key, [])
        for candidate in candidates:
            count = process_candidate(candidate, race_label, client)
            total += count
            logger.info(f"{candidate['name']}: {count} new events")

    logger.info(f"Done. {total} new events added.")

if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scraper.py -v
```

**Step 5: Create `tests/__init__.py`**

**Step 6: Commit**

```bash
git add src/scraper.py tests/ && git commit -m "feat: main scraper orchestrator"
```

---

### Task 7: Create Airtable Table via MCP

**No files — uses MCP tools.**

**Step 1:** Call `mcp__claude_ai_Airtable__create_table` on base `appwkB7dSz28n4knq` with table name "Candidate Events" and all fields defined in the design doc.

**Step 2:** Verify table was created with `mcp__claude_ai_Airtable__list_tables_for_base`.

---

### Task 8: End-to-End Test and README

**Files:**
- Modify: `README.md`

**Step 1: Write README**

```markdown
# Maine Candidate Event Tracker

Automated daily scraper that finds public events for Maine 2026 candidates and populates an Airtable table for the BDN newsroom.

## Races Tracked
- US Senate (Collins' seat) — **priority**
- Governor
- US House CD-1
- US House CD-2

## Setup

1. Clone this repo
2. `pip install -r requirements.txt`
3. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
4. Run: `python -m src.scraper`

## Updating Candidates

Edit `candidates.yaml` to add/remove candidates or update their source URLs.

## GitHub Actions

Runs daily at 8am ET. Can also be triggered manually from the Actions tab.
```

**Step 2: Run the scraper manually against real Airtable** (after secrets are configured)

```bash
ANTHROPIC_API_KEY=... AIRTABLE_API_KEY=... AIRTABLE_BASE_ID=appwkB7dSz28n4knq python -m src.scraper
```

**Step 3: Commit**

```bash
git add README.md && git commit -m "docs: add README"
```
