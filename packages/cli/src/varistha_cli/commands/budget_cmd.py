"""CLI commands for budget tracking, kill switches, and emergency stops."""

from __future__ import annotations

import getpass
import json
import sys

import click

from varistha_cli.client import VaristhaApiError, VaristhaClient, VaristhaConnectionError
from varistha_cli.display import (
    console,
    display_agent_budget,
    display_global_kill_switch,
    display_kill_switch_event,
    print_error,
)


def _get_default_operator() -> str:
    """Get current system username as default operator tag."""
    try:
        return getpass.getuser()
    except Exception:
        return "operator"


@click.command(name="budget")
@click.argument("agent")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def budget_command(ctx: click.Context, agent: str, json_output: bool) -> None:
    """Inspect budget usage, daily spend, and circuit-breaker status for an agent."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)

    try:
        data = client.get_agent_budget(agent)
    except VaristhaConnectionError as err:
        print_error(str(err))
        sys.exit(1)
    except VaristhaApiError as err:
        print_error(f"Failed to get budget for agent '{agent}': {err.message}")
        sys.exit(1)

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_agent_budget(data)


@click.command(name="kill")
@click.argument("agent")
@click.option(
    "--reason",
    "-r",
    default="Emergency stop tripped by operator",
    help="Reason for halting agent.",
)
@click.option("--operator", "-o", default=None, help="Operator identity tripping the kill switch.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def kill_command(
    ctx: click.Context,
    agent: str,
    reason: str,
    operator: str | None,
    json_output: bool,
) -> None:
    """Trip an agent kill switch to halt all execution immediately."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)
    effective_op = operator or _get_default_operator()

    try:
        data = client.kill_agent(agent, reason=reason, operator=effective_op)
    except VaristhaConnectionError as err:
        print_error(str(err))
        sys.exit(1)
    except VaristhaApiError as err:
        print_error(f"Failed to trip kill switch for agent '{agent}': {err.message}")
        sys.exit(1)

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_kill_switch_event(data, action="kill")


@click.command(name="resume")
@click.argument("agent")
@click.option("--operator", "-o", default=None, help="Operator identity clearing the kill switch.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def resume_command(
    ctx: click.Context,
    agent: str,
    operator: str | None,
    json_output: bool,
) -> None:
    """Clear an agent kill switch and reactivate execution permissions."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)
    effective_op = operator or _get_default_operator()

    try:
        data = client.resume_agent(agent, operator=effective_op)
    except VaristhaConnectionError as err:
        print_error(str(err))
        sys.exit(1)
    except VaristhaApiError as err:
        print_error(f"Failed to resume agent '{agent}': {err.message}")
        sys.exit(1)

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_kill_switch_event(data, action="resume")


@click.command(name="emergency-stop")
@click.option("--enable", is_flag=True, help="Enable global emergency stop halting all agents.")
@click.option("--disable", is_flag=True, help="Disable global emergency stop, restoring execution.")
@click.option(
    "--reason",
    "-r",
    default="Global emergency stop triggered",
    help="Reason for emergency stop.",
)
@click.option("--operator", "-o", default=None, help="Operator identity toggling global stop.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def emergency_stop_command(
    ctx: click.Context,
    enable: bool,
    disable: bool,
    reason: str,
    operator: str | None,
    json_output: bool,
) -> None:
    """Inspect or toggle the control plane-wide global emergency stop."""
    api_url: str = ctx.obj.get("api_url", "http://localhost:8000")
    client = VaristhaClient(base_url=api_url)
    effective_op = operator or _get_default_operator()

    try:
        if enable:
            data = client.set_global_kill_switch(
                enabled=True,
                reason=reason,
                operator=effective_op,
            )
        elif disable:
            data = client.set_global_kill_switch(
                enabled=False,
                reason=None,
                operator=effective_op,
            )
        else:
            data = client.get_global_kill_switch()
    except VaristhaConnectionError as err:
        print_error(str(err))
        sys.exit(1)
    except VaristhaApiError as err:
        print_error(f"Failed to access emergency stop status: {err.message}")
        sys.exit(1)

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_global_kill_switch(data)
