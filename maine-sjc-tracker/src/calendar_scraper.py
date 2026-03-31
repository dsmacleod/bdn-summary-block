"""Scrape the Maine Law Court oral argument calendar."""

import re
from bs4 import BeautifulSoup
from src.constants import COUNTY_CODES, BASE_URL


def parse_calendar(html: str) -> dict:
    """Parse calendar HTML, return dict of docket_number -> case dict."""
    soup = BeautifulSoup(html, "html.parser")
    cases = {}
    current_date = ""

    for element in soup.find_all(["h3", "table"]):
        if element.name == "h3" and "Oral Argument" in element.get_text():
            # Extract date from "Oral Arguments: Tuesday, April 7, 2026\nat the..."
            text = element.get_text()
            match = re.search(
                r"Oral Arguments?:\s*\w+,\s*(.+?)(?:\s*at\s|\s*$)", text
            )
            if match:
                current_date = match.group(1).strip()
            else:
                current_date = (
                    text.replace("Oral Arguments:", "")
                    .replace("Oral Argument:", "")
                    .strip()
                    .split("\n")[0]
                    .strip()
                )
        elif element.name == "table" and current_date:
            for row in element.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue

                docket = cells[1].get_text(strip=True)
                if not re.match(r"[A-Za-z]+-\d+-\d+", docket):
                    continue

                county_code = docket.split("-")[0]
                county = COUNTY_CODES.get(county_code, county_code)

                # Attorneys separated by semicolons
                attorneys_text = cells[3].get_text(strip=True)
                attorneys = [a.strip() for a in attorneys_text.split(";")]
                attorney_appellant = attorneys[0] if len(attorneys) >= 1 else ""
                attorney_appellee = attorneys[1] if len(attorneys) >= 2 else ""

                # Brief links from the Topics & Briefs cell
                briefs_cell = cells[4]
                brief_links = []
                for a_tag in briefs_cell.find_all("a", href=True):
                    href = a_tag["href"]
                    if href.startswith("javascript:"):
                        continue
                    if not href.startswith("http"):
                        href = f"{BASE_URL}/{href}"
                    brief_links.append(href)

                # Summary from hidden div
                summary = ""
                summary_div = briefs_cell.find("div", class_="summary")
                if summary_div:
                    summary = summary_div.get_text(strip=True)

                cases[docket] = {
                    "docket_number": docket,
                    "case_name": cells[2].get_text(strip=True),
                    "county": county,
                    "attorney_appellant": attorney_appellant,
                    "attorney_appellee": attorney_appellee,
                    "trial_judge": "",
                    "subject": "",
                    "status": "Scheduled",
                    "argument_date": current_date,
                    "decision_date": "",
                    "outcome": "",
                    "brief_links": brief_links,
                    "opinion_link": "",
                    "summary": summary,
                }

    return cases
