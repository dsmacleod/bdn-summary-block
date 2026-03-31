import responses
import pytest
from src.http_client import fetch_page, check_url_exists


@responses.activate
def test_fetch_page_returns_html():
    responses.add(responses.GET, "https://example.com/page", body="<html>hello</html>", status=200)
    result = fetch_page("https://example.com/page")
    assert result == "<html>hello</html>"


@responses.activate
def test_fetch_page_retries_on_failure():
    responses.add(responses.GET, "https://example.com/page", status=500)
    responses.add(responses.GET, "https://example.com/page", status=500)
    responses.add(responses.GET, "https://example.com/page", body="<html>ok</html>", status=200)
    result = fetch_page("https://example.com/page")
    assert result == "<html>ok</html>"


@responses.activate
def test_fetch_page_raises_after_max_retries():
    responses.add(responses.GET, "https://example.com/page", status=500)
    responses.add(responses.GET, "https://example.com/page", status=500)
    responses.add(responses.GET, "https://example.com/page", status=500)
    with pytest.raises(Exception):
        fetch_page("https://example.com/page")


@responses.activate
def test_check_url_exists_true():
    responses.add(responses.HEAD, "https://example.com/file.pdf", status=200)
    assert check_url_exists("https://example.com/file.pdf") is True


@responses.activate
def test_check_url_exists_false():
    responses.add(responses.HEAD, "https://example.com/file.pdf", status=404)
    assert check_url_exists("https://example.com/file.pdf") is False
