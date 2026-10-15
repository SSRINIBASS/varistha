"""Spec diffing engine for Varistha Agent Specifications.

Detects field-level deltas between two AgentSpec versions and classifies
changes as breaking vs non-breaking per docs/SPEC.md § 5.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from models import AgentSpec, BudgetConfig, EvalConfig, GuardrailsConfig
from pydantic import BaseModel, Field
from validator import validate_spec

# Autonomy level ordering for escalation detection
_AUTONOMY_LEVELS: dict[str, int] = {
    "L0": 0,
    "L1": 1,
    "L2": 2,
    "L3": 3,
}


class ChangeType(StrEnum):
    """Classification of the nature of a field difference."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class DiffEntry(BaseModel):
    """A single detected change between two agent specifications."""

    field: str = Field(..., description="Dotted path of the changed field.")
    change_type: ChangeType = Field(..., description="added, removed, or modified.")
    old_value: Any = Field(default=None, description="Previous value or None if added.")
    new_value: Any = Field(default=None, description="New value or None if removed.")
    is_breaking: bool = Field(default=False, description="Whether this change is breaking.")
    breaking_reason: str | None = Field(
        default=None, description="Explanation if this change is breaking."
    )
    description: str = Field(..., description="Human-readable description of the change.")


class SpecDiff(BaseModel):
    """Structured diff summary comparing two agent specifications."""

    from_version: str | None = Field(default=None, description="Base/source version string.")
    to_version: str | None = Field(default=None, description="Target/new version string.")
    has_changes: bool = Field(default=False, description="True if any difference was detected.")
    has_breaking_changes: bool = Field(
        default=False, description="True if any breaking difference exists."
    )
    summary: dict[str, int] = Field(
        default_factory=dict, description="Counts of total, added, removed, modified, breaking."
    )
    entries: list[DiffEntry] = Field(default_factory=list, description="All detected diff entries.")
    breaking_entries: list[DiffEntry] = Field(
        default_factory=list, description="Filtered list of breaking diff entries."
    )


def _ensure_spec(spec: Any) -> AgentSpec:
    """Coerce a raw dict or validate an AgentSpec."""
    if isinstance(spec, AgentSpec):
        return spec
    if isinstance(spec, dict):
        return validate_spec(spec)
    msg = f"Expected AgentSpec or dict, got {type(spec).__name__}"
    raise TypeError(msg)



def _diff_metadata(old: AgentSpec, new: AgentSpec, entries: list[DiffEntry]) -> None:
    """Compare metadata block."""
    if old.metadata.name != new.metadata.name:
        entries.append(
            DiffEntry(
                field="metadata.name",
                change_type=ChangeType.MODIFIED,
                old_value=old.metadata.name,
                new_value=new.metadata.name,
                is_breaking=True,
                breaking_reason="Agent identifier slug cannot be changed between versions.",
                description=(
                    f"Agent name changed from '{old.metadata.name}' to '{new.metadata.name}'."
                ),
            )
        )
    if old.metadata.owner != new.metadata.owner:
        entries.append(
            DiffEntry(
                field="metadata.owner",
                change_type=ChangeType.MODIFIED,
                old_value=old.metadata.owner,
                new_value=new.metadata.owner,
                is_breaking=False,
                description=f"Owner updated from '{old.metadata.owner}' to '{new.metadata.owner}'.",
            )
        )
    if old.metadata.stage != new.metadata.stage:
        entries.append(
            DiffEntry(
                field="metadata.stage",
                change_type=ChangeType.MODIFIED,
                old_value=old.metadata.stage,
                new_value=new.metadata.stage,
                is_breaking=False,
                description=f"Stage changed from '{old.metadata.stage}' to '{new.metadata.stage}'.",
            )
        )
    if old.metadata.version != new.metadata.version:
        entries.append(
            DiffEntry(
                field="metadata.version",
                change_type=ChangeType.MODIFIED,
                old_value=old.metadata.version,
                new_value=new.metadata.version,
                is_breaking=False,
                description=(
                    f"Version updated from '{old.metadata.version}' to '{new.metadata.version}'."
                ),
            )
        )


def _diff_core_spec(old: AgentSpec, new: AgentSpec, entries: list[DiffEntry]) -> None:
    """Compare role, instructions, and autonomy."""
    if old.spec.role != new.spec.role:
        entries.append(
            DiffEntry(
                field="spec.role",
                change_type=ChangeType.MODIFIED,
                old_value=old.spec.role,
                new_value=new.spec.role,
                is_breaking=False,
                description="Agent role description updated.",
            )
        )
    if old.spec.instructions != new.spec.instructions:
        entries.append(
            DiffEntry(
                field="spec.instructions",
                change_type=ChangeType.MODIFIED,
                old_value=old.spec.instructions,
                new_value=new.spec.instructions,
                is_breaking=False,
                description="Agent prompt instructions updated.",
            )
        )

    old_lvl = _AUTONOMY_LEVELS.get(old.spec.autonomy, 1)
    new_lvl = _AUTONOMY_LEVELS.get(new.spec.autonomy, 1)
    if old.spec.autonomy != new.spec.autonomy:
        is_breaking = new_lvl > old_lvl
        entries.append(
            DiffEntry(
                field="spec.autonomy",
                change_type=ChangeType.MODIFIED,
                old_value=old.spec.autonomy,
                new_value=new.spec.autonomy,
                is_breaking=is_breaking,
                breaking_reason=(
                    f"Autonomy escalated from {old.spec.autonomy} to {new.spec.autonomy}, "
                    "expanding agent execution permissions."
                    if is_breaking
                    else None
                ),
                description=(
                    f"Autonomy escalated to {new.spec.autonomy}."
                    if is_breaking
                    else f"Autonomy restricted to {new.spec.autonomy}."
                ),
            )
        )


def _diff_model(old: AgentSpec, new: AgentSpec, entries: list[DiffEntry]) -> None:
    """Compare model configuration."""
    if old.spec.model.primary != new.spec.model.primary:
        entries.append(
            DiffEntry(
                field="spec.model.primary",
                change_type=ChangeType.MODIFIED,
                old_value=old.spec.model.primary,
                new_value=new.spec.model.primary,
                is_breaking=True,
                breaking_reason=(
                    f"Primary model changed from '{old.spec.model.primary}' to "
                    f"'{new.spec.model.primary}', which may alter prompt adherence and behavior."
                ),
                description=f"Primary model changed to '{new.spec.model.primary}'.",
            )
        )
    if old.spec.model.fallback != new.spec.model.fallback:
        entries.append(
            DiffEntry(
                field="spec.model.fallback",
                change_type=ChangeType.MODIFIED,
                old_value=old.spec.model.fallback,
                new_value=new.spec.model.fallback,
                is_breaking=False,
                description=f"Fallback model changed to '{new.spec.model.fallback}'.",
            )
        )


def _diff_plugins(old: AgentSpec, new: AgentSpec, entries: list[DiffEntry]) -> None:
    """Compare plugin list and toggles."""
    old_plugins = {p.name: p.enabled for p in old.spec.plugins}
    new_plugins = {p.name: p.enabled for p in new.spec.plugins}

    # Removed plugins
    for name in sorted(set(old_plugins.keys()) - set(new_plugins.keys())):
        entries.append(
            DiffEntry(
                field=f"spec.plugins.{name}",
                change_type=ChangeType.REMOVED,
                old_value={"name": name, "enabled": old_plugins[name]},
                new_value=None,
                is_breaking=True,
                breaking_reason=f"Plugin '{name}' removed from agent capabilities.",
                description=f"Plugin '{name}' removed.",
            )
        )

    # Added plugins
    for name in sorted(set(new_plugins.keys()) - set(old_plugins.keys())):
        entries.append(
            DiffEntry(
                field=f"spec.plugins.{name}",
                change_type=ChangeType.ADDED,
                old_value=None,
                new_value={"name": name, "enabled": new_plugins[name]},
                is_breaking=False,
                description=f"Plugin '{name}' added (enabled: {new_plugins[name]}).",
            )
        )

    # Modified plugins (enabled toggle changed)
    for name in sorted(set(old_plugins.keys()) & set(new_plugins.keys())):
        if old_plugins[name] != new_plugins[name]:
            was_disabled = old_plugins[name] is True and new_plugins[name] is False
            entries.append(
                DiffEntry(
                    field=f"spec.plugins.{name}.enabled",
                    change_type=ChangeType.MODIFIED,
                    old_value=old_plugins[name],
                    new_value=new_plugins[name],
                    is_breaking=was_disabled,
                    breaking_reason=(
                        f"Active plugin '{name}' was disabled." if was_disabled else None
                    ),
                    description=f"Plugin '{name}' enabled toggled to {new_plugins[name]}.",
                )
            )


def _diff_guardrails(
    old_g: GuardrailsConfig | None, new_g: GuardrailsConfig | None, entries: list[DiffEntry]
) -> None:
    """Compare guardrail policy configurations."""
    for category in ("input", "output", "tools"):
        old_rules = set(getattr(old_g, category, []) if old_g else [])
        new_rules = set(getattr(new_g, category, []) if new_g else [])

        for rule in sorted(old_rules - new_rules):
            entries.append(
                DiffEntry(
                    field=f"spec.guardrails.{category}.{rule}",
                    change_type=ChangeType.REMOVED,
                    old_value=rule,
                    new_value=None,
                    is_breaking=True,
                    breaking_reason=(
                        f"Security guardrail '{rule}' was removed from {category} policies."
                    ),
                    description=f"Guardrail '{rule}' removed from {category}.",
                )
            )
        for rule in sorted(new_rules - old_rules):
            entries.append(
                DiffEntry(
                    field=f"spec.guardrails.{category}.{rule}",
                    change_type=ChangeType.ADDED,
                    old_value=None,
                    new_value=rule,
                    is_breaking=False,
                    description=f"Guardrail '{rule}' added to {category}.",
                )
            )


def _diff_budget(
    old_b: BudgetConfig | None, new_b: BudgetConfig | None, entries: list[DiffEntry]
) -> None:
    """Compare budget spend constraints."""
    if old_b and not new_b:
        entries.append(
            DiffEntry(
                field="spec.budget",
                change_type=ChangeType.REMOVED,
                old_value=old_b.model_dump(),
                new_value=None,
                is_breaking=True,
                breaking_reason="Budget constraints removed entirely, permitting unlimited spend.",
                description="Budget limits removed.",
            )
        )
        return

    if not old_b and new_b:
        entries.append(
            DiffEntry(
                field="spec.budget",
                change_type=ChangeType.ADDED,
                old_value=None,
                new_value=new_b.model_dump(),
                is_breaking=False,
                description="Budget constraints added.",
            )
        )
        return

    if old_b and new_b:
        if old_b.max_usd_per_run != new_b.max_usd_per_run:
            is_breaking = new_b.max_usd_per_run < old_b.max_usd_per_run
            entries.append(
                DiffEntry(
                    field="spec.budget.max_usd_per_run",
                    change_type=ChangeType.MODIFIED,
                    old_value=old_b.max_usd_per_run,
                    new_value=new_b.max_usd_per_run,
                    is_breaking=is_breaking,
                    breaking_reason=(
                        f"Per-run budget lowered from ${old_b.max_usd_per_run:.2f} to "
                        f"${new_b.max_usd_per_run:.2f}, which may cause runs to exceed cost limits."
                        if is_breaking
                        else None
                    ),
                    description=(
                        f"Per-run budget changed to ${new_b.max_usd_per_run:.2f} "
                        f"({'reduced' if is_breaking else 'increased'})."
                    ),
                )
            )
        if old_b.max_usd_per_day != new_b.max_usd_per_day:
            is_breaking = new_b.max_usd_per_day < old_b.max_usd_per_day
            entries.append(
                DiffEntry(
                    field="spec.budget.max_usd_per_day",
                    change_type=ChangeType.MODIFIED,
                    old_value=old_b.max_usd_per_day,
                    new_value=new_b.max_usd_per_day,
                    is_breaking=is_breaking,
                    breaking_reason=(
                        f"Daily budget lowered from ${old_b.max_usd_per_day:.2f} to "
                        f"${new_b.max_usd_per_day:.2f}."
                        if is_breaking
                        else None
                    ),
                    description=(
                        f"Daily budget changed to ${new_b.max_usd_per_day:.2f} "
                        f"({'reduced' if is_breaking else 'increased'})."
                    ),
                )
            )


def _diff_triggers(old: AgentSpec, new: AgentSpec, entries: list[DiffEntry]) -> None:
    """Compare trigger list."""
    old_by_type = {t.type: t.cron for t in old.spec.triggers}
    new_by_type = {t.type: t.cron for t in new.spec.triggers}

    for t_type in sorted(set(old_by_type.keys()) - set(new_by_type.keys())):
        entries.append(
            DiffEntry(
                field=f"spec.triggers.{t_type}",
                change_type=ChangeType.REMOVED,
                old_value={"type": t_type, "cron": old_by_type[t_type]},
                new_value=None,
                is_breaking=True,
                breaking_reason=f"Trigger of type '{t_type}' was removed.",
                description=f"Trigger '{t_type}' removed.",
            )
        )

    for t_type in sorted(set(new_by_type.keys()) - set(old_by_type.keys())):
        entries.append(
            DiffEntry(
                field=f"spec.triggers.{t_type}",
                change_type=ChangeType.ADDED,
                old_value=None,
                new_value={"type": t_type, "cron": new_by_type[t_type]},
                is_breaking=False,
                description=f"Trigger '{t_type}' added.",
            )
        )

    for t_type in sorted(set(old_by_type.keys()) & set(new_by_type.keys())):
        if old_by_type[t_type] != new_by_type[t_type]:
            entries.append(
                DiffEntry(
                    field=f"spec.triggers.{t_type}.cron",
                    change_type=ChangeType.MODIFIED,
                    old_value=old_by_type[t_type],
                    new_value=new_by_type[t_type],
                    is_breaking=False,
                    description=(
                        f"Trigger '{t_type}' cron schedule updated to '{new_by_type[t_type]}'."
                    ),
                )
            )


def _diff_evals(
    old_e: EvalConfig | None, new_e: EvalConfig | None, entries: list[DiffEntry]
) -> None:
    """Compare evals configuration."""
    if old_e and not new_e:
        entries.append(
            DiffEntry(
                field="spec.evals",
                change_type=ChangeType.REMOVED,
                old_value=old_e.model_dump(),
                new_value=None,
                is_breaking=True,
                breaking_reason="Evaluation suite removed from specification.",
                description="Evaluation suite removed.",
            )
        )
        return

    if not old_e and new_e:
        entries.append(
            DiffEntry(
                field="spec.evals",
                change_type=ChangeType.ADDED,
                old_value=None,
                new_value=new_e.model_dump(),
                is_breaking=False,
                description=(
                    f"Eval suite '{new_e.suite}' added with {new_e.min_pass_rate:.0%} threshold."
                ),
            )
        )
        return

    if old_e and new_e:
        if old_e.suite != new_e.suite:
            entries.append(
                DiffEntry(
                    field="spec.evals.suite",
                    change_type=ChangeType.MODIFIED,
                    old_value=old_e.suite,
                    new_value=new_e.suite,
                    is_breaking=False,
                    description=f"Eval suite file changed from '{old_e.suite}' to '{new_e.suite}'.",
                )
            )
        if old_e.min_pass_rate != new_e.min_pass_rate:
            is_stricter = new_e.min_pass_rate > old_e.min_pass_rate
            entries.append(
                DiffEntry(
                    field="spec.evals.min_pass_rate",
                    change_type=ChangeType.MODIFIED,
                    old_value=old_e.min_pass_rate,
                    new_value=new_e.min_pass_rate,
                    is_breaking=is_stricter,
                    breaking_reason=(
                        f"Eval min pass rate increased from {old_e.min_pass_rate:.0%} to "
                        f"{new_e.min_pass_rate:.0%}, making promotion requirements stricter."
                        if is_stricter
                        else None
                    ),
                    description=(
                        f"Eval min pass rate updated to {new_e.min_pass_rate:.0%} "
                        f"({'stricter' if is_stricter else 'relaxed'})."
                    ),
                )
            )


def diff_specs(
    old_spec: AgentSpec | dict[str, Any],
    new_spec: AgentSpec | dict[str, Any],
) -> SpecDiff:
    """Compare two agent specifications and produce a structured diff.

    Args:
        old_spec: The base or previous AgentSpec or specification dict.
        new_spec: The target or new AgentSpec or specification dict.

    Returns:
        A SpecDiff detailing all changes, categorized by breaking impact.

    """
    old = _ensure_spec(old_spec)
    new = _ensure_spec(new_spec)

    entries: list[DiffEntry] = []

    _diff_metadata(old, new, entries)
    _diff_core_spec(old, new, entries)
    _diff_model(old, new, entries)
    _diff_plugins(old, new, entries)
    _diff_guardrails(old.spec.guardrails, new.spec.guardrails, entries)
    _diff_budget(old.spec.budget, new.spec.budget, entries)
    _diff_triggers(old, new, entries)
    _diff_evals(old.spec.evals, new.spec.evals, entries)

    breaking_entries = [e for e in entries if e.is_breaking]

    summary = {
        "total": len(entries),
        "added": sum(1 for e in entries if e.change_type == ChangeType.ADDED),
        "removed": sum(1 for e in entries if e.change_type == ChangeType.REMOVED),
        "modified": sum(1 for e in entries if e.change_type == ChangeType.MODIFIED),
        "breaking": len(breaking_entries),
    }

    return SpecDiff(
        from_version=old.metadata.version,
        to_version=new.metadata.version,
        has_changes=len(entries) > 0,
        has_breaking_changes=len(breaking_entries) > 0,
        summary=summary,
        entries=entries,
        breaking_entries=breaking_entries,
    )
