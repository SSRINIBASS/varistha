"""Unit tests for SQLAlchemy database models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from shared.db.models import Agent, AgentVersion, Run, Span
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_agent_create_defaults(test_session: AsyncSession) -> None:
    """Agent created with minimal fields gets defaults and timestamps."""
    agent = Agent(
        name="lead-researcher",
        owner="founder@example.com",
    )
    test_session.add(agent)
    await test_session.commit()
    await test_session.refresh(agent)

    assert isinstance(agent.id, uuid.UUID)
    assert agent.name == "lead-researcher"
    assert agent.owner == "founder@example.com"
    assert agent.stage == "draft"
    assert agent.current_version is None
    assert agent.created_at is not None
    assert agent.updated_at is not None


async def test_agent_name_unique(test_session: AsyncSession) -> None:
    """Duplicate agent name violates unique constraint."""
    agent1 = Agent(name="duplicate-slug", owner="a@example.com")
    agent2 = Agent(name="duplicate-slug", owner="b@example.com")
    test_session.add(agent1)
    await test_session.commit()

    test_session.add(agent2)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()


async def test_agent_version_create_and_relationship(test_session: AsyncSession) -> None:
    """AgentVersion correctly associates with Agent and stores spec JSON."""
    agent = Agent(name="market-researcher", owner="a@example.com")
    test_session.add(agent)
    await test_session.commit()

    spec_payload = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": "market-researcher",
            "owner": "a@example.com",
            "stage": "prototype",
            "version": "0.1.0",
        },
        "spec": {
            "role": "Market researcher",
            "model": {"primary": "gpt-4o"},
            "instructions": "Research market",
            "autonomy": "L1",
            "triggers": [{"type": "manual"}],
        },
    }

    version = AgentVersion(
        agent_id=agent.id,
        version="0.1.0",
        spec=spec_payload,
    )
    test_session.add(version)
    await test_session.commit()

    # Verify relationship navigation
    stmt = select(Agent).where(Agent.id == agent.id)
    result = await test_session.execute(stmt)
    loaded_agent = result.scalar_one()

    assert len(loaded_agent.versions) == 1
    assert loaded_agent.versions[0].version == "0.1.0"
    assert loaded_agent.versions[0].spec["spec"]["role"] == "Market researcher"
    assert loaded_agent.versions[0].agent.id == agent.id


async def test_agent_version_unique_per_agent(test_session: AsyncSession) -> None:
    """Duplicate (agent_id, version) violates unique constraint."""
    agent1 = Agent(name="agent-one", owner="a@example.com")
    agent2 = Agent(name="agent-two", owner="a@example.com")
    test_session.add_all([agent1, agent2])
    await test_session.commit()

    v1 = AgentVersion(agent_id=agent1.id, version="1.0.0", spec={"v": "1.0.0"})
    test_session.add(v1)
    await test_session.commit()

    # Same version on agent2 succeeds
    v_other = AgentVersion(agent_id=agent2.id, version="1.0.0", spec={"v": "1.0.0"})
    test_session.add(v_other)
    await test_session.commit()

    # Same version on agent1 fails
    v_dup = AgentVersion(agent_id=agent1.id, version="1.0.0", spec={"v": "1.0.0"})
    test_session.add(v_dup)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    await test_session.rollback()


async def test_run_create_and_link(test_session: AsyncSession) -> None:
    """Run records execution details and foreign key associations."""
    agent = Agent(name="coder", owner="c@example.com")
    test_session.add(agent)
    await test_session.commit()

    run = Run(
        agent_id=agent.id,
        status="running",
        trigger_type="manual",
        input={"query": "find bugs"},
        started_at=datetime.now(UTC),
        cost_usd=0.015,
        total_tokens=1500,
    )
    test_session.add(run)
    await test_session.commit()
    await test_session.refresh(run)

    assert isinstance(run.id, uuid.UUID)
    assert run.agent_id == agent.id
    assert run.status == "running"
    assert run.input == {"query": "find bugs"}
    assert run.cost_usd == 0.015
    assert run.total_tokens == 1500
    assert run.agent.name == "coder"


async def test_span_create_and_hierarchy(test_session: AsyncSession) -> None:
    """Span records trace hierarchy and associates with Run."""
    agent = Agent(name="tracer-agent", owner="t@example.com")
    test_session.add(agent)
    await test_session.commit()

    run = Run(agent_id=agent.id, status="running")
    test_session.add(run)
    await test_session.commit()

    root_span = Span(
        run_id=run.id,
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
        name="agent_execution",
        kind="INTERNAL",
        start_time=datetime.now(UTC),
        attributes={"varistha.agent.name": "tracer-agent"},
    )
    child_span = Span(
        run_id=run.id,
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="5fb397be34d23b0f",
        parent_span_id="00f067aa0ba902b7",
        name="llm_call",
        kind="CLIENT",
        start_time=datetime.now(UTC),
        attributes={"gen_ai.system": "openai", "gen_ai.request.model": "gpt-4o"},
    )
    test_session.add_all([root_span, child_span])
    await test_session.commit()

    stmt = select(Run).where(Run.id == run.id)
    result = await test_session.execute(stmt)
    loaded_run = result.scalar_one()

    assert len(loaded_run.spans) == 2
    span_names = [s.name for s in loaded_run.spans]
    assert "agent_execution" in span_names
    assert "llm_call" in span_names
    assert child_span.parent_span_id == root_span.span_id


async def test_cascade_delete(test_session: AsyncSession) -> None:
    """Deleting an agent cascades deletion to its versions, runs, and spans."""
    agent = Agent(name="to-delete", owner="del@example.com")
    test_session.add(agent)
    await test_session.commit()

    version = AgentVersion(agent_id=agent.id, version="0.1.0", spec={})
    run = Run(agent_id=agent.id, status="completed")
    test_session.add_all([version, run])
    await test_session.commit()

    span = Span(
        run_id=run.id,
        trace_id="trace-1",
        span_id="span-1",
        name="step",
        start_time=datetime.now(UTC),
    )
    test_session.add(span)
    await test_session.commit()

    # Delete agent
    await test_session.delete(agent)
    await test_session.commit()

    # Verify everything was removed
    versions = (await test_session.execute(select(AgentVersion))).scalars().all()
    runs = (await test_session.execute(select(Run))).scalars().all()
    spans = (await test_session.execute(select(Span))).scalars().all()

    assert len(versions) == 0
    assert len(runs) == 0
    assert len(spans) == 0
