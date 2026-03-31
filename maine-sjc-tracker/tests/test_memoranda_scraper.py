from pathlib import Path
from src.memoranda_scraper import parse_memoranda

FIXTURE = Path(__file__).parent / "fixtures" / "memoranda_sample.html"


def test_parse_memoranda_extracts_cases():
    html = FIXTURE.read_text()
    cases = parse_memoranda(html)
    assert len(cases) >= 2
    case = list(cases.values())[0]
    assert case["status"] == "Decided"
    assert case["trial_judge"] != ""
    assert case["outcome"] != ""
    assert case["subject"] != ""
    assert case["decision_date"] != ""


def test_parse_memoranda_county_lookup():
    html = FIXTURE.read_text()
    cases = parse_memoranda(html)
    assert cases["And-25-146"]["county"] == "Androscoggin"
    assert cases["Yor-25-375"]["county"] == "York"
    assert cases["BCD-25-339"]["county"] == "Business & Consumer Docket"


def test_parse_memoranda_fields():
    html = FIXTURE.read_text()
    cases = parse_memoranda(html)
    case = cases["And-25-146"]
    assert case["case_name"] == "In re Children of Hillary H."
    assert case["decision_date"] == "3/26/26"
    assert case["trial_judge"] == "Robinson"
    assert case["outcome"] == "Affirmed"
    assert case["subject"] == "Termination of parental rights"
