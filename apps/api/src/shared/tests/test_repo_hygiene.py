"""Tests for repository hygiene, open-source compliance, and release assets."""

import tomllib
from pathlib import Path

import yaml


def get_repo_root() -> Path:
    """Find the repository root relative to this test file."""
    # This file is apps/api/src/shared/tests/test_repo_hygiene.py -> 5 levels up to repo root
    current = Path(__file__).resolve()
    return current.parents[5]


def test_required_hygiene_documents_exist() -> None:
    """Verify that all open-source repository hygiene files exist."""
    root = get_repo_root()
    required_files = [
        "LICENSE",
        "README.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CHANGELOG.md",
    ]
    for filename in required_files:
        file_path = root / filename
        assert file_path.exists(), f"Missing required document: {filename}"
        assert file_path.stat().st_size > 50, f"File {filename} appears empty or truncated"


def test_license_is_apache_2() -> None:
    """Verify that LICENSE explicitly contains Apache License Version 2.0 text."""
    root = get_repo_root()
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0" in license_text


def test_issue_templates_are_valid_yaml() -> None:
    """Verify that all GitHub issue templates are valid YAML documents."""
    root = get_repo_root()
    template_dir = root / ".github" / "ISSUE_TEMPLATE"
    assert template_dir.exists(), "Missing .github/ISSUE_TEMPLATE directory"

    templates = ["bug_report.yml", "feature_request.yml", "plugin_proposal.yml"]
    for template_name in templates:
        template_file = template_dir / template_name
        assert template_file.exists(), f"Missing template: {template_name}"
        data = yaml.safe_load(template_file.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"Template {template_name} is not a valid YAML mapping"
        assert "name" in data
        assert "description" in data
        assert "body" in data


def test_release_workflow_is_valid_yaml() -> None:
    """Verify that .github/workflows/release.yml is valid YAML and includes necessary jobs."""
    root = get_repo_root()
    release_wf = root / ".github" / "workflows" / "release.yml"
    assert release_wf.exists(), "Missing .github/workflows/release.yml"

    data = yaml.safe_load(release_wf.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "jobs" in data
    jobs = data["jobs"]
    assert "verify" in jobs
    assert "build-docker" in jobs
    assert "build-pypi-packages" in jobs


def test_monorepo_packages_declare_apache_license() -> None:
    """Verify that all sub-packages in the monorepo declare Apache-2.0 license."""
    root = get_repo_root()
    pyproject_files = [
        root / "apps" / "api" / "pyproject.toml",
        root / "apps" / "worker" / "pyproject.toml",
        root / "packages" / "cli" / "pyproject.toml",
        root / "packages" / "spec" / "pyproject.toml",
        root / "packages" / "sdk" / "pyproject.toml",
    ]

    for pyproject in pyproject_files:
        assert pyproject.exists(), f"Missing {pyproject}"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = data.get("project", {})
        license_decl = project.get("license", {})
        if isinstance(license_decl, dict):
            license_text = license_decl.get("text", "")
        else:
            license_text = str(license_decl)
        assert "Apache-2.0" in license_text or "Apache 2.0" in license_text, (
            f"{pyproject} does not specify Apache-2.0 license (found: {license_decl})"
        )
