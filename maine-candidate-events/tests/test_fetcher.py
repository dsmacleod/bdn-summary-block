from unittest.mock import patch, MagicMock
from src.fetcher import fetch_page, search_candidate_events

def test_fetch_page_returns_text():
    with patch("src.fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, text="<html><body>Event on March 5</body></html>"
        )
        result = fetch_page("https://example.com")
        assert result is not None
        assert len(result) > 0

def test_fetch_page_handles_failure():
    with patch("src.fetcher.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")
        result = fetch_page("https://example.com")
        assert result is None

def test_search_candidate_events_returns_urls():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"url": "https://example.com/event1"},
                {"url": "https://example.com/event2"},
            ]
        }
    }
    with patch("src.fetcher.requests.get", return_value=mock_response):
        with patch.dict("os.environ", {"BRAVE_API_KEY": "test-key"}):
            urls = search_candidate_events("Susan Collins")
            assert len(urls) == 2
