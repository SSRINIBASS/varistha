"""Unit tests for the web page fetcher."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fetcher import extract_title_and_text, fetch_url
from ssrf import SSRFSecurityError


def test_extract_title_and_text_cleans_scripts_and_styles() -> None:
    """HTML tags, javascript scripts, and css styles are cleanly removed."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title> Acme Corporation </title>
        <style>body { background: red; }</style>
    </head>
    <body>
        <h1>Welcome to Acme</h1>
        <script>console.log("secret tracker");</script>
        <p>We build AI agents for modern startups.</p>
        <div>Contact: <a href="mailto:info@acme.com">info@acme.com</a></div>
    </body>
    </html>
    """

    title, text = extract_title_and_text(html)

    assert title == "Acme Corporation"
    assert "console.log" not in text
    assert "background: red" not in text
    assert "Welcome to Acme" in text
    assert "We build AI agents for modern startups." in text
    assert "info@acme.com" in text


@pytest.mark.asyncio
async def test_fetch_url_returns_untrusted_extracted_content() -> None:
    """fetch_url extracts content and flags output as untrusted."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_redirect = False
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_response.text = (
        "<html><head><title>Test Page</title></head><body><p>Clean body text</p></body></html>"
    )

    with (
        patch("fetcher.validate_url_against_ssrf"),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.return_value = mock_response

        result = await fetch_url("https://example.com/test", max_chars=500)

        assert result["status_code"] == 200
        assert result["title"] == "Test Page"
        assert result["content"] == "Clean body text"
        assert result["untrusted"] is True
        assert result["url"] == "https://example.com/test"


@pytest.mark.asyncio
async def test_fetch_url_enforces_ssrf_before_request() -> None:
    """fetch_url rejects blocked URLs immediately without issuing network calls."""
    with (
        patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        pytest.raises(SSRFSecurityError),
    ):
        await fetch_url("http://169.254.169.254/latest/meta-data/")

    mock_get.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_url_redirect_to_blocked_ip_raises_ssrf() -> None:
    """Redirect to private IP in redirect chain is caught and blocked."""
    mock_redirect_response = MagicMock()
    mock_redirect_response.status_code = 302
    mock_redirect_response.is_redirect = True
    mock_redirect_response.headers = {"location": "http://127.0.0.1/admin"}

    with (
        patch("fetcher.validate_url_against_ssrf"),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.return_value = mock_redirect_response
        with pytest.raises(SSRFSecurityError):
            await fetch_url("https://example.com/redirect-to-internal")
