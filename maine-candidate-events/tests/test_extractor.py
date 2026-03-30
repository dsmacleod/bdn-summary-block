import json
from unittest.mock import patch, MagicMock
from src.extractor import extract_events

SAMPLE_TEXT = """
Join Senator Collins for a Town Hall at the Bangor Civic Center
on April 15, 2026 at 6:00 PM. Open to all constituents.
Also appearing at the Portland Press Club on April 20 at noon.
"""

def test_extract_events_returns_list():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps([
        {
            "event_type": "Town Hall",
            "date_time": "2026-04-15T18:00:00",
            "location": "Bangor Civic Center, Bangor",
            "source_url": "https://example.com"
        },
        {
            "event_type": "Campaign Stop",
            "date_time": "2026-04-20T12:00:00",
            "location": "Portland Press Club, Portland",
            "source_url": "https://example.com"
        }
    ]))]

    with patch("src.extractor.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        events = extract_events("Susan Collins", SAMPLE_TEXT, "https://example.com")
        assert len(events) == 2
        assert events[0]["event_type"] == "Town Hall"
        assert events[1]["location"] == "Portland Press Club, Portland"

def test_extract_events_handles_no_events():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="[]")]

    with patch("src.extractor.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        events = extract_events("Susan Collins", "No events here.", "https://example.com")
        assert events == []
