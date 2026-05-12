import json
import re

ME_FIPS = {
    "Androscoggin": "23001", "Aroostook": "23003", "Cumberland": "23005",
    "Franklin": "23007", "Hancock": "23009", "Kennebec": "23011",
    "Knox": "23013", "Lincoln": "23015", "Oxford": "23017",
    "Penobscot": "23019", "Piscataquis": "23021", "Sagadahoc": "23023",
    "Somerset": "23025", "Waldo": "23027", "Washington": "23029", "York": "23031",
}

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

def parse_counties(map_cfg_js: str) -> list:
    """Extract 16 Maine county prices from AAA's map-config JS blob.

    The config has a line like:
        map_data : {"st1":{"id":1,"name":"Androscoggin","comment":"$4.561",...},
                    "st2":{"id":2,"name":"Aroostook","comment":"$4.522",...}, ...}
    The 'comment' field holds the regular-gas price.
    """
    m = re.search(r'map_data\s*:\s*(\{.*?\})\s*,\s*groups', map_cfg_js, re.DOTALL)
    if not m:
        raise ValueError("Could not locate map_data block in AAA map config JS")
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"map_data is not valid JSON: {e}") from e

    counties = []
    seen = set()
    for entry in data.values():
        name = entry.get("name", "").strip()
        price_str = entry.get("comment", "")
        pm = re.match(r'\$(\d+\.\d{2,3})', price_str)
        if not pm:
            raise ValueError(f"County {name!r} has unparseable price: {price_str!r}")
        if name not in ME_FIPS:
            raise ValueError(f"Unknown Maine county in map_data: {name!r}")
        counties.append({
            "name": name,
            "fips": ME_FIPS[name],
            "avg_regular": float(pm.group(1)),
        })
        seen.add(name)
    missing = set(ME_FIPS) - seen
    if missing:
        raise ValueError(f"Missing counties in map_data: {sorted(missing)}")
    return counties
