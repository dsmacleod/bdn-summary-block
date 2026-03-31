from pathlib import Path
from src.opinions_scraper import parse_opinions

FIXTURE = Path(__file__).parent / "fixtures" / "opinions_sample.html"


def test_parse_opinions_extracts_cases():
    html = FIXTURE.read_text()
    cases = parse_opinions(html)
    assert len(cases) >= 2
    case = list(cases.values())[0]
    assert case["case_name"] != ""
    assert case["status"] == "Decided"
    assert case["decision_date"] != ""
    assert case["opinion_link"] != ""
    assert ".pdf" in case["opinion_link"]


def test_parse_opinions_correct_values():
    html = FIXTURE.read_text()
    cases = parse_opinions(html)
    assert "2026 ME 29" in cases
    assert cases["2026 ME 29"]["case_name"] == "Alexis Harriman v. Dillon Lamothe et al."
    assert cases["2026 ME 29"]["decision_date"] == "March 26, 2026"
    assert cases["2026 ME 29"]["opinion_number"] == "2026 ME 29"


def test_parse_opinions_link_format():
    html = FIXTURE.read_text()
    cases = parse_opinions(html)
    link = cases["2026 ME 29"]["opinion_link"]
    assert link.startswith("https://")
    assert link.endswith(".pdf")
