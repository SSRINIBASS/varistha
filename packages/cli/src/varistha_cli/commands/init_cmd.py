"""Implementation of `varistha init` command."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from varistha_cli.display import console, print_error, print_success
from varistha_cli.templates import generate_starter_spec


@click.command(name="init")
@click.argument("name", default="my-agent", required=False)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Target YAML output path (default: agent.yaml or <name>.yaml).",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing file without prompting.",
)
@click.option(
    "--role",
    type=str,
    default=None,
    help="Role description for the AI agent.",
)
@click.option(
    "--owner",
    type=str,
    default="team@example.com",
    help="Owner email address.",
)
@click.option(
    "--model",
    type=str,
    default="gpt-4o-mini",
    help="Primary LLM model.",
)
def init_command(
    name: str,
    output_path: str | None,
    force: bool,
    role: str | None,
    owner: str,
    model: str,
) -> None:
    """Initialize a new Agent Spec YAML file."""
    # Determine target filename
    if output_path:
        target = Path(output_path)
    elif name != "my-agent":
        target = Path(f"{name}.yaml")
    else:
        target = Path("agent.yaml")

    if target.exists() and not force:
        print_error(
            f"File already exists: {target}",
            details="Use --force / -f to overwrite, or specify a different --output path.",
        )
        sys.exit(1)

    spec_yaml = generate_starter_spec(
        name=name,
        role=role,
        owner=owner,
        primary_model=model,
    )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(spec_yaml, encoding="utf-8")
    except OSError as err:
        print_error(f"Failed to write spec file: {err}")
        sys.exit(1)

    print_success(f"Initialized agent spec at [bold]{target}[/bold]")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  1. Review and customize [cyan]{target}[/cyan]")
    console.print(f"  2. Apply to registry: [bold green]varistha apply -f {target}[/bold green]")
    console.print(f"  3. Run the agent:     [bold cyan]varistha run {name}[/bold cyan]\n")
