"""Tests for documentation integrity, guide presence, and valid relative links."""

import re
from pathlib import Path


def get_repo_root() -> Path:
    """Find the repository root relative to this test file."""
    return Path(__file__).resolve().parents[5]


def test_core_guides_exist_and_structured() -> None:
    """Verify that all Phase 7 user and operator guides exist and have content."""
    root = get_repo_root()
    guides_dir = root / "docs" / "guides"
    assert guides_dir.exists(), "Missing docs/guides directory"

    expected_guides = [
        "quickstart.md",
        "concepts.md",
        "role-packs.md",
        "plugin-authoring.md",
        "production-hardening.md",
        "api-reference.md",
        "agent-spec-guide.md",
    ]

    for guide_name in expected_guides:
        guide_file = guides_dir / guide_name
        assert guide_file.exists(), f"Guide missing: {guide_name}"
        content = guide_file.read_text(encoding="utf-8")
        assert len(content) > 300, f"Guide {guide_name} appears too brief or empty"
        assert content.startswith("# "), f"Guide {guide_name} must begin with an H1 heading"


def test_guide_relative_markdown_links_resolve() -> None:
    """Verify that relative markdown links between docs resolve to existing files."""
    root = get_repo_root()
    guides_dir = root / "docs" / "guides"

    link_pattern = re.compile(r"\[.*?\]\((?P<link>[^:]+?\.md)\)")

    for guide_file in guides_dir.glob("*.md"):
        content = guide_file.read_text(encoding="utf-8")
        for match in link_pattern.finditer(content):
            target = match.group("link")
            # Skip anchor links
            if target.startswith("#"):
                continue
            resolved = (guide_file.parent / target).resolve()
            assert resolved.exists(), (
                f"Broken link '{target}' in {guide_file.name} (resolved to {resolved})"
            )
