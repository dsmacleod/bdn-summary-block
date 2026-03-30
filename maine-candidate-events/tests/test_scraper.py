from unittest.mock import patch, MagicMock
from src.scraper import process_candidate


def test_process_candidate_finds_and_adds_events():
    candidate = {
        "name": "Susan Collins",
        "party": "Republican",
        "sources": ["https://example.com/events"],
    }
    mock_client = MagicMock()
    mock_client.is_duplicate.return_value = False

    with patch("src.scraper.fetch_page", return_value="Town hall April 15 at Bangor Civic Center"):
        with patch("src.scraper.search_candidate_events", return_value=["https://news.example.com"]):
            with patch("src.scraper.extract_events", return_value=[{
                "event_type": "Town Hall",
                "date_time": "2026-04-15T18:00:00",
                "location": "Bangor Civic Center, Bangor",
                "source_url": "https://example.com/events",
            }]):
                added = process_candidate(candidate, "Senate", mock_client)
                assert added == 2
                assert mock_client.add_event.call_count == 2
