import os
import pytest
from fetch_prices import parse_state_average

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

def _load(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()

def test_parse_state_average_happy():
    html = _load("aaa-happy.html")
    avg = parse_state_average(html)
    assert isinstance(avg, float)
    assert 1.0 < avg < 10.0
