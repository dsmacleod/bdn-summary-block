import re

import responses
from src.brief_prober import probe_briefs


@responses.activate
def test_probe_finds_new_brief():
    responses.add(
        responses.HEAD,
        "https://www.courts.maine.gov/courts/sjc/briefs/2026-03/25-500 Appellant brief.pdf",
        status=200,
    )
    responses.add(responses.HEAD, url=re.compile(r".*"), status=404)

    found = probe_briefs(
        year_short="25",
        seq_start=499,
        seq_end=502,
        months=["2026-03"],
    )
    assert "25-500" in found
    assert len(found["25-500"]) >= 1


@responses.activate
def test_probe_stops_after_consecutive_misses():
    responses.add(responses.HEAD, url=re.compile(r".*"), status=404)

    found = probe_briefs(
        year_short="25",
        seq_start=900,
        seq_end=915,
        months=["2026-03"],
        max_consecutive_misses=5,
    )
    assert len(found) == 0
