import os
import pytest
from fetch_prices import parse_state_average, parse_national_average, parse_state_trend

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
