"""Scrape Maine Law Court memoranda of decision."""

import re
from bs4 import BeautifulSoup
from src.constants import COUNTY_CODES


def parse_memoranda(html: str) -> dict:
    """Parse memoranda HTML, return dict of docket_number -> case dict."""
    soup = BeautifulSoup(html, "html.parser")
    cases = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            docket = cells[0].get_text(strip=True)
            if not re.match(r"[A-Za-z]+-\d+-\d+", docket):
                continue

            county_code = docket.split("-")[0]
            county = COUNTY_CODES.get(county_code, county_code)

            cases[docket] = {
                "docket_number": docket,
                "case_name": cells[2].get_text(strip=True),
                "county": county,
                "attorney_appellant": "",
                "attorney_appellee": "",
                "trial_judge": cells[5].get_text(strip=True),
                "subject": cells[4].get_text(strip=True),
                "status": "Decided",
                "argument_date": "",
                "decision_date": cells[3].get_text(strip=True),
                "outcome": cells[6].get_text(strip=True),
                "brief_links": [],
                "opinion_link": "",
                "summary": "",
            }

    return cases
