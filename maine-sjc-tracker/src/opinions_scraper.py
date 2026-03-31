"""Scrape Maine Law Court published opinions."""

import re
from bs4 import BeautifulSoup
from src.constants import BASE_URL


def parse_opinions(html: str) -> dict:
    """Parse opinions HTML. Returns dict keyed by opinion number."""
    soup = BeautifulSoup(html, "html.parser")
    cases = {}

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            opinion_num = cells[0].get_text(strip=True)
            if not re.match(r"\d{4}\s+ME\s+\d+", opinion_num):
                continue

            link_tag = cells[1].find("a", href=True)
            case_name = cells[1].get_text(strip=True)
            opinion_link = ""
            if link_tag:
                href = link_tag["href"]
                if not href.startswith("http"):
                    opinion_link = f"{BASE_URL}/{href}"
                else:
                    opinion_link = href

            cases[opinion_num] = {
                "docket_number": "",
                "case_name": case_name,
                "county": "",
                "attorney_appellant": "",
                "attorney_appellee": "",
                "trial_judge": "",
                "subject": "",
                "status": "Decided",
                "argument_date": "",
                "decision_date": cells[2].get_text(strip=True),
                "outcome": "",
                "brief_links": [],
                "opinion_link": opinion_link,
                "summary": "",
                "opinion_number": opinion_num,
            }

    return cases
