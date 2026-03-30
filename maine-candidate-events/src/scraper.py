"""Main scraper orchestrator for Maine candidate events."""

import logging
import os
import re
from datetime import date, datetime

import yaml

from src.fetcher import fetch_page, search_candidate_events
from src.extractor import extract_events
from src.airtable_client import AirtableClient
from src.mobilize_source import fetch_mobilize_events

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
            # Validate date format and skip past events
            if not re.match(r"^\d{4}-\d{2}-\d{2}", dt):
                logger.warning(f"Skipping invalid date '{dt}' for {name}")
                continue
            try:
                event_date = datetime.fromisoformat(dt).date()
                if event_date < date.today():
                    logger.debug(f"Skipping past event: {name} on {dt}")
                    continue
            except ValueError:
                logger.warning(f"Skipping unparseable date '{dt}' for {name}")
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

    # Build candidate-to-race lookup
    candidate_races = {}
    for race_key, race_label in RACE_LABELS.items():
        for c in config.get(race_key, []):
            candidate_races[c["name"]] = race_label

    # 1. Mobilize.us events
    total = 0
    mobilize_events = fetch_mobilize_events()
    for evt in mobilize_events:
        dt = evt["date_time"]
        location = evt["location"]
        candidate = evt.get("candidate", "")
        if not candidate:
            continue
        race = candidate_races.get(candidate, "")
        if not race:
            continue
        if client.is_duplicate(candidate, dt, location):
            continue
        record = {
            "Candidate": candidate,
            "Race": race,
            "Event Type": evt.get("event_type", "Other"),
            "Date & Time": dt,
            "Location": location,
            "Source URL": evt.get("source_url", ""),
            "Source": "Campaign Website",
            "Last Verified": date.today().isoformat(),
        }
        client.add_event(record)
        total += 1
        logger.info(f"Mobilize: {candidate} - {evt.get('event_type')} on {dt} at {location}")

    # 2. Web scraping + Brave search
    for race_key, race_label in RACE_LABELS.items():
        candidates = config.get(race_key, [])
        for candidate in candidates:
            count = process_candidate(candidate, race_label, client)
            total += count
            logger.info(f"{candidate['name']}: {count} new events")

    logger.info(f"Done. {total} new events added.")


if __name__ == "__main__":
    main()
