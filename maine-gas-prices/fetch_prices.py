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

def parse_national_average(html: str) -> float:
    """Extract the US national average from the AAA state-page HTML.

    Target markup:
        <p>Today's AAA<br />
        National Average </p>
        <p class="numb">
          $4.546 ...
    """
    m = re.search(
        r'National Average\s*</p>\s*<p[^>]*class="numb"[^>]*>\s*\$(\d+\.\d{2,3})',
        html, re.DOTALL,
    )
    if not m:
        raise ValueError("Could not locate national average in AAA HTML")
    return float(m.group(1))

def parse_state_trend(html: str) -> dict:
    """Pull the Week/Month/Year-ago regular-gas averages from the state trend table.

    Target markup (each in the first such table):
        <td>Week Ago Avg.</td>
        <td>$4.323</td>   <-- regular (first $ after the label)
    """
    keys = [("week_ago", "Week Ago Avg."), ("month_ago", "Month Ago Avg."), ("year_ago", "Year Ago Avg.")]
    out = {}
    for k, label in keys:
        m = re.search(
            rf'{re.escape(label)}\s*</td>\s*<td>\s*\$(\d+\.\d{{2,3}})',
            html, re.DOTALL,
        )
        if not m:
            raise ValueError(f"Could not locate '{label}' in AAA HTML")
        out[k] = float(m.group(1))
    return out
