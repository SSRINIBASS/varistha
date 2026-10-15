"""Tests for web-search plugin."""

from __future__ import annotations

import pytest
from searcher import parse_duckduckgo_html, search_web


@pytest.mark.asyncio
async def test_search_web_empty_query() -> None:
    res = await search_web("")
    assert res["query"] == ""
    assert res["results"] == []
    assert res["total_results"] == 0


@pytest.mark.asyncio
async def test_search_web_mock_engine() -> None:
    res = await search_web("OpenAI pricing", max_results=2, engine="mock")
    assert res["query"] == "OpenAI pricing"
    assert res["engine"] == "mock"
    assert res["total_results"] == 2
    assert len(res["results"]) == 2
    assert "Result 1 for OpenAI pricing" in res["results"][0]["title"]
    assert res["results"][0]["url"] == "https://example.com/item-1"


def test_parse_duckduckgo_html_valid_content() -> None:
    sample_html = """
    <div class="result results_links results_links_deep web-result">
      <div class="result__body">
        <h2 class="result__title">
          <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fvaristha.ai%2Fdocs&amp;rut=1">
            Varistha <b>Agent</b> Control Plane
          </a>
        </h2>
        <a class="result__snippet" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fvaristha.ai%2Fdocs&amp;rut=1">
          Open-source control plane for building, running, and monitoring AI employees.
        </a>
      </div>
    </div>
    <div class="result results_links results_links_deep web-result">
      <div class="result__body">
        <h2 class="result__title">
          <a class="result__a" href="https://example.org/second-item">
            Second Item Title
          </a>
        </h2>
        <a class="result__snippet" href="https://example.org/second-item">
          Snippet text for second search result.
        </a>
      </div>
    </div>
    """
    results = parse_duckduckgo_html(sample_html, max_results=1)
    assert len(results) == 1
    assert results[0]["title"] == "Varistha Agent Control Plane"
    assert results[0]["url"] == "https://varistha.ai/docs"
    assert "Open-source control plane" in results[0]["snippet"]


def test_parse_duckduckgo_html_empty_or_malformed() -> None:
    results = parse_duckduckgo_html("<html><body>No results found</body></html>")
    assert results == []
