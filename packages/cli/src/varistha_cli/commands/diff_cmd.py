"""CLI command: varistha diff."""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.display import print_error, print_spec_diff


@click.command(name="diff")
@click.argument("agent_id_or_name", required=False, default=None)
@click.argument("v1", required=False, default=None)
@click.argument("v2", required=False, default=None)
@click.option(
    "-f",
    "--file",
    "spec_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to local agent spec YAML file to diff against published version.",
)
@click.option(
    "--base-version",
    default=None,
    help="Base version to diff against (used with -f, defaults to current active version).",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with non-zero exit code if breaking changes are detected.",
)
@click.pass_context
def diff_command(
    ctx: click.Context,
    agent_id_or_name: str | None,
    v1: str | None,
    v2: str | None,
    spec_file: Path | None,
    base_version: str | None,
    strict: bool,
) -> None:
    """Compare two agent versions or preview local changes against remote spec."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    # Mode 1: Compare local file against remote active version
    if spec_file is not None:
        try:
            content = spec_file.read_text(encoding="utf-8")
            raw_spec = yaml.safe_load(content)
            if not isinstance(raw_spec, dict):
                print_error("Invalid Spec File", f"File '{spec_file}' is not a valid YAML mapping.")
                ctx.exit(1)
        except Exception as exc:
            print_error("Failed to read spec file", str(exc))
            ctx.exit(1)

        name = agent_id_or_name or raw_spec.get("metadata", {}).get("name")
        if not name:
            print_error(
                "Missing Agent Name",
                "Provide an agent name or ensure metadata.name is present in the spec file.",
            )
            ctx.exit(1)

        try:
            diff_data = client.preview_spec_diff(name, raw_spec, base_version=base_version)
        except VaristhaConnectionError as exc:
            print_error("Connection Error", str(exc))
            ctx.exit(1)
        except VaristhaApiError as exc:
            print_error(f"API Error ({exc.status_code})", exc.message)
            ctx.exit(1)

        print_spec_diff(diff_data)
        if strict and diff_data.get("has_breaking_changes", False):
            ctx.exit(1)
        return

    # Mode 2: Compare two published versions of an agent
    if not agent_id_or_name or not v1 or not v2:
        print_error(
            "Invalid Arguments",
            "Usage: varistha diff <agent-name> <v1> <v2>\n   or: varistha diff -f <agent.yaml>",
        )
        ctx.exit(1)

    try:
        diff_data = client.get_version_diff(agent_id_or_name, v1, v2)
    except VaristhaConnectionError as exc:
        print_error("Connection Error", str(exc))
        ctx.exit(1)
    except VaristhaApiError as exc:
        print_error(f"API Error ({exc.status_code})", exc.message)
        ctx.exit(1)

    print_spec_diff(diff_data)
    if strict and diff_data.get("has_breaking_changes", False):
        ctx.exit(1)
