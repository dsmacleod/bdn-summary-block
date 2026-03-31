from unittest.mock import MagicMock, patch
from src.sheets_writer import upsert_cases
from src.constants import SHEET_COLUMNS


def test_upsert_appends_new_case():
    mock_sheet = MagicMock()
    mock_sheet.get_all_records.return_value = []
    mock_sheet.row_values.return_value = SHEET_COLUMNS

    cases = {
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
            "summary": "A test case.",
        }
    }

    result = upsert_cases(mock_sheet, cases)
    mock_sheet.append_row.assert_called_once()
    assert result["added"] == 1
    assert result["updated"] == 0


def test_upsert_updates_existing_case():
    mock_sheet = MagicMock()
    mock_sheet.get_all_records.return_value = [
        {"Docket Number": "And-24-525", "Status": "Scheduled", "First Seen": "2026-03-01"}
    ]
    mock_sheet.row_values.return_value = SHEET_COLUMNS
    mock_sheet.find.return_value = MagicMock(row=2)

    cases = {
        "And-24-525": {
            "docket_number": "And-24-525",
            "case_name": "State v. Hart",
            "county": "Androscoggin",
            "attorney_appellant": "",
            "attorney_appellee": "",
            "trial_judge": "Murphy",
            "subject": "",
            "status": "Decided",
            "argument_date": "",
            "decision_date": "3/26/26",
            "outcome": "Affirmed",
            "brief_links": [],
            "opinion_link": "",
            "summary": "",
        }
    }

    result = upsert_cases(mock_sheet, cases)
    mock_sheet.update.assert_called()
    assert result["updated"] == 1
    assert result["added"] == 0
