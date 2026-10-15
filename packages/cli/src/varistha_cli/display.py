"""Rich console formatting and display utilities for Varistha CLI."""

from __future__ import annotations

from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def format_status(status: str) -> str:
    """Format run/agent status with color styling."""
    status_lower = status.lower()
    if status_lower in ("completed", "passed", "active"):
        return f"[bold green]{status.upper()}[/bold green]"
    if status_lower in ("running", "executing"):
        return f"[bold cyan]{status.upper()}[/bold cyan]"
    if status_lower in ("failed", "error", "rejected"):
        return f"[bold red]{status.upper()}[/bold red]"
    if status_lower in ("waiting_approval", "pending", "paused"):
        return f"[bold yellow]{status.upper()}[/bold yellow]"
    return f"[bold]{status.upper()}[/bold]"


def format_cost(cost_usd: float | None) -> str:
    """Format USD cost."""
    if cost_usd is None:
        return "$0.0000"
    return f"${cost_usd:.4f}"


def format_tokens(tokens: int | None) -> str:
    """Format token count with comma separators."""
    if tokens is None:
        return "0"
    return f"{tokens:,}"


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]+[/bold green] {message}")


def print_error(title: str, details: str | list[str] | None = None) -> None:
    """Print error message in a styled red panel."""
    content = f"[bold red]{title}[/bold red]"
    if isinstance(details, list) and details:
        content += "\n\n" + "\n".join(f"  - {item}" for item in details)
    elif isinstance(details, str) and details:
        content += f"\n\n{details}"

    console.print(
        Panel(
            content,
            title="[bold red]Error[/bold red]",
            border_style="red",
            box=ROUNDED,
        )
    )


def print_agent_panel(agent_data: dict[str, Any], title: str = "Agent Registered") -> None:
    """Print agent details in a styled panel."""
    metadata = agent_data.get("metadata", {}) or {}
    spec = agent_data.get("spec", {}) or {}

    agent_id = agent_data.get("id") or metadata.get("id") or "N/A"
    name = agent_data.get("name") or metadata.get("name") or "unknown"
    version = agent_data.get("version") or metadata.get("version") or "0.1.0"
    stage = agent_data.get("stage") or metadata.get("stage") or "dev"
    role = agent_data.get("role") or spec.get("role") or "N/A"
    autonomy = agent_data.get("autonomy") or spec.get("autonomy") or "L1"

    model = spec.get("model", {}) if isinstance(spec, dict) else {}
    primary_model = model.get("primary", "gpt-4o-mini") if isinstance(model, dict) else "N/A"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Agent ID", str(agent_id))
    table.add_row("Name", str(name))
    table.add_row("Version", f"v{version}")
    table.add_row("Stage", f"[cyan]{stage}[/cyan]")
    table.add_row("Autonomy", f"[yellow]{autonomy}[/yellow]")
    table.add_row("Model", str(primary_model))
    table.add_row("Role", str(role)[:80] + ("..." if len(str(role)) > 80 else ""))

    console.print(
        Panel(
            table,
            title=f"[bold green]{title}[/bold green]",
            border_style="green",
            box=ROUNDED,
        )
    )


def print_run_summary(run_data: dict[str, Any]) -> None:
    """Print executed run summary table and output."""
    run_id = run_data.get("id", "N/A")
    agent_id = run_data.get("agent_id", "N/A")
    status = run_data.get("status", "unknown")
    trace_id = run_data.get("trace_id") or "N/A"
    duration_ms = run_data.get("duration_ms")
    total_tokens = run_data.get("total_tokens")
    cost_usd = run_data.get("cost_usd")
    output = run_data.get("output")
    error_msg = run_data.get("error_message")

    duration_str = f"{duration_ms:.1f} ms" if duration_ms is not None else "N/A"

    table = Table(title="Execution Summary", box=ROUNDED)
    table.add_column("Field", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Run ID", str(run_id))
    table.add_row("Agent ID", str(agent_id))
    table.add_row("Status", format_status(str(status)))
    table.add_row("Duration", duration_str)
    table.add_row("Tokens", format_tokens(total_tokens))
    table.add_row("Cost (USD)", format_cost(cost_usd))
    table.add_row("Trace ID", str(trace_id))

    console.print(table)

    if output is not None:
        if isinstance(output, dict) and "response" in output:
            resp_text = str(output["response"])
        elif isinstance(output, str):
            resp_text = output
        else:
            import json

            resp_text = json.dumps(output, indent=2)

        console.print(
            Panel(
                resp_text,
                title="[bold cyan]Run Output[/bold cyan]",
                border_style="cyan",
                box=ROUNDED,
            )
        )

    if error_msg:
        console.print(
            Panel(
                f"[bold red]{error_msg}[/bold red]",
                title="[bold red]Execution Error[/bold red]",
                border_style="red",
                box=ROUNDED,
            )
        )
