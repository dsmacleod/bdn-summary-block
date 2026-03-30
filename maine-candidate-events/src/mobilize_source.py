"""Fetch upcoming events from Mobilize.us API for Maine campaigns."""

import logging
from datetime import date

import requests

logger = logging.getLogger(__name__)

MOBILIZE_API = "https://api.mobilize.us/v1/events"

# Known Maine campaign/org slugs on Mobilize
MAINE_ORG_SLUGS = [
    "mainedems",
    "jacksonformaine",
    "grahamformaine",
    "millsformaine",
    "chelliepingree",
    "baldacciformaine",
    "dunlapformaine",
    "woodformaine",
    "indivisiblebangor",
    "indivisiblemidmaine",
]


def fetch_mobilize_events() -> list[dict]:
    """Fetch upcoming Maine-related events from Mobilize.us.

    Returns list of dicts with keys: candidate, race, event_type, date_time,
    location, source_url, source.
    """
    events = []

    for slug in MAINE_ORG_SLUGS:
        url = f"https://api.mobilize.us/v1/organizations/{slug}/events"
        try:
            resp = requests.get(
                url,
                params={"timeslot_start": "gte_now", "per_page": 25},
                timeout=10,
            )
            if resp.status_code == 404:
                logger.debug(f"Mobilize org not found: {slug}")
                continue
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Mobilize fetch failed for {slug}: {e}")
            continue

        for evt in data.get("data", []):
            title = evt.get("title", "")
            event_type = _classify_event_type(title, evt.get("event_type", ""))
            browser_url = evt.get("browser_url", "")
            location = evt.get("location", {}) or {}
            venue = location.get("venue", "")
            locality = location.get("locality", "")
            region = location.get("region", "")

            # Only include Maine events
            if region and region != "ME":
                continue

            loc_str = f"{venue}, {locality}" if venue and locality else (venue or locality or "Virtual")

            for timeslot in evt.get("timeslots", []):
                start = timeslot.get("start_date")
                if not start:
                    continue
                # start_date is unix timestamp
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromtimestamp(start, tz=timezone.utc)
                    if dt.date() < date.today():
                        continue
                    dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")
                except Exception:
                    continue

                events.append({
                    "candidate": _extract_candidate(slug, title),
                    "event_type": event_type,
                    "date_time": dt_str,
                    "location": loc_str,
                    "source_url": browser_url,
                    "source": "Campaign Website",
                })

    logger.info(f"Mobilize: found {len(events)} upcoming Maine events")
    return events


def _classify_event_type(title: str, mobilize_type: str) -> str:
    title_lower = title.lower()
    if "town hall" in title_lower:
        return "Town Hall"
    if "rally" in title_lower:
        return "Rally"
    if "debate" in title_lower:
        return "Debate"
    if "forum" in title_lower:
        return "Forum"
    if "fundrais" in title_lower or "finance" in title_lower:
        return "Fundraiser"
    if "press" in title_lower:
        return "Press Conference"
    return "Campaign Stop"


def _extract_candidate(slug: str, title: str) -> str:
    """Best-effort candidate name from org slug."""
    slug_map = {
        "mainedems": "",  # Party events, not candidate-specific
        "jacksonformaine": "Troy Jackson",
        "grahamformaine": "Graham Platner",
        "millsformaine": "Janet Mills",
        "chelliepingree": "Chellie Pingree",
        "baldacciformaine": "Joe Baldacci",
        "dunlapformaine": "Matthew Dunlap",
        "woodformaine": "Jordan Wood",
        "indivisiblebangor": "",
        "indivisiblemidmaine": "",
    }
    return slug_map.get(slug, "")
