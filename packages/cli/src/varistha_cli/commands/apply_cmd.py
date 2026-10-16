"""Implementation of `varistha apply` command."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click
import yaml

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.display import console, print_agent_panel, print_error, print_success

try:
    from spec import SpecValidationError, validate_spec_yaml
except ImportError:
    spec_src = Path(__file__).resolve().parents[4] / "spec" / "src"
    if spec_src.exists() and str(spec_src) not in sys.path:
        sys.path.insert(0, str(spec_src))
    from spec import SpecValidationError, validate_spec_yaml


@click.command(name="apply")
@click.option(
    "-f",
    "--file",
    "file_path",
    type=click.Path(dir_okay=False, readable=True),
    required=True,
    help="Path to the Agent Spec YAML file.",
)
@click.pass_context
def apply_command(ctx: click.Context, file_path: str) -> None:
    """Validate and register or update an Agent Spec."""
    target = Path(file_path)
    if not target.exists():
        print_error(f"Spec file not found: {target}")
        sys.exit(1)

    try:
        content = target.read_text(encoding="utf-8")
    except OSError as err:
        print_error(f"Could not read file {target}: {err}")
        sys.exit(1)

    # 1. Local validation via varistha-spec
    try:
        spec_obj = validate_spec_yaml(content)
    except SpecValidationError as err:
        print_error(
            f"Agent spec validation failed for {target.name}",
            details=err.errors or [str(err)],
        )
        sys.exit(1)
    except yaml.YAMLError as err:
        print_error(f"YAML parsing error in {target.name}", details=str(err))
        sys.exit(1)

    # Convert to dictionary for API payload
    raw_spec: dict[str, Any] = yaml.safe_load(content)  # pyright: ignore[reportAssignmentType]
    if isinstance(raw_spec.get("spec"), dict):
        instr = raw_spec["spec"].get("instructions")
        if isinstance(instr, str) and instr.endswith((".md", ".txt")):
            instr_path = target.parent / instr
            if instr_path.exists():
                raw_spec["spec"]["instructions"] = instr_path.read_text(encoding="utf-8")

    agent_name = spec_obj.metadata.name
    version = spec_obj.metadata.version

    # 2. Communicate with API
    api_url: str = (
        ctx.obj.get("api_url", "http://localhost:8000") if ctx.obj else "http://localhost:8000"
    )
    client = VaristhaClient(base_url=api_url)

    try:
        existing_agent = client.get_agent(agent_name)
        if existing_agent is None:
            # Create new agent
            res = client.create_agent(raw_spec)
            print_success(f"Created new agent [bold cyan]{agent_name}[/bold cyan] (v{version})")
            print_agent_panel(res, title="Agent Created")
        else:
            # Agent exists, publish a new version
            res = client.create_agent_version(agent_name, raw_spec)
            print_success(
                f"Registered version [bold]v{version}[/bold] for agent "
                f"[bold cyan]{agent_name}[/bold cyan]"
            )
            print_agent_panel(res, title="Agent Version Updated")

    except VaristhaConnectionError as err:
        print_error("Connection Error", details=str(err))
        sys.exit(1)
    except VaristhaApiError as err:
        details = err.details
        if isinstance(details, dict) and "detail" in details:
            details_str = str(details["detail"])
        else:
            details_str = str(details) if details else str(err)
        print_error("API Rejection", details=details_str)
        sys.exit(1)

    console.print(
        f"\n[dim]Next step:[/dim] Execute a run with "
        f"[bold cyan]varistha run {agent_name}[/bold cyan]\n"
    )
