"""Tests for linkedin-post plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from linkedin_poster import (
    LinkedInPostValidationError,
    post_to_linkedin,
    validate_linkedin_post,
)


def test_manifest_declares_requires_approval() -> None:
    manifest_path = Path(__file__).resolve().parents[1] / "plugin.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "linkedin-post"
    assert data["requires_approval"] is True


def test_validate_linkedin_post_text_and_visibility() -> None:
    text, vis = validate_linkedin_post("We're thrilled to introduce Varistha!", "public")
    assert text == "We're thrilled to introduce Varistha!"
    assert vis == "PUBLIC"

    # Empty raises
    with pytest.raises(LinkedInPostValidationError):
        validate_linkedin_post("   ", "PUBLIC")

    # Exceeding 3000 chars raises
    with pytest.raises(LinkedInPostValidationError):
        validate_linkedin_post("A" * 3001, "PUBLIC")

    # Invalid visibility raises
    with pytest.raises(LinkedInPostValidationError):
        validate_linkedin_post("Hello world", "INVALID_SCOPE")


@pytest.mark.asyncio
async def test_post_to_linkedin_mock_success() -> None:
    res = await post_to_linkedin(
        text="Varistha allows self-hosted AI employee governance.",
        title="Open-source AI control plane",
        article_url="https://varistha.ai/blog/launch",
        visibility="PUBLIC",
        mock=True,
    )

    assert res["status"] == "simulated_posted"
    assert res["share_urn"].startswith("urn:li:share:")
    assert "linkedin.com/feed/update" in res["url"]
    assert res["visibility"] == "PUBLIC"
    assert res["article_url"] == "https://varistha.ai/blog/launch"
    assert res["mock"] is True
