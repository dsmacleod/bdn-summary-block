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
    all_texts: list = []  # list of (text, source_url)

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
