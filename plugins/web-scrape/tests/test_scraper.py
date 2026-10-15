"""Tests for web-scrape plugin."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from scraper import (
    convert_html_to_markdown,
    extract_headings_from_html,
    extract_links_from_html,
    extract_metadata,
    scrape_url,
)
from ssrf import SSRFSecurityError


def test_extract_metadata_title_and_description() -> None:
    html = """
    <html>
      <head>
        <title> Acme AI &amp; Robotics </title>
        <meta name="description" content="Autonomous robotics for industrial manufacturing.">
      </head>
      <body><h1>Welcome</h1></body>
    </html>
    """
    title, desc = extract_metadata(html)
    assert title == "Acme AI & Robotics"
    assert desc == "Autonomous robotics for industrial manufacturing."


def test_extract_headings() -> None:
    html = """
    <div>
      <h1>Main Headline</h1>
      <p>Intro</p>
      <h2>Section 1: Overview</h2>
      <h3>Sub-point A</h3>
      <h2>Section 2: Pricing</h2>
    </div>
    """
    headings = extract_headings_from_html(html)
    assert headings == [
        "Main Headline",
        "Section 1: Overview",
        "Sub-point A",
        "Section 2: Pricing",
    ]


def test_extract_links() -> None:
    html = """
    <div>
      <a href="/pricing">View Pricing</a>
      <a href="https://github.com/varistha">GitHub Repo</a>
      <a href="javascript:void(0)">Ignored</a>
      <a href="#section">Anchor Ignored</a>
    </div>
    """
    links = extract_links_from_html(html, "https://varistha.ai/product")
    assert len(links) == 2
    assert links[0]["text"] == "View Pricing"
    assert links[0]["url"] == "https://varistha.ai/pricing"
    assert links[1]["text"] == "GitHub Repo"
    assert links[1]["url"] == "https://github.com/varistha"


def test_convert_html_to_markdown() -> None:
    html = """
    <html>
      <head><title>Test</title><style>.box { color: red; }</style></head>
      <body>
        <nav><a href="/">Home</a></nav>
        <h1>Varistha Control Plane</h1>
        <p>Varistha is an <b>open-source</b> control plane for AI agents.</p>
        <h2>Key Capabilities</h2>
        <ul>
          <li>Plugin system</li>
          <li>Deterministic guardrails</li>
        </ul>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    md = convert_html_to_markdown(html)
    assert "# Varistha Control Plane" in md
    assert "## Key Capabilities" in md
    assert "- Plugin system" in md
    assert "- Deterministic guardrails" in md
    assert "open-source control plane" in md
    assert ".box" not in md  # Style removed
    assert "Copyright" not in md  # Footer removed


@pytest.mark.asyncio
async def test_scrape_url_enforces_ssrf_blocking() -> None:
    for forbidden in [
        "http://127.0.0.1",
        "http://localhost:8000",
        "http://169.254.169.254",
        "http://10.0.0.1",
        "http://192.168.1.1",
    ]:
        with pytest.raises(SSRFSecurityError):
            await scrape_url(forbidden)


@pytest.mark.asyncio
async def test_scrape_url_mocked_http_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_page = """
    <html>
      <head>
        <title>Varistha Intelligence</title>
        <meta name="description" content="AI employee operations platform.">
      </head>
      <body>
        <h1>Architecture Overview</h1>
        <p>Comprehensive guide to running AI employees.</p>
        <a href="/docs/plugins">Plugins Guide</a>
      </body>
    </html>
    """

    class MockResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.text = sample_page
            self.headers = {"content-type": "text/html"}
            self.is_redirect = False

    class MockAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> MockAsyncClient:
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def get(self, url: str, **kwargs: Any) -> MockResponse:
            return MockResponse()

    def _mock_validate(_url: str) -> None:
        pass

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    monkeypatch.setattr("scraper.validate_url_against_ssrf", _mock_validate)

    res = await scrape_url("https://varistha.ai/architecture")
    assert res["status_code"] == 200
    assert res["title"] == "Varistha Intelligence"
    assert res["meta_description"] == "AI employee operations platform."
    assert res["headings"] == ["Architecture Overview"]
    assert "# Architecture Overview" in res["markdown"]
    assert len(res["links"]) == 1
    assert res["links"][0]["url"] == "https://varistha.ai/docs/plugins"
