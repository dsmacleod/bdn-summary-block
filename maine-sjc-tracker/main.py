"""Maine SJC Case Tracker — entry point."""

import json
import os
import sys
from datetime import date

import gspread
from google.oauth2.service_account import Credentials

from src.http_client import fetch_page
from src.calendar_scraper import parse_calendar
from src.memoranda_scraper import parse_memoranda
from src.opinions_scraper import parse_opinions
from src.brief_prober import probe_briefs
from src.merger import merge_cases
from src.sheets_writer import upsert_cases
from src.constants import CALENDAR_URL, MEMORANDA_URL, OPINIONS_URL


def get_sheet():
    """Authenticate and return the Google Sheet worksheet."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not creds_json or not sheet_id:
        print("Error: Set GOOGLE_CREDENTIALS_JSON and GOOGLE_SHEET_ID env vars")
        sys.exit(1)

    creds_dict = json.loads(creds_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    return spreadsheet.sheet1


def get_probe_months() -> list[str]:
    """Generate recent month folder names to probe."""
    today = date.today()
    months = []
    for offset in range(3):
        m = today.month - offset
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        months.append(f"{y}-{m:02d}")
    return months


def main():
    print("=== Maine SJC Case Tracker ===")

    # 1. Scrape calendar
    print("Scraping calendar...")
    calendar_html = fetch_page(CALENDAR_URL)
    calendar_cases = parse_calendar(calendar_html)
    print(f"  Found {len(calendar_cases)} cases on calendar")

    # 2. Scrape memoranda
    print("Scraping memoranda...")
    memoranda_html = fetch_page(MEMORANDA_URL)
    memoranda_cases = parse_memoranda(memoranda_html)
    print(f"  Found {len(memoranda_cases)} memoranda decisions")

    # 3. Scrape opinions
    print("Scraping opinions...")
    opinions_html = fetch_page(OPINIONS_URL)
    opinions_cases = parse_opinions(opinions_html)
    print(f"  Found {len(opinions_cases)} published opinions")

    # 4. Probe briefs
    print("Probing briefs directory...")
    months = get_probe_months()
    today = date.today()
    probed_cases = {}

    for year_offset in range(2):
        yr = today.year - year_offset
        yr_short = str(yr)[-2:]
        found = probe_briefs(
            year_short=yr_short,
            seq_start=1,
            seq_end=600,
            months=months,
        )
        for docket_short, briefs in found.items():
            full_dockets = set(calendar_cases.keys()) | set(memoranda_cases.keys())
            already_known = any(docket_short in d for d in full_dockets)
            if not already_known:
                probed_cases[docket_short] = {
                    "docket_number": docket_short,
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
                    "brief_links": briefs,
                    "opinion_link": "",
                    "summary": "",
                }

    print(f"  Found {len(probed_cases)} cases via brief probing")

    # 5. Merge
    print("Merging cases...")
    all_cases = merge_cases(calendar_cases, memoranda_cases, opinions_cases, probed_cases)
    print(f"  Total unique cases: {len(all_cases)}")

    # 6. Write to Google Sheets
    print("Writing to Google Sheets...")
    sheet = get_sheet()
    result = upsert_cases(sheet, all_cases)
    print(f"  Added: {result['added']}, Updated: {result['updated']}")

    print("Done!")


if __name__ == "__main__":
    main()
