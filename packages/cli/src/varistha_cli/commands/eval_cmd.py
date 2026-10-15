"""CLI commands for running and viewing offline evaluation suites."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import click
import yaml

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.display import (
    console,
    display_eval_run_result,
    display_eval_suites_table,
    print_error,
)


@click.group(name="eval", help="Manage and execute agent evaluation suites.")
def eval_group() -> None:
    """Manage and execute evaluation suites."""


@eval_group.command(name="list", help="List available evaluation suites.")
@click.option(
    "--agent",
    "-a",
    "agent_filter",
    default=None,
    help="Filter suites by Agent UUID or name.",
)
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def eval_list_command(ctx: click.Context, agent_filter: str | None, json_output: bool) -> None:
    """List evaluation suites."""
    api_url: str = ctx.obj.get("api_url") if ctx.obj else "http://localhost:8000"
    client = VaristhaClient(base_url=api_url)

    target_agent_id: str | None = None
    if agent_filter:
        try:
            # Check if UUID
            uuid.UUID(agent_filter)
            target_agent_id = agent_filter
        except ValueError:
            # Look up agent by name
            try:
                agent_obj = client.get_agent(agent_filter)
                if agent_obj:
                    target_agent_id = str(agent_obj.get("id"))
                else:
                    print_error(f"Agent '{agent_filter}' not found.")
                    ctx.exit(1)
                    return
            except Exception as err:
                print_error(f"Failed to lookup agent '{agent_filter}': {err}")
                ctx.exit(1)
                return

    try:
        data = client.list_eval_suites(agent_id=target_agent_id)
    except VaristhaConnectionError as err:
        print_error(str(err))
        ctx.exit(1)
        return
    except VaristhaApiError as err:
        print_error(f"Failed to list eval suites: {err}")
        ctx.exit(1)
        return

    if json_output:
        console.print_json(json.dumps(data))
    else:
        display_eval_suites_table(data.get("suites", []), data.get("total", 0))


@eval_group.command(name="run", help="Execute an evaluation suite against an agent version.")
@click.argument("suite_id_or_file")
@click.option("--version", "-v", "version_id", default=None, help="Target Agent Version UUID.")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON.")
@click.pass_context
def eval_run_command(
    ctx: click.Context,
    suite_id_or_file: str,
    version_id: str | None,
    json_output: bool,
) -> None:
    """Execute evaluation suite test cases and evaluate assertions."""
    api_url: str = ctx.obj.get("api_url") if ctx.obj else "http://localhost:8000"
    client = VaristhaClient(base_url=api_url)

    target_path = Path(suite_id_or_file)
    target_suite_id: str | None = None

    if target_path.is_file():
        # Load from file
        try:
            file_content = target_path.read_text(encoding="utf-8")
            doc: dict[str, Any] = yaml.safe_load(file_content) or {}
        except Exception as err:
            print_error(f"Failed to read evaluation file '{suite_id_or_file}': {err}")
            ctx.exit(1)
            return

        meta = doc.get("metadata", {})
        spec = doc.get("spec", {})
        suite_name = meta.get("name") or target_path.stem
        agent_ref = meta.get("agent")

        if not agent_ref:
            print_error(f"Eval file '{suite_id_or_file}' missing required 'metadata.agent' field.")
            ctx.exit(1)
            return

        try:
            agent = client.get_agent(agent_ref)
            if not agent:
                print_error(f"Agent '{agent_ref}' referenced in eval suite does not exist.")
                ctx.exit(1)
                return
            agent_id = str(agent.get("id"))
        except Exception as err:
            print_error(f"Could not resolve agent '{agent_ref}': {err}")
            ctx.exit(1)
            return

        # Check if suite already registered
        try:
            suites_data = client.list_eval_suites(agent_id=agent_id)
            existing_suites = suites_data.get("suites", [])
            match = next((s for s in existing_suites if s.get("name") == suite_name), None)
            if match:
                target_suite_id = str(match["id"])
            else:
                # Register new suite
                raw_evaluators = [
                    ev.model_dump() if hasattr(ev, "model_dump") else ev
                    for ev in spec.get("evaluators", [])
                ]
                raw_cases = [
                    c.model_dump() if hasattr(c, "model_dump") else c for c in spec.get("cases", [])
                ]
                config = {
                    "evaluators": raw_evaluators,
                    "cases": raw_cases,
                }
                new_suite = client.create_eval_suite(
                    agent_id=agent_id,
                    name=suite_name,
                    description=spec.get("description"),
                    config=config,
                )
                target_suite_id = str(new_suite["id"])
        except Exception as err:
            print_error(f"Failed to register or resolve eval suite: {err}")
            ctx.exit(1)
            return
    else:
        # Check if UUID or name
        try:
            uuid.UUID(suite_id_or_file)
            target_suite_id = suite_id_or_file
        except ValueError:
            # Search by name
            try:
                all_suites = client.list_eval_suites().get("suites", [])
                match = next((s for s in all_suites if s.get("name") == suite_id_or_file), None)
                if match:
                    target_suite_id = str(match["id"])
                else:
                    print_error(f"Evaluation suite '{suite_id_or_file}' not found.")
                    ctx.exit(1)
                    return
            except Exception as err:
                print_error(f"Failed to find eval suite '{suite_id_or_file}': {err}")
                ctx.exit(1)
                return

    try:
        run_data = client.execute_eval_suite(
            suite_id=target_suite_id,
            agent_version_id=version_id,
            trigger="cli",
        )
    except VaristhaConnectionError as err:
        print_error(str(err))
        ctx.exit(1)
        return
    except VaristhaApiError as err:
        print_error(f"Evaluation execution failed: {err}")
        ctx.exit(1)
        return

    if json_output:
        console.print_json(json.dumps(run_data))
    else:
        display_eval_run_result(run_data)

    pass_rate = run_data.get("pass_rate")
    if pass_rate is not None and pass_rate < 0.8:
        ctx.exit(1)
