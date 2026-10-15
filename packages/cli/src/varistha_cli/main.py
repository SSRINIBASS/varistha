"""Main entrypoint for Varistha CLI."""

from __future__ import annotations

import os

import click

from varistha_cli import __version__
from varistha_cli.commands.apply_cmd import apply_command
from varistha_cli.commands.init_cmd import init_command
from varistha_cli.commands.run_cmd import run_command


@click.group(name="varistha", invoke_without_command=False)
@click.option(
    "--api-url",
    envvar="VARISTHA_API_URL",
    default=lambda: os.getenv("VARISTHA_API_URL", "http://localhost:8000"),
    help="Varistha Control Plane API URL (default: http://localhost:8000).",
)
@click.version_option(version=__version__, prog_name="varistha")
@click.pass_context
def cli(ctx: click.Context, api_url: str) -> None:
    """Varistha CLI — build, run, monitor, and govern AI agent employees."""
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url.rstrip("/")


cli.add_command(init_command)
cli.add_command(apply_command)
cli.add_command(run_command)

main = cli

if __name__ == "__main__":
    main()
