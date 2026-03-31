from src.merger import merge_cases


def test_merge_combines_sources():
    calendar = {
        "And-24-525": {
            "docket_number": "And-24-525",
            "case_name": "State v. Hart",
            "county": "Androscoggin",
            "attorney_appellant": "Doe",
            "attorney_appellee": "Smith",
            "trial_judge": "",
            "subject": "",
            "status": "Scheduled",
            "argument_date": "April 7, 2026",
            "decision_date": "",
            "outcome": "",
            "brief_links": ["https://example.com/brief.pdf"],
            "opinion_link": "",
            "summary": "Test case.",
        }
    }
    memoranda = {
        "And-24-525": {
            "docket_number": "And-24-525",
            "case_name": "State v. Hart",
            "county": "Androscoggin",
            "attorney_appellant": "",
            "attorney_appellee": "",
            "trial_judge": "Murphy",
            "subject": "Criminal",
            "status": "Decided",
            "argument_date": "",
            "decision_date": "3/26/26",
            "outcome": "Affirmed",
            "brief_links": [],
            "opinion_link": "",
            "summary": "",
        }
    }
    merged = merge_cases(calendar, memoranda, {}, {})

    case = merged["And-24-525"]
    assert case["status"] == "Decided"
    assert case["trial_judge"] == "Murphy"
    assert case["argument_date"] == "April 7, 2026"
    assert case["outcome"] == "Affirmed"
    assert case["attorney_appellant"] == "Doe"
    assert len(case["brief_links"]) >= 1


def test_merge_briefing_status_from_prober():
    probed = {
        "25-999": {
            "docket_number": "25-999",
            "case_name": "",
            "county": "",
            "attorney_appellant": "",
            "attorney_appellee": "",
            "trial_judge": "",
            "subject": "",
            "status": "Briefing",
            "argument_date": "",
            "decision_date": "",
            "outcome": "",
            "brief_links": ["https://example.com/brief.pdf"],
            "opinion_link": "",
            "summary": "",
        }
    }
    merged = merge_cases({}, {}, {}, probed)
    assert "25-999" in merged
    assert merged["25-999"]["status"] == "Briefing"


def test_merge_deduplicates_brief_links():
    source1 = {
        "And-24-525": {
            "docket_number": "And-24-525",
            "case_name": "Test",
            "county": "",
            "attorney_appellant": "",
            "attorney_appellee": "",
            "trial_judge": "",
            "subject": "",
            "status": "Scheduled",
            "argument_date": "",
            "decision_date": "",
            "outcome": "",
            "brief_links": ["https://example.com/a.pdf", "https://example.com/b.pdf"],
            "opinion_link": "",
            "summary": "",
        }
    }
    source2 = {
        "And-24-525": {
            "docket_number": "And-24-525",
            "case_name": "Test",
            "county": "",
            "attorney_appellant": "",
            "attorney_appellee": "",
            "trial_judge": "",
            "subject": "",
            "status": "Scheduled",
            "argument_date": "",
            "decision_date": "",
            "outcome": "",
            "brief_links": ["https://example.com/b.pdf", "https://example.com/c.pdf"],
            "opinion_link": "",
            "summary": "",
        }
    }
    merged = merge_cases(source1, source2, {}, {})
    assert len(merged["And-24-525"]["brief_links"]) == 3
