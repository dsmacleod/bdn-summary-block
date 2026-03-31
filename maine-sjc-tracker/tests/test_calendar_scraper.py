from pathlib import Path
from src.calendar_scraper import parse_calendar

FIXTURE = Path(__file__).parent / "fixtures" / "calendar_sample.html"


def test_parse_calendar_extracts_cases():
    html = FIXTURE.read_text()
    cases = parse_calendar(html)
    assert len(cases) >= 2

    # Test a case with full data (BCD-25-166 has briefs)
    case = cases["BCD-25-166"]
    assert case["case_name"] == "Bruce MacMillan et al. v. R.M. Davis, Inc."
    assert case["county"] == "Business & Consumer Docket"
    assert case["status"] == "Scheduled"
    assert case["argument_date"] == "April 7, 2026"
    assert case["attorney_appellant"] == "Bruce W. Hepler"
    assert len(case["brief_links"]) == 3
    assert case["summary"] != ""


def test_parse_calendar_no_briefs_yet():
    html = FIXTURE.read_text()
    cases = parse_calendar(html)
    # And-24-525 has "Topics and briefs will be posted soon"
    no_brief_cases = [c for c in cases.values() if not c["brief_links"]]
    assert len(no_brief_cases) >= 1
    assert cases["And-24-525"]["brief_links"] == []


def test_parse_calendar_multiple_dates():
    html = FIXTURE.read_text()
    cases = parse_calendar(html)
    dates = {c["argument_date"] for c in cases.values()}
    assert len(dates) >= 2


def test_parse_calendar_county_lookup():
    html = FIXTURE.read_text()
    cases = parse_calendar(html)
    assert cases["And-24-525"]["county"] == "Androscoggin"
    assert cases["Ken-22-53"]["county"] == "Kennebec"
