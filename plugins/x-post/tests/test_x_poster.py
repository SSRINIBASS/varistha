"""Tests for x-post plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from x_poster import (
    XPostValidationError,
    post_to_x,
    validate_post_text,
)


def test_manifest_declares_requires_approval() -> None:
    manifest_path = Path(__file__).resolve().parents[1] / "plugin.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "x-post"
    assert data["requires_approval"] is True


def test_validate_post_text_length_and_empty() -> None:
    # Valid
    assert validate_post_text("Excited to launch Varistha!") == "Excited to launch Varistha!"

    # Empty raises
    with pytest.raises(XPostValidationError):
        validate_post_text("   ")

    # Exceeding 280 chars raises
    long_text = "A" * 281
    with pytest.raises(XPostValidationError):
        validate_post_text(long_text)


@pytest.mark.asyncio
async def test_post_to_x_mock_success() -> None:
    res = await post_to_x(
        text="Varistha Phase 5 is here: Open-source agent ecosystem.",
        reply_to_id="1234567890",
        mock=True,
    )

    assert res["status"] == "simulated_posted"
    assert res["post_id"].startswith("tw_")
    assert "x.com" in res["url"]
    assert res["char_count"] == len("Varistha Phase 5 is here: Open-source agent ecosystem.")
    assert res["reply_to_id"] == "1234567890"
    assert res["mock"] is True
