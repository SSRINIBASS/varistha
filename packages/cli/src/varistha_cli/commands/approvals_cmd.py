"""CLI commands for managing and resolving governance approval requests."""

from __future__ import annotations

import getpass
import json
from pathlib import Path
from typing import Any

import click

from varistha_cli.client import VaristhaApiError, VaristhaClient, VaristhaConnectionError
from varistha_cli.display import (
    console,
    display_approval_detail,
    display_approvals_table,
    print_error,
    print_success,
)


def _get_default_reviewer() -> str:
    """Get current system username as default reviewer tag."""
    try:
        return getpass.getuser()
    except Exception:
        return "operator"


@click.group(name="approvals")
def approvals_group() -> None:
    """Manage human-in-the-loop approval workflows."""


@approvals_group.command(name="list")
@click.option(
    "--status",
    "status_filter",
    type=click.Choice(["pending", "approved", "rejected", "edited"], case_sensitive=False),
    help="Filter by status.",
)
@click.option("--agent-id", help="Filter by agent UUID.")
@click.option("--run-id", help="Filter by run UUID.")
@click.option("--limit", default=50, show_default=True, type=int, help="Limit number of results.")
@click.option("--offset", default=0, show_default=True, type=int, help="Offset for pagination.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def list_approvals_cmd(
    ctx: click.Context,
    status_filter: str | None,
    agent_id: str | None,
    run_id: str | None,
    limit: int,
    offset: int,
    json_output: bool,
) -> None:
    """List approval requests awaiting or resolved by operators."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.list_approvals(
            agent_id=agent_id,
            run_id=run_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        if json_output:
            click.echo(json.dumps(data, indent=2))
            return

        display_approvals_table(data.get("items", []), data.get("total", 0))

    except VaristhaConnectionError as err:
        print_error("Connection Error", str(err))
        ctx.exit(1)
    except VaristhaApiError as err:
        print_error(f"API Error ({err.status_code})", err.message)
        ctx.exit(1)


@approvals_group.command(name="get")
@click.argument("approval_id")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def get_approval_cmd(ctx: click.Context, approval_id: str, json_output: bool) -> None:
    """Show details and payload of a single approval request."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.get_approval(approval_id)
        if json_output:
            click.echo(json.dumps(data, indent=2))
            return

        display_approval_detail(data)

    except VaristhaConnectionError as err:
        print_error("Connection Error", str(err))
        ctx.exit(1)
    except VaristhaApiError as err:
        print_error(f"API Error ({err.status_code})", err.message)
        ctx.exit(1)


@approvals_group.command(name="approve")
@click.argument("approval_id")
@click.option(
    "--reviewer", default=_get_default_reviewer, help="Operator identifier resolving approval."
)
@click.option("--feedback", help="Optional review feedback/notes.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def approve_cmd(
    ctx: click.Context,
    approval_id: str,
    reviewer: str,
    feedback: str | None,
    json_output: bool,
) -> None:
    """Approve a pending action without modifications."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.resolve_approval(
            approval_id=approval_id,
            decision="approve",
            reviewer=reviewer,
            feedback=feedback,
        )
        if json_output:
            click.echo(json.dumps(data, indent=2))
            return

        print_success(f"Approval '{approval_id}' marked APPROVED by '{reviewer}'.")
        display_approval_detail(data)

    except VaristhaConnectionError as err:
        print_error("Connection Error", str(err))
        ctx.exit(1)
    except VaristhaApiError as err:
        print_error(f"API Error ({err.status_code})", err.message)
        ctx.exit(1)


@approvals_group.command(name="reject")
@click.argument("approval_id")
@click.option(
    "--reviewer", default=_get_default_reviewer, help="Operator identifier resolving approval."
)
@click.option("--feedback", help="Optional reason for rejection.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def reject_cmd(
    ctx: click.Context,
    approval_id: str,
    reviewer: str,
    feedback: str | None,
    json_output: bool,
) -> None:
    """Reject a pending action, stopping run execution."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.resolve_approval(
            approval_id=approval_id,
            decision="reject",
            reviewer=reviewer,
            feedback=feedback,
        )
        if json_output:
            click.echo(json.dumps(data, indent=2))
            return

        console.print(f"[bold red]x[/bold red] Approval '{approval_id}' REJECTED by '{reviewer}'.")
        display_approval_detail(data)

    except VaristhaConnectionError as err:
        print_error("Connection Error", str(err))
        ctx.exit(1)
    except VaristhaApiError as err:
        print_error(f"API Error ({err.status_code})", err.message)
        ctx.exit(1)


@approvals_group.command(name="edit")
@click.argument("approval_id")
@click.option(
    "--payload", required=True, help="Edited payload as JSON string or path to JSON file."
)
@click.option(
    "--reviewer", default=_get_default_reviewer, help="Operator identifier resolving approval."
)
@click.option("--feedback", help="Feedback explaining edits.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def edit_cmd(
    ctx: click.Context,
    approval_id: str,
    payload: str,
    reviewer: str,
    feedback: str | None,
    json_output: bool,
) -> None:
    """Edit proposed action payload and approve the modified version."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    parsed_payload: dict[str, Any]
    try:
        path = Path(payload)
        if path.is_file():
            parsed_payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            parsed_payload = json.loads(payload)
    except Exception as err:
        print_error("Invalid Payload", f"Could not parse payload as JSON or read file: {err}")
        ctx.exit(1)

    try:
        data = client.resolve_approval(
            approval_id=approval_id,
            decision="edit",
            reviewer=reviewer,
            approved_payload=parsed_payload,
            feedback=feedback,
        )
        if json_output:
            click.echo(json.dumps(data, indent=2))
            return

        print_success(f"Approval '{approval_id}' EDITED & APPROVED by '{reviewer}'.")
        display_approval_detail(data)

    except VaristhaConnectionError as err:
        print_error("Connection Error", str(err))
        ctx.exit(1)
    except VaristhaApiError as err:
        print_error(f"API Error ({err.status_code})", err.message)
        ctx.exit(1)
