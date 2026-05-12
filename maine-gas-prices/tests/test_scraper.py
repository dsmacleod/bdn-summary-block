import os
import pytest
from fetch_prices import parse_state_average, parse_national_average, parse_state_trend, parse_counties

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

def _load(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()

def test_parse_state_average_happy():
    html = _load("aaa-happy.html")
    avg = parse_state_average(html)
    assert isinstance(avg, float)
    assert 1.0 < avg < 10.0

def test_parse_national_average_happy():
    html = _load("aaa-happy.html")
    avg = parse_national_average(html)
    assert isinstance(avg, float)
    assert 1.0 < avg < 10.0

def test_parse_state_trend_happy():
    html = _load("aaa-happy.html")
    trend = parse_state_trend(html)
    assert set(trend.keys()) == {"week_ago", "month_ago", "year_ago"}
    for v in trend.values():
        assert 1.0 < v < 10.0

def test_parse_counties_happy():
    js = _load("aaa-map-cfg-happy.js")
    counties = parse_counties(js)
    assert len(counties) == 16
    names = {c["name"] for c in counties}
    expected = {"Androscoggin","Aroostook","Cumberland","Franklin","Hancock",
                "Kennebec","Knox","Lincoln","Oxford","Penobscot","Piscataquis",
                "Sagadahoc","Somerset","Waldo","Washington","York"}
    assert names == expected
    for c in counties:
        assert "fips" in c and c["fips"].startswith("23")
        assert 1.0 < c["avg_regular"] < 10.0
