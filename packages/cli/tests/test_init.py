"""Tests for `varistha init` command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from varistha_cli.main import cli

from spec import validate_spec_yaml

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner


def test_init_default_creates_agent_yaml(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha init` creates a valid agent.yaml."""
    out = tmp_path / "agent.yaml"
    result = runner.invoke(cli, ["init", "-o", str(out)])
    assert result.exit_code == 0
    assert "Initialized agent spec" in result.output
    assert out.exists()

    content = out.read_text(encoding="utf-8")
    spec = validate_spec_yaml(content)
    assert spec.metadata.name == "my-agent"
    assert spec.metadata.owner == "team@example.com"
    assert spec.metadata.version == "0.1.0"
    assert spec.spec.autonomy == "L1"


def test_init_custom_name_creates_named_yaml(
    runner: CliRunner, tmp_path: Path, monkeypatch: object
) -> None:
    """`varistha init researcher` creates researcher.yaml in current dir."""
    import os

    os.chdir(tmp_path)
    result = runner.invoke(cli, ["init", "researcher"])
    assert result.exit_code == 0
    target = tmp_path / "researcher.yaml"
    assert target.exists()

    content = target.read_text(encoding="utf-8")
    spec = validate_spec_yaml(content)
    assert spec.metadata.name == "researcher"


def test_init_custom_output_flag(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha init -o custom/path/spec.yaml` creates spec at custom path."""
    out = tmp_path / "custom" / "path" / "spec.yaml"
    result = runner.invoke(cli, ["init", "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()

    content = out.read_text(encoding="utf-8")
    spec = validate_spec_yaml(content)
    assert spec.metadata.name == "my-agent"


def test_init_with_options(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha init` with custom --role, --owner, and --model."""
    out = tmp_path / "sales-bot.yaml"
    result = runner.invoke(
        cli,
        [
            "init",
            "sales-bot",
            "-o",
            str(out),
            "--role",
            "Handles incoming demo requests",
            "--owner",
            "sales@example.com",
            "--model",
            "claude-3-5-sonnet",
        ],
    )
    assert result.exit_code == 0
    assert out.exists()

    content = out.read_text(encoding="utf-8")
    spec = validate_spec_yaml(content)
    assert spec.metadata.name == "sales-bot"
    assert spec.metadata.owner == "sales@example.com"
    assert "Handles incoming demo requests" in spec.spec.role
    assert spec.spec.model.primary == "claude-3-5-sonnet"


def test_init_aborts_if_file_exists_without_force(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha init` aborts with error if target file already exists."""
    out = tmp_path / "agent.yaml"
    out.write_text("existing content", encoding="utf-8")
    result = runner.invoke(cli, ["init", "-o", str(out)])
    assert result.exit_code == 1
    assert "File already exists" in result.output
    assert out.read_text(encoding="utf-8") == "existing content"


def test_init_overwrites_with_force(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha init --force` overwrites existing file."""
    out = tmp_path / "agent.yaml"
    out.write_text("existing content", encoding="utf-8")
    result = runner.invoke(cli, ["init", "-o", str(out), "--force"])
    assert result.exit_code == 0
    assert "Initialized agent spec" in result.output
    content = out.read_text(encoding="utf-8")
    assert content != "existing content"
    spec = validate_spec_yaml(content)
    assert spec.metadata.name == "my-agent"
