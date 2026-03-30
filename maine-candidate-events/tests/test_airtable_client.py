from unittest.mock import patch, MagicMock
from src.airtable_client import AirtableClient

def test_get_existing_events_returns_set():
    mock_table = MagicMock()
    mock_table.all.return_value = [
        {"fields": {"Candidate": "Susan Collins", "Date & Time": "2026-04-15T18:00:00.000Z", "Location": "Bangor Civic Center, Bangor"}},
        {"fields": {"Candidate": "Susan Collins", "Date & Time": "2026-04-20T12:00:00.000Z", "Location": "Portland Press Club, Portland"}},
    ]

    with patch("src.airtable_client.Api") as MockApi:
        MockApi.return_value.table.return_value = mock_table
        client = AirtableClient("fake_key", "fake_base", "fake_table")
        existing = client.get_existing_events()
        assert len(existing) == 2

def test_is_duplicate_detects_match():
    with patch("src.airtable_client.Api") as MockApi:
        MockApi.return_value.table.return_value = MagicMock()
        client = AirtableClient("fake_key", "fake_base", "fake_table")
        client._existing = {
            ("susan collins", "2026-04-15", "bangor civic center bangor"),
        }
        assert client.is_duplicate("Susan Collins", "2026-04-15T18:00:00", "Bangor Civic Center, Bangor")

def test_is_duplicate_fuzzy_location():
    with patch("src.airtable_client.Api") as MockApi:
        MockApi.return_value.table.return_value = MagicMock()
        client = AirtableClient("fake_key", "fake_base", "fake_table")
        client._existing = {
            ("susan collins", "2026-04-15", "bangor civic center bangor"),
        }
        assert client.is_duplicate("Susan Collins", "2026-04-15T18:00:00", "Bangor Civic Ctr, Bangor ME")
