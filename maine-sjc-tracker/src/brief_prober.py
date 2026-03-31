"""Probe the briefs directory for undiscovered cases."""

from src.constants import BRIEFS_BASE_URL
from src.http_client import check_url_exists

BRIEF_TYPES = [
    "Appellant brief",
    "Appellant Brief",
    "Appellants brief",
    "Appellee brief",
    "Appellee Brief",
]


def probe_briefs(
    year_short: str,
    seq_start: int,
    seq_end: int,
    months: list[str],
    max_consecutive_misses: int = 10,
) -> dict:
    """Probe for brief PDFs by sequential docket number.

    Returns dict of "YY-SEQ" -> list of found brief URLs.
    """
    found = {}
    consecutive_misses = 0

    for seq in range(seq_start, seq_end + 1):
        docket_short = f"{year_short}-{seq}"
        briefs_found = []

        for month in months:
            for brief_type in BRIEF_TYPES:
                url = f"{BRIEFS_BASE_URL}/{month}/{docket_short} {brief_type}.pdf"
                if check_url_exists(url):
                    briefs_found.append(url)
                    break  # Found one type in this month, don't check other capitalizations

        if briefs_found:
            found[docket_short] = briefs_found
            consecutive_misses = 0
        else:
            consecutive_misses += 1
            if consecutive_misses >= max_consecutive_misses:
                break

    return found
