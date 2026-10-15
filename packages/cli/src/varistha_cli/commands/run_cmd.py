"""Implementation of `varistha run` command."""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import click

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaClientError,
    VaristhaConnectionError,
)
from varistha_cli.display import console, print_error, print_run_summary, print_success


@click.command(name="run")
@click.argument("agent_id_or_name", required=True)
@click.option(
    "-i",
    "--input",
    "input_text",
    type=str,
    default="Execute default task",
    help="Input task query or JSON string.",
)
@click.option(
    "-w/-nw",
    "--watch/--no-watch",
    default=True,
    help="Wait and poll for run completion (default: --watch).",
)
@click.option(
    "--timeout",
    type=int,
    default=60,
    help="Timeout in seconds when waiting for run to complete.",
)
@click.option(
    "--interval",
    type=float,
    default=0.5,
    help="Polling interval in seconds.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output response as raw JSON.",
)
@click.pass_context
def run_command(
    ctx: click.Context,
    agent_id_or_name: str,
    input_text: str,
    watch: bool,
    timeout: int,
    interval: float,
    as_json: bool,
) -> None:
    """Trigger an execution run for an agent."""
    api_url: str = (
        ctx.obj.get("api_url", "http://localhost:8000") if ctx.obj else "http://localhost:8000"
    )
    client = VaristhaClient(base_url=api_url)

    # Parse input text as JSON if structured, else wrap as {"query": input_text}
    input_payload: dict[str, Any]
    if input_text.strip().startswith("{") and input_text.strip().endswith("}"):
        try:
            input_payload = json.loads(input_text)
        except json.JSONDecodeError:
            input_payload = {"query": input_text}
    else:
        input_payload = {"query": input_text}

    # 1. Trigger the run
    try:
        run_data = client.trigger_run(
            id_or_name=agent_id_or_name,
            input_data=input_payload,
            trigger_type="manual",
        )
    except VaristhaConnectionError as err:
        if as_json:
            click.echo(json.dumps({"error": str(err)}))
        else:
            print_error("Connection Error", details=str(err))
        sys.exit(1)
    except VaristhaApiError as err:
        if as_json:
            click.echo(json.dumps({"error": str(err), "details": err.details}))
        else:
            print_error("API Error", details=str(err.details or err))
        sys.exit(1)

    run_id: str = run_data.get("id", "")
    initial_status: str = run_data.get("status", "running")

    if not watch:
        if as_json:
            click.echo(json.dumps(run_data, indent=2))
        else:
            print_success(f"Run triggered: [bold]{run_id}[/bold] (status: {initial_status})")
            console.print(
                f"[dim]Check status later with:[/dim] varistha run {agent_id_or_name} --watch"
            )
        return

    # 2. Watch mode: poll run status until completion
    terminal_statuses = {"completed", "failed", "waiting_approval"}
    start_time = time.time()
    current_run = run_data

    if not as_json and current_run.get("status") not in terminal_statuses:
        with console.status(
            f"[bold cyan]Running agent {agent_id_or_name}...[/bold cyan]", spinner="dots"
        ):
            while current_run.get("status") not in terminal_statuses:
                if time.time() - start_time > timeout:
                    print_error(f"Run {run_id} timed out after {timeout} seconds")
                    sys.exit(1)
                time.sleep(interval)
                try:
                    current_run = client.get_run(run_id)
                except VaristhaClientError as err:
                    print_error("Polling Error", details=str(err))
                    sys.exit(1)
    elif current_run.get("status") not in terminal_statuses:
        while current_run.get("status") not in terminal_statuses:
            if time.time() - start_time > timeout:
                click.echo(
                    json.dumps({"error": f"Run timed out after {timeout}s", "run": current_run})
                )
                sys.exit(1)
            time.sleep(interval)
            try:
                current_run = client.get_run(run_id)
            except VaristhaClientError as err:
                click.echo(json.dumps({"error": str(err)}))
                sys.exit(1)

    # 3. Final render
    if as_json:
        click.echo(json.dumps(current_run, indent=2))
    else:
        status = current_run.get("status")
        if status == "completed":
            print_success(f"Run [bold]{run_id}[/bold] completed successfully!")
        elif status == "waiting_approval":
            console.print(
                f"[bold yellow]! Run [bold]{run_id}[/bold] is waiting for "
                "human approval.[/bold yellow]"
            )
        elif status == "failed":
            console.print(f"[bold red]x Run [bold]{run_id}[/bold] failed.[/bold red]")

        print_run_summary(current_run)

    if current_run.get("status") == "failed":
        sys.exit(1)
