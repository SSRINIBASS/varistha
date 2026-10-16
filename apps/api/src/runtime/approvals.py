"""Runtime approval check utilities enforcing autonomy boundaries outside the model."""

from __future__ import annotations

from typing import Any

OUTBOUND_KEYWORDS = {
    "send_email",
    "email_send",
    "send_newsletter",
    "social",
    "post_social",
    "tweet",
    "post_tweet",
    "x_post",
    "post_to_x",
    "linkedin_post",
    "post_to_linkedin",
    "crm_write",
    "update_crm",
    "slack_post",
    "webhook_post",
}


def check_approval_requirement(
    output: dict[str, Any],
    input_data: dict[str, Any],
    autonomy: str,
) -> tuple[bool, str, str | None, dict[str, Any]]:
    """Determine whether the executed action requires approval outside the model."""
    action_name = (
        output.get("action")
        or output.get("tool")
        or input_data.get("action")
        or input_data.get("tool")
    )
    tool_name = str(action_name) if action_name else None
    action_type = str(output.get("action_type") or input_data.get("action_type") or "tool_call")

    requires_approval = (
        output.get("requires_approval") is True
        or input_data.get("requires_approval") is True
        or action_type == "outbound_action"
    )

    is_outbound = False
    if tool_name:
        normalized = tool_name.lower().replace("-", "_")
        if "draft" not in normalized and any(kw in normalized for kw in OUTBOUND_KEYWORDS):
            is_outbound = True
            action_type = "outbound_action"

    payload = output.get("payload") or output

    # Autonomy L0: Every proposed action/tool requires approval
    if autonomy == "L0" and (tool_name or requires_approval or is_outbound):
        return True, action_type, tool_name, payload

    # Autonomy L1: Outbound actions or tools with requires_approval require approval
    if autonomy == "L1" and (is_outbound or requires_approval):
        return True, action_type, tool_name, payload

    return False, action_type, tool_name, {}
