"""Tests for runtime human-in-the-loop approval interrupts and span generation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from runtime.adapter import LangGraphRuntime
from runtime.interface import RunContext
from runtime.service import trigger_agent_run
from shared.db.models import Agent, AgentVersion, Approval, Span
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


@pytest.mark.asyncio
async def test_runtime_adapter_interrupts_outbound_action_at_l1():
    """Agents at autonomy L1 attempting outbound actions are paused with approval.wait span."""
    adapter = LangGraphRuntime()

    mock_response = MagicMock()
    mock_choice = MagicMock()
    # Model produces an outbound action proposal (send email)
    mock_choice.message.content = (
        '{"action": "send_email", "payload": {"to": "lead@corp.com", "subject": "Demo Request"}}'
    )
    mock_response.choices = [mock_choice]
    mock_response.usage.total_tokens = 150

    with (
        patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
        patch("litellm.completion_cost", return_value=0.003),
    ):
        mock_acompletion.return_value = mock_response

        context = RunContext(
            run_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            agent_name="outbound-agent",
            model="gpt-4o",
            instructions="Handle lead and send email.",
            input_data={"lead": "Acme Corp"},
            spec_snapshot={
                "spec": {
                    "autonomy": "L1",
                    "plugins": [{"name": "email-sender", "enabled": True}],
                }
            },
        )

        result = await adapter.execute(context)

        assert result.status == "waiting_approval"
        assert result.approval_required is True
        assert result.proposed_action is not None
        assert result.proposed_action["action_type"] == "outbound_action"
        assert result.proposed_action["tool_name"] == "send_email"
        assert result.proposed_action["payload"] == {
            "to": "lead@corp.com",
            "subject": "Demo Request",
        }


@pytest.mark.asyncio
async def test_runtime_adapter_allows_autonomous_at_l3():
    """Agents at autonomy L3 execute outbound actions without human interrupt."""
    adapter = LangGraphRuntime()

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"action": "send_email", "payload": {"to": "lead@corp.com"}}'
    mock_response.choices = [mock_choice]
    mock_response.usage.total_tokens = 150

    with (
        patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
        patch("litellm.completion_cost", return_value=0.003),
    ):
        mock_acompletion.return_value = mock_response

        context = RunContext(
            run_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            agent_name="autonomous-agent",
            model="gpt-4o",
            instructions="Automated outreach.",
            input_data={},
            spec_snapshot={
                "spec": {
                    "autonomy": "L3",
                }
            },
        )

        result = await adapter.execute(context)
        assert result.status == "completed"
        assert result.approval_required is False


@pytest.mark.asyncio
async def test_trigger_agent_run_creates_approval_record_and_spans(
    db_session: AsyncSession,
    test_engine: AsyncEngine,
):
    """trigger_agent_run creates an Approval DB record and saves approval.wait span."""
    agent = Agent(
        id=uuid.uuid4(),
        name="sales-bot",
        owner="sales@corp.com",
        stage="staging",
        current_version="0.1.0",
    )
    db_session.add(agent)
    await db_session.flush()

    version = AgentVersion(
        id=uuid.uuid4(),
        agent_id=agent.id,
        version="0.1.0",
        spec={
            "metadata": {"stage": "staging"},
            "spec": {
                "autonomy": "L1",
                "model": {"primary": "gpt-4o"},
                "instructions": "Outreach bot",
            },
        },
    )
    db_session.add(version)
    await db_session.commit()

    adapter = LangGraphRuntime()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"action": "crm_write", "payload": {"lead": "New Deal"}}'
    mock_response.choices = [mock_choice]
    mock_response.usage.total_tokens = 120

    with (
        patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
        patch("litellm.completion_cost", return_value=0.002),
    ):
        mock_acompletion.return_value = mock_response

        run = await trigger_agent_run(
            session=db_session,
            id_or_name=str(agent.id),
            input_data={"lead": "deal_123"},
            trigger_type="manual",
            runtime=adapter,
        )

        assert run.status == "waiting_approval"
        assert run.completed_at is None

        # Verify Approval record was created in the database
        stmt = select(Approval).where(Approval.run_id == run.id)
        appr_res = await db_session.execute(stmt)
        approval = appr_res.scalar_one_or_none()
        assert approval is not None
        assert approval.status == "pending"
        assert approval.tool_name == "crm_write"
        assert approval.proposed_payload == {"lead": "New Deal"}

        # Verify spans: approval.wait span exists in DB
        span_stmt = select(Span).where(Span.run_id == run.id, Span.name == "approval.wait")
        span_res = await db_session.execute(span_stmt)
        wait_span = span_res.scalar_one_or_none()
        assert wait_span is not None
        assert wait_span.attributes is not None
        assert wait_span.attributes.get("varistha.approval_required") is True
