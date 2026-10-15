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
    if status_lower in ("completed", "passed", "active", "approved"):
        return f"[bold green]{status.upper()}[/bold green]"
    if status_lower in ("running", "executing", "edited"):
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


def print_spec_diff(diff_data: dict[str, Any]) -> None:
    """Print structured spec diff with breaking change highlights."""
    from_ver = diff_data.get("from_version") or "base"
    to_ver = diff_data.get("to_version") or "target"
    has_changes = diff_data.get("has_changes", False)
    has_breaking = diff_data.get("has_breaking_changes", False)
    summary = diff_data.get("summary", {})
    entries = diff_data.get("entries", [])

    if not has_changes:
        msg = f"[bold green]No differences detected between v{from_ver} and v{to_ver}.[/bold green]"
        console.print(
            Panel(
                msg,
                title="[bold green]Spec Diff[/bold green]",
                border_style="green",
                box=ROUNDED,
            )
        )
        return

    # Header summary
    total = summary.get("total", len(entries))
    added = summary.get("added", 0)
    removed = summary.get("removed", 0)
    modified = summary.get("modified", 0)
    breaking = summary.get("breaking", 0)

    summary_line = (
        f"Total Changes: [bold]{total}[/bold] | "
        f"[green]+{added} added[/green] | "
        f"[red]-{removed} removed[/red] | "
        f"[yellow]~{modified} modified[/yellow] | "
        f"[bold red]!{breaking} breaking[/bold red]"
    )

    console.print(
        Panel(
            summary_line,
            title=f"[bold cyan]Spec Diff: v{from_ver} -> v{to_ver}[/bold cyan]",
            border_style="red" if has_breaking else "cyan",
            box=ROUNDED,
        )
    )

    if has_breaking:
        breaking_items: list[str] = []
        for e in diff_data.get("breaking_entries", []):
            reason = e.get("breaking_reason") or e.get("description")
            breaking_items.append(f"  - [bold red]{e['field']}[/bold red]: {reason}")
        breaking_details = "\n".join(breaking_items)
        alert_body = (
            f"[bold red]WARNING: This diff introduces {breaking} BREAKING change(s)![/bold red]\n\n"
            f"{breaking_details}"
        )
        console.print(
            Panel(
                alert_body,
                title="[bold red]Breaking Changes Alert[/bold red]",
                border_style="red",
                box=ROUNDED,
            )
        )

    # Table of all changes
    table = Table(box=ROUNDED, show_header=True, header_style="bold")
    table.add_column("Field", style="cyan")
    table.add_column("Type", justify="center")
    table.add_column("Old Value", style="dim")
    table.add_column("New Value")
    table.add_column("Impact", justify="center")

    for e in entries:
        ctype = e.get("change_type", "modified").lower()
        if ctype == "added":
            type_badge = "[bold green]+ ADDED[/bold green]"
        elif ctype == "removed":
            type_badge = "[bold red]- REMOVED[/bold red]"
        else:
            type_badge = "[bold yellow]~ MODIFIED[/bold yellow]"

        is_brk = e.get("is_breaking", False)
        impact_badge = "[bold red]BREAKING[/bold red]" if is_brk else "[green]Safe[/green]"

        old_val = str(e.get("old_value")) if e.get("old_value") is not None else "-"
        new_val = str(e.get("new_value")) if e.get("new_value") is not None else "-"

        if len(old_val) > 40:
            old_val = old_val[:37] + "..."
        if len(new_val) > 40:
            new_val = new_val[:37] + "..."

        table.add_row(e.get("field", ""), type_badge, old_val, new_val, impact_badge)

    console.print(table)


def display_approvals_table(items: list[dict[str, Any]], total: int) -> None:
    """Render a styled table of approval requests."""
    if not items:
        console.print("[dim]No approval requests found matching criteria.[/dim]")
        return

    table = Table(
        title=f"Governance Approvals ({len(items)} of {total})",
        box=ROUNDED,
        header_style="bold",
    )
    table.add_column("Approval ID", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Action Type")
    table.add_column("Tool / Action")
    table.add_column("Reviewer", style="dim")
    table.add_column("Created At", style="dim")

    for item in items:
        appr_id = str(item.get("id", ""))
        short_id = appr_id[:8] + "..." if len(appr_id) > 12 else appr_id
        status_styled = format_status(item.get("status", "pending"))
        action_type = item.get("action_type", "-")
        tool_name = item.get("tool_name") or "-"
        reviewer = item.get("reviewer") or "-"
        created_at = str(item.get("created_at", ""))[:19]

        table.add_row(short_id, status_styled, action_type, tool_name, reviewer, created_at)

    console.print(table)


def display_approval_detail(approval: dict[str, Any]) -> None:
    """Render comprehensive detail view of a single approval request."""
    import json

    appr_id = approval.get("id", "")
    status_styled = format_status(approval.get("status", "pending"))
    action_type = approval.get("action_type", "-")
    tool_name = approval.get("tool_name") or "-"
    reviewer = approval.get("reviewer") or "-"
    feedback = approval.get("feedback") or "-"
    created_at = str(approval.get("created_at", ""))[:19]
    resolved_at = str(approval.get("resolved_at", ""))[:19] if approval.get("resolved_at") else "-"

    overview_lines = [
        f"[bold]Approval ID:[/bold] {appr_id}",
        f"[bold]Run ID:[/bold] {approval.get('run_id', '-')}",
        f"[bold]Agent ID:[/bold] {approval.get('agent_id', '-')}",
        f"[bold]Status:[/bold] {status_styled}",
        f"[bold]Action Type:[/bold] {action_type}",
        f"[bold]Tool Name:[/bold] {tool_name}",
        f"[bold]Created At:[/bold] {created_at}",
        f"[bold]Resolved At:[/bold] {resolved_at}",
        f"[bold]Reviewer:[/bold] {reviewer}",
        f"[bold]Feedback:[/bold] {feedback}",
    ]
    if approval.get("description"):
        overview_lines.append(f"[bold]Description:[/bold] {approval.get('description')}")

    console.print(
        Panel(
            "\n".join(overview_lines),
            title=f"[bold]Approval Detail — {appr_id[:8]}[/bold]",
            box=ROUNDED,
            border_style="cyan",
        )
    )

    # Proposed Payload
    proposed_str = json.dumps(approval.get("proposed_payload", {}), indent=2)
    console.print(
        Panel(
            proposed_str,
            title="[bold yellow]Proposed Payload (Agent Requested)[/bold yellow]",
            box=ROUNDED,
            border_style="yellow",
        )
    )

    # Approved Payload (if resolved)
    if approval.get("approved_payload") is not None:
        approved_str = json.dumps(approval.get("approved_payload", {}), indent=2)
        console.print(
            Panel(
                approved_str,
                title="[bold green]Approved Payload (Human Approved)[/bold green]",
                box=ROUNDED,
                border_style="green",
            )
        )

    # Diff (if edited)
    if approval.get("diff") is not None:
        diff_str = json.dumps(approval.get("diff", {}), indent=2)
        console.print(
            Panel(
                diff_str,
                title="[bold cyan]Payload Diff (Proposed vs Final Approved)[/bold cyan]",
                box=ROUNDED,
                border_style="cyan",
            )
        )


def display_agent_budget(b: dict[str, Any]) -> None:
    """Render financial spend, ceilings, and circuit-breaker flags for an agent."""
    agent_name = b.get("agent_name", "Unknown")
    is_active = b.get("is_active", True)
    kill_tripped = b.get("kill_switch_tripped", False)

    if kill_tripped:
        status_styled = "[bold red]HALTED (Kill Switch Tripped)[/bold red]"
    elif not is_active:
        status_styled = "[bold yellow]INACTIVE[/bold yellow]"
    else:
        status_styled = "[bold green]ACTIVE[/bold green]"

    daily_spend = b.get("daily_spend_usd", 0.0)
    runs_count = b.get("daily_runs_count", 0)
    max_run = b.get("max_usd_per_run")
    max_day = b.get("max_usd_per_day")
    remaining = b.get("daily_budget_remaining_usd")
    pct = b.get("daily_budget_utilization_pct")

    lines = [
        f"[bold]Agent Name:[/bold] {agent_name}",
        f"[bold]Operational Status:[/bold] {status_styled}",
    ]

    if kill_tripped:
        lines.append(f"[bold red]Trip Reason:[/bold red] {b.get('kill_switch_reason', '-')}")
        tripped_at = str(b.get("kill_switch_tripped_at", ""))[:19]
        lines.append(f"[bold red]Tripped At:[/bold red] {tripped_at}")

    lines.append(f"[bold]Today's Spend:[/bold] [yellow]${daily_spend:.4f}[/yellow]")
    lines.append(f"[bold]Runs Executed Today:[/bold] {runs_count}")

    if max_run is not None:
        lines.append(f"[bold]Max Budget Per Run:[/bold] [cyan]${max_run:.2f}[/cyan]")
    else:
        lines.append("[bold]Max Budget Per Run:[/bold] [dim]Unbounded[/dim]")

    if max_day is not None:
        lines.append(f"[bold]Max Budget Per Day:[/bold] [cyan]${max_day:.2f}[/cyan]")
        lines.append(f"[bold]Remaining Today:[/bold] [green]${remaining:.4f}[/green]")
        pct_color = "green" if (pct or 0) < 80 else ("yellow" if (pct or 0) < 100 else "red")
        pct_str = f"[{pct_color}]{pct:.1f}%[/{pct_color}]"
        lines.append(f"[bold]Daily Budget Utilization:[/bold] {pct_str}")
    else:
        lines.append("[bold]Max Budget Per Day:[/bold] [dim]Unbounded[/dim]")

    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold]Financial Budget & Circuit Breaker — {agent_name}[/bold]",
            box=ROUNDED,
            border_style="red" if kill_tripped else "cyan",
        )
    )


def display_kill_switch_event(event: dict[str, Any], action: str) -> None:
    """Render confirmation panel for tripping or resuming an agent kill switch."""
    agent_name = event.get("agent_name", "Unknown")
    if action == "kill":
        console.print(
            Panel(
                f"[bold red]EMERGENCY STOP ACTIVATED[/bold red]\n"
                f"Agent [bold]{agent_name}[/bold] has been halted.\n"
                f"Reason: {event.get('reason', '-')}\n"
                f"Operator: {event.get('operator', '-')}",
                title="[bold red]Circuit Breaker Tripped[/bold red]",
                box=ROUNDED,
                border_style="red",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold green]AGENT RESUMED[/bold green]\n"
                f"Agent [bold]{agent_name}[/bold] kill switch cleared.\n"
                f"Execution re-enabled by operator: {event.get('operator', '-')}",
                title="[bold green]Normal Operation Restored[/bold green]",
                box=ROUNDED,
                border_style="green",
            )
        )


def display_global_kill_switch(status_data: dict[str, Any]) -> None:
    """Render platform-wide emergency stop status."""
    enabled = status_data.get("enabled", False)
    if enabled:
        console.print(
            Panel(
                f"[bold red]PLATFORM EMERGENCY STOP ACTIVE[/bold red]\n"
                f"All agent executions across the entire control plane are halted.\n"
                f"Reason: {status_data.get('reason', '-')}\n"
                f"Tripped At: {status_data.get('tripped_at', '-')}\n"
                f"Operator: {status_data.get('operator', '-')}",
                title="[bold red]Global Kill Switch[/bold red]",
                box=ROUNDED,
                border_style="red",
            )
        )
    else:
        console.print(
            Panel(
                "[bold green]GLOBAL EMERGENCY STOP INACTIVE[/bold green]\n"
                "Control plane agent execution engine is operating normally.",
                title="[bold green]Global Kill Switch[/bold green]",
                box=ROUNDED,
                border_style="green",
            )
        )


def display_policies_table(items: list[dict[str, Any]], total: int) -> None:
    """Render a styled table of registered guardrail policies."""
    if not items:
        console.print("[yellow]No guardrail policies registered.[/yellow]")
        return

    table = Table(
        title=f"Guardrail Policies ({total} available)",
        box=ROUNDED,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Policy Name", style="bold cyan")
    table.add_column("Hooks", justify="center")
    table.add_column("Description")

    for p in items:
        hooks = ", ".join(f"[magenta]{h}[/magenta]" for h in p.get("supported_hooks", []))
        table.add_row(p.get("name", "-"), hooks, p.get("description", "-"))

    console.print(table)


def display_policy_test_result(result: dict[str, Any]) -> None:
    """Render the outcome of testing a guardrail policy."""
    passed = result.get("passed", False)
    action = result.get("action", "allow")
    policy_name = result.get("policy_name", "-")

    if not passed or action == "block":
        violations = result.get("violations", [])
        viol_text = "\n".join(f"  - [red]{v}[/red]" for v in violations)
        console.print(
            Panel(
                f"[bold red]POLICY BLOCKED: {policy_name}[/bold red]\n"
                f"Action: [bold red]{action.upper()}[/bold red]\n\n"
                f"Violations Detected:\n{viol_text}",
                title="[bold red]Guardrail Check Failed[/bold red]",
                box=ROUNDED,
                border_style="red",
            )
        )
    elif action == "redact":
        mod = result.get("modified_data")
        mod_repr = str(mod) if mod is not None else "-"
        console.print(
            Panel(
                f"[bold yellow]POLICY REDACTED: {policy_name}[/bold yellow]\n"
                f"Action: [bold yellow]{action.upper()}[/bold yellow]\n\n"
                f"Sanitized Output:\n[dim]{mod_repr}[/dim]",
                title="[bold yellow]Guardrail PII Redaction[/bold yellow]",
                box=ROUNDED,
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold green]POLICY PASSED: {policy_name}[/bold green]\n"
                f"Action: [bold green]{action.upper()}[/bold green]\n"
                f"Payload conforms to guardrail requirements.",
                title="[bold green]Guardrail Check Passed[/bold green]",
                box=ROUNDED,
                border_style="green",
            )
        )


def display_eval_suites_table(suites: list[dict[str, Any]], total: int) -> None:
    """Display table of evaluation suites."""
    table = Table(title=f"Evaluation Suites ({total})", box=ROUNDED, header_style="bold cyan")
    table.add_column("Suite ID", style="dim", no_wrap=True)
    table.add_column("Suite Name", style="bold", no_wrap=True)
    table.add_column("Agent ID", style="dim", no_wrap=True)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Cases", justify="right")
    table.add_column("Evaluators", justify="right")
    table.add_column("Updated", style="dim")

    for s in suites:
        cfg = s.get("config", {}) or {}
        cases = len(cfg.get("cases", []))
        evaluators = len(cfg.get("evaluators", []))
        table.add_row(
            str(s.get("id", ""))[:8] + "...",
            str(s.get("name", "-")),
            str(s.get("agent_id", ""))[:8] + "...",
            str(s.get("eval_type", "offline")),
            str(cases),
            str(evaluators),
            str(s.get("updated_at", "-"))[:19],
        )

    console.print(table)


def display_eval_run_result(run_data: dict[str, Any]) -> None:
    """Display evaluation run assertions and summary badge."""
    run_id = str(run_data.get("id", "-"))
    suite_id = str(run_data.get("suite_id", "-"))
    status_str = str(run_data.get("status", "completed")).upper()
    total_cases = run_data.get("total_cases", 0)
    passed_cases = run_data.get("passed_cases", 0)
    pass_rate = run_data.get("pass_rate")
    duration_ms = run_data.get("duration_ms", 0)

    pass_rate_str = f"{pass_rate * 100:.1f}%" if pass_rate is not None else "0.0%"
    is_success = status_str == "COMPLETED" and (pass_rate is not None and pass_rate >= 0.8)
    badge_style = "bold green" if is_success else "bold red"
    border_style = "green" if is_success else "red"

    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("Key", style="dim")
    summary_table.add_column("Value", style="bold")
    summary_table.add_row("Run ID", run_id)
    summary_table.add_row("Suite ID", suite_id)
    summary_table.add_row("Status", f"[{badge_style}]{status_str}[/{badge_style}]")
    summary_table.add_row("Pass Rate", f"[{badge_style}]{pass_rate_str}[/{badge_style}]")
    summary_table.add_row("Assertions", f"{passed_cases} / {total_cases} passed")
    summary_table.add_row("Duration", f"{duration_ms} ms")

    console.print(
        Panel(
            summary_table,
            title=f"[{badge_style}]Offline Evaluation Summary[/{badge_style}]",
            box=ROUNDED,
            border_style=border_style,
        )
    )

    results = run_data.get("results", [])
    if results:
        res_table = Table(title="Assertion Results", box=ROUNDED, header_style="bold cyan")
        res_table.add_column("Case", style="bold")
        res_table.add_column("Evaluator")
        res_table.add_column("Type", style="dim")
        res_table.add_column("Outcome", justify="center")
        res_table.add_column("Score", justify="right")
        res_table.add_column("Latency", justify="right", style="dim")
        res_table.add_column("Failure / Note")

        for r in results:
            passed = r.get("passed", False)
            outcome = "[bold green]PASS[/bold green]" if passed else "[bold red]FAIL[/bold red]"
            score = f"{r.get('score', 0.0):.2f}"
            latency = f"{r.get('latency_ms', 0)}ms"
            fail_reason = r.get("failure_reason") or "-"
            fail_reason = f"[red]{fail_reason}[/red]" if not passed else f"[dim]{fail_reason}[/dim]"

            res_table.add_row(
                str(r.get("case_name") or r.get("case_id")),
                str(r.get("evaluator_name")),
                str(r.get("evaluator_type")),
                outcome,
                score,
                latency,
                fail_reason,
            )

        console.print(res_table)
