"""Write case data to Google Sheets."""

from datetime import date
from src.constants import SHEET_COLUMNS

FIELD_TO_COLUMN = {
    "docket_number": "Docket Number",
    "case_name": "Case Name",
    "county": "County",
    "attorney_appellant": "Attorney (Appellant)",
    "attorney_appellee": "Attorney (Appellee)",
    "trial_judge": "Trial Judge",
    "subject": "Subject",
    "status": "Status",
    "argument_date": "Argument Date",
    "decision_date": "Decision Date",
    "outcome": "Outcome",
    "brief_links": "Brief Links",
    "opinion_link": "Opinion Link",
    "summary": "Summary",
}


def _case_to_row(case: dict, first_seen: str = "") -> list:
    """Convert case dict to a row list matching SHEET_COLUMNS order."""
    today = date.today().isoformat()
    row = []
    for col in SHEET_COLUMNS:
        if col == "First Seen":
            row.append(first_seen or today)
        elif col == "Last Updated":
            row.append(today)
        elif col == "Brief Links":
            row.append("\n".join(case.get("brief_links", [])))
        else:
            field = next((k for k, v in FIELD_TO_COLUMN.items() if v == col), None)
            row.append(case.get(field, "") if field else "")
    return row


def upsert_cases(sheet, cases: dict) -> dict:
    """Upsert cases into a Google Sheet. Returns counts of added/updated."""
    existing_records = sheet.get_all_records()
    existing_dockets = {r["Docket Number"]: r for r in existing_records if r.get("Docket Number")}

    added = 0
    updated = 0

    for key, case in cases.items():
        docket = case.get("docket_number", key)

        if docket in existing_dockets:
            existing = existing_dockets[docket]
            first_seen = existing.get("First Seen", "")
            row = _case_to_row(case, first_seen=first_seen)
            cell = sheet.find(docket)
            if cell:
                col_count = len(SHEET_COLUMNS)
                sheet.update(f"A{cell.row}:{chr(64 + col_count)}{cell.row}", [row])
                updated += 1
        else:
            row = _case_to_row(case)
            sheet.append_row(row)
            added += 1

    return {"added": added, "updated": updated}
