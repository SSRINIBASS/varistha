import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { ApprovalStatusBadge, KillSwitchBadge } from "@/components/badges";
import { PayloadDiffViewer } from "@/components/governance/payload-diff-viewer";
import { ApprovalsInbox } from "@/components/governance/approvals-inbox";
import { BudgetsDashboard } from "@/components/governance/budgets-dashboard";
import { GuardrailsExplorer } from "@/components/governance/guardrails-explorer";
import type {
  Agent,
  AgentBudgetStatus,
  ApprovalItem,
  GlobalKillSwitchStatus,
  PolicyInfo,
} from "@/lib/types";
import * as api from "@/lib/api";

// Mock API module
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    resolveApproval: vi.fn(),
    tripAgentKillSwitch: vi.fn(),
    resumeAgent: vi.fn(),
    setGlobalKillSwitch: vi.fn(),
    testPolicy: vi.fn(),
  };
});

describe("Governance Badges", () => {
  it("renders ApprovalStatusBadge variations", () => {
    const { rerender } = render(<ApprovalStatusBadge status="pending" />);
    expect(screen.getByText("Pending")).toBeDefined();

    rerender(<ApprovalStatusBadge status="approved" />);
    expect(screen.getByText("Approved")).toBeDefined();

    rerender(<ApprovalStatusBadge status="rejected" />);
    expect(screen.getByText("Rejected")).toBeDefined();

    rerender(<ApprovalStatusBadge status="edited" />);
    expect(screen.getByText("Edited")).toBeDefined();
  });

  it("renders KillSwitchBadge halted and active states", () => {
    const { rerender } = render(<KillSwitchBadge tripped={true} />);
    expect(screen.getByText("Halted")).toBeDefined();

    rerender(<KillSwitchBadge tripped={false} />);
    expect(screen.getByText("Active")).toBeDefined();
  });
});

describe("PayloadDiffViewer", () => {
  it("renders single proposed payload when payloads are identical", () => {
    const payload = { recipient: "alice@acme.com", message: "Hello" };
    render(<PayloadDiffViewer proposedPayload={payload} />);
    expect(screen.getByText("Proposed Payload")).toBeDefined();
  });

  it("renders side-by-side diff when approved payload is modified", () => {
    const proposed = { recipient: "alice@acme.com", message: "Draft text" };
    const approved = { recipient: "alice@acme.com", message: "Approved final text" };
    render(<PayloadDiffViewer proposedPayload={proposed} approvedPayload={approved} />);
    expect(screen.getByText("Original (Proposed by Agent)")).toBeDefined();
    expect(screen.getByText("Approved / Edited Payload")).toBeDefined();
  });
});

describe("ApprovalsInbox", () => {
  const mockApprovals: ApprovalItem[] = [
    {
      id: "app-1",
      run_id: "run-uuid-12345678",
      agent_id: "agent-1",
      status: "pending",
      action_type: "outbound_action",
      tool_name: "send_email",
      description: "Send contract email to counterparty",
      proposed_payload: { to: "partner@deal.com", body: "Please review agreement" },
      created_at: "2026-10-15T12:00:00Z",
    },
    {
      id: "app-2",
      run_id: "run-uuid-87654321",
      agent_id: "agent-2",
      status: "approved",
      action_type: "outbound_action",
      tool_name: "post_tweet",
      description: "Post changelog update on social",
      proposed_payload: { status: "v1.2.0 released!" },
      approved_payload: { status: "v1.2.0 released!" },
      created_at: "2026-10-15T10:00:00Z",
      resolved_at: "2026-10-15T10:05:00Z",
      reviewer: "admin",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders approval list and filters by status tab", () => {
    render(<ApprovalsInbox approvals={mockApprovals} onRefresh={vi.fn()} />);

    // Default filter is 'pending'
    expect(screen.getByText("Send contract email to counterparty")).toBeDefined();

    // Switch to 'all' tab
    const allTab = screen.getByText("all");
    fireEvent.click(allTab);
    expect(screen.getByText("Post changelog update on social")).toBeDefined();
  });

  it("opens approval inspection modal and triggers approval action", async () => {
    vi.mocked(api.resolveApproval).mockResolvedValueOnce({
      ...mockApprovals[0]!,
      status: "approved",
      resolved_at: "2026-10-15T12:05:00Z",
      reviewer: "operator",
    } as ApprovalItem);

    const onRefresh = vi.fn();
    render(<ApprovalsInbox approvals={mockApprovals} onRefresh={onRefresh} />);

    // Click row to open modal
    fireEvent.click(screen.getByText("Send contract email to counterparty"));
    expect(screen.getByText(/Approval Request: send_email/)).toBeDefined();

    // Click Approve button (exact match to distinguish from Save & Approve)
    const approveBtn = screen.getByRole("button", { name: /^Approve$/i });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(api.resolveApproval).toHaveBeenCalledWith("app-1", {
        action: "approve",
        reviewer: "operator",
      });
      expect(onRefresh).toHaveBeenCalled();
    });
  });
});

describe("BudgetsDashboard", () => {
  const mockAgents: Agent[] = [
    {
      id: "agent-1",
      name: "lead-researcher",
      stage: "production",
      current_version: "1.0.0",
      created_at: "2026-10-15T10:00:00Z",
      updated_at: "2026-10-15T10:00:00Z",
      version_count: 1,
    },
  ];

  const mockBudgets: Record<string, AgentBudgetStatus> = {
    "lead-researcher": {
      agent_id: "agent-1",
      agent_name: "lead-researcher",
      daily_spend_usd: 1.5,
      daily_budget_usd: 10.0,
      remaining_daily_budget_usd: 8.5,
      max_usd_per_run: 0.5,
      is_active: true,
      kill_switch_tripped: false,
    },
  };

  const mockGlobalKs: GlobalKillSwitchStatus = {
    enabled: false,
    reason: null,
    tripped_at: null,
    operator: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders global emergency stop banner and agent budget metrics", () => {
    render(
      <BudgetsDashboard
        agents={mockAgents}
        budgets={mockBudgets}
        globalKillSwitch={mockGlobalKs}
        onRefresh={vi.fn()}
      />
    );

    expect(screen.getByText("Global Emergency Stop")).toBeDefined();
    expect(screen.getByText("INACTIVE (NORMAL)")).toBeDefined();
    expect(screen.getByText("lead-researcher")).toBeDefined();
    expect(screen.getByText(/\$1\.5000/)).toBeDefined();
    expect(screen.getByText("Trip Kill Switch")).toBeDefined();
  });

  it("opens kill switch prompt and trips agent circuit breaker", async () => {
    vi.mocked(api.tripAgentKillSwitch).mockResolvedValueOnce({
      ...mockBudgets["lead-researcher"]!,
      is_active: false,
      kill_switch_tripped: true,
      kill_switch_reason: "High error rate",
    } as AgentBudgetStatus);

    const onRefresh = vi.fn();
    render(
      <BudgetsDashboard
        agents={mockAgents}
        budgets={mockBudgets}
        globalKillSwitch={mockGlobalKs}
        onRefresh={onRefresh}
      />
    );

    // Click Trip Kill Switch
    fireEvent.click(screen.getByText("Trip Kill Switch"));
    expect(screen.getByText(/Halt Agent: lead-researcher/)).toBeDefined();

    // Type reason and confirm
    const reasonInput = screen.getByPlaceholderText(/Unusual tool error rate/i);
    fireEvent.change(reasonInput, { target: { value: "High error rate" } });

    fireEvent.click(screen.getByText("Confirm Halt"));

    await waitFor(() => {
      expect(api.tripAgentKillSwitch).toHaveBeenCalledWith("lead-researcher", "High error rate");
      expect(onRefresh).toHaveBeenCalled();
    });
  });
});

describe("GuardrailsExplorer", () => {
  const mockPolicies: PolicyInfo[] = [
    {
      name: "pii-redact",
      description: "Redacts sensitive PII from content",
      supported_hooks: ["input", "output", "tools"],
    },
    {
      name: "injection-scan",
      description: "Blocks prompt injection attacks",
      supported_hooks: ["input", "tools"],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists active guardrail policies and executes evaluation in sandbox", async () => {
    vi.mocked(api.testPolicy).mockResolvedValueOnce({
      policy_name: "pii-redact",
      passed: true,
      action: "redact",
      modified_data: "Contact [REDACTED_EMAIL]",
      violations: [],
      metadata: { total_redactions: 1 },
    });

    render(<GuardrailsExplorer policies={mockPolicies} />);

    expect(screen.getAllByText("pii-redact").length).toBeGreaterThan(0);
    expect(screen.getAllByText("injection-scan").length).toBeGreaterThan(0);

    // Evaluate
    const evalBtn = screen.getByRole("button", { name: /Evaluate Guardrail/i });
    fireEvent.click(evalBtn);

    await waitFor(() => {
      expect(api.testPolicy).toHaveBeenCalled();
      expect(screen.getByText("SANITIZED (REDACT)")).toBeDefined();
      expect(screen.getByText(/\[REDACTED_EMAIL\]/)).toBeDefined();
    });
  });
});
