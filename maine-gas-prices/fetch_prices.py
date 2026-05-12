import re

def parse_state_average(html: str) -> float:
    """Extract Maine's regular-gas state average from the AAA state-page HTML.

    Target markup (first table on the state page):
        <td>Current Avg.</td>
        <td>$4.539</td>   <-- regular (first $ after the label)
    """
    m = re.search(r'Current Avg\.\s*</td>\s*<td>\s*\$(\d+\.\d{2,3})', html, re.DOTALL)
    if not m:
        raise ValueError("Could not locate Maine state average in AAA HTML")
    return float(m.group(1))
