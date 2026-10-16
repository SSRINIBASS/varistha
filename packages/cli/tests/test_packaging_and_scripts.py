"""Tests for Varistha CLI packaging, versioning, and installer scripts."""

from pathlib import Path

from click.testing import CliRunner
from varistha_cli.main import cli


def get_repo_root() -> Path:
    """Find the repository root relative to this test file."""
    # packages/cli/tests/test_packaging_and_scripts.py -> 4 levels up
    return Path(__file__).resolve().parents[3]


def test_cli_version_flag() -> None:
    """Verify that `varistha --version` displays the correct version string."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
    assert "varistha" in result.output


def test_cli_help_lists_all_subcommands() -> None:
    """Verify that root `varistha --help` lists all documented subcommands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    expected_commands = [
        "init",
        "apply",
        "run",
        "diff",
        "approvals",
        "budget",
        "kill",
        "resume",
        "emergency-stop",
        "policies",
        "eval",
    ]
    for cmd in expected_commands:
        assert cmd in result.output, f"Command '{cmd}' missing from varistha --help"


def test_cli_subcommand_helps() -> None:
    """Verify that subcommands respond to --help with exit code 0."""
    runner = CliRunner()
    subcommands = ["init", "apply", "run", "diff", "budget"]
    for cmd in subcommands:
        result = runner.invoke(cli, [cmd, "--help"])
        assert result.exit_code == 0, f"Command '{cmd} --help' failed with: {result.output}"
        assert "Usage: varistha" in result.output


def test_install_sh_script_integrity() -> None:
    """Verify scripts/install.sh exists, has shebang, and correct logic."""
    root = get_repo_root()
    install_sh = root / "scripts" / "install.sh"
    assert install_sh.exists(), "Missing scripts/install.sh"
    content = install_sh.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in content
    assert "check_prerequisites" in content
    assert "install_varistha" in content
    assert "docker compose" in content


def test_install_ps1_script_integrity() -> None:
    """Verify scripts/install.ps1 exists and has correct PowerShell syntax."""
    root = get_repo_root()
    install_ps1 = root / "scripts" / "install.ps1"
    assert install_ps1.exists(), "Missing scripts/install.ps1"
    content = install_ps1.read_text(encoding="utf-8")
    assert "[CmdletBinding()]" in content
    assert "Check-Prerequisites" in content
    assert "Install-Varistha" in content
    assert "Show-NextSteps" in content
