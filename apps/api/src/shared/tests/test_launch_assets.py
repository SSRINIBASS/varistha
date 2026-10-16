"""Tests validating launch playbook, community assets, and project roadmap."""

from pathlib import Path


def get_repo_root() -> Path:
    """Find the repository root relative to this test file."""
    return Path(__file__).resolve().parents[5]


def test_launch_playbook_integrity() -> None:
    """Verify that docs/launch/launch-playbook.md contains all required channel launch assets."""
    root = get_repo_root()
    playbook_file = root / "docs" / "launch" / "launch-playbook.md"
    assert playbook_file.exists(), "Missing docs/launch/launch-playbook.md"

    content = playbook_file.read_text(encoding="utf-8")
    assert content.startswith("# "), "Playbook must start with an H1 heading"
    assert "Show HN" in content, "Missing Show HN launch copy"
    assert "r/selfhosted" in content, "Missing r/selfhosted copy"
    assert "r/LocalLLaMA" in content, "Missing r/LocalLLaMA copy"
    assert "Product Hunt" in content, "Missing Product Hunt kit"
    assert "docker compose" in content, "Missing quickstart instructions in launch copy"


def test_public_roadmap_integrity() -> None:
    """Verify that docs/ROADMAP.md outlines upcoming version milestones."""
    root = get_repo_root()
    roadmap_file = root / "docs" / "ROADMAP.md"
    assert roadmap_file.exists(), "Missing docs/ROADMAP.md"

    content = roadmap_file.read_text(encoding="utf-8")
    assert content.startswith("# "), "Roadmap must start with an H1 heading"
    assert "v0.1.0" in content, "Missing v0.1.0 current release section"
    assert "v0.2.0" in content, "Missing v0.2.0 milestone"
    assert "v0.3.0" in content, "Missing v0.3.0 milestone"
    assert "v1.0.0" in content, "Missing v1.0.0 milestone"
    assert "Hatchet" in content or "Temporal" in content, "Missing distributed runtime roadmap"
