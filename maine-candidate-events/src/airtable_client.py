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
