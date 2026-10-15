"""CLI commands for managing and testing guardrail policies."""

from __future__ import annotations

import json

import click

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.display import (
    console,
    display_policies_table,
    display_policy_test_result,
    print_error,
)


@click.group(name="policies", help="Manage and test guardrail policies and content filters.")
def policies_group() -> None:
    """Guardrail policies command group."""


@policies_group.command(name="list", help="List all registered platform guardrail policies.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def policies_list_command(ctx: click.Context, json_output: bool) -> None:
    """Display registered guardrails."""
    api_url: str = ctx.obj.get("api_url") if ctx.obj else "http://localhost:8000"
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.list_policies()
    except VaristhaConnectionError as err:
        print_error(str(err))
        ctx.exit(1)
        return
    except VaristhaApiError as err:
        print_error(f"Failed to list policies: {err}")
        ctx.exit(1)
        return

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_policies_table(data.get("policies", []), data.get("total", 0))


@policies_group.command(name="test", help="Evaluate a guardrail policy interactively.")
@click.argument("policy_name")
@click.option(
    "--input",
    "-i",
    "payload_text",
    required=True,
    help="Text or payload string to evaluate.",
)
@click.option(
    "--hook",
    "-h",
    default="input",
    type=click.Choice(["input", "output", "tools"], case_sensitive=False),
    show_default=True,
    help="Execution hook point to test.",
)
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def policies_test_command(
    ctx: click.Context,
    policy_name: str,
    payload_text: str,
    hook: str,
    json_output: bool,
) -> None:
    """Test a policy against sample input."""
    api_url: str = ctx.obj.get("api_url") if ctx.obj else "http://localhost:8000"
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.test_policy(policy_name=policy_name, payload=payload_text, hook=hook)
    except VaristhaConnectionError as err:
        print_error(str(err))
        ctx.exit(1)
        return
    except VaristhaApiError as err:
        print_error(f"Failed to test policy '{policy_name}': {err}")
        ctx.exit(1)
        return

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_policy_test_result(data)
