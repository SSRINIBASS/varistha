import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { LifecycleBoard } from "@/components/lifecycle-board";
import { PromoteModal } from "@/components/promote-modal";
import { StageHistoryModal } from "@/components/stage-history-modal";
import { VersionDiffModal } from "@/components/version-diff-modal";
import type { Agent, GateEvaluation, StageTransition, SpecDiff } from "@/lib/types";
import * as api from "@/lib/api";

// Mock API module
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    getAgents: vi.fn(),
    getGateEvaluation: vi.fn(),
    promoteAgent: vi.fn(),
    getStageHistory: vi.fn(),
    getAgentVersions: vi.fn(),
    getVersionDiff: vi.fn(),
  };
});

describe("LifecycleBoard", () => {
  const mockAgents: Agent[] = [
    {
      id: "agent-1",
      name: "lead-researcher",
      description: "Autonomous market research agent",
      owner: "alice@example.com",
      stage: "prototype",
      current_version: "1.0.0",
      created_at: "2026-10-15T10:00:00Z",
      updated_at: "2026-10-15T10:00:00Z",
      version_count: 2,
    },
    {
      id: "agent-2",
      name: "support-bot",
      description: "Customer triage specialist",
      owner: "bob@example.com",
      stage: "production",
      current_version: "2.1.0",
      created_at: "2026-10-10T10:00:00Z",
      updated_at: "2026-10-14T10:00:00Z",
      version_count: 5,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 6 stage columns and distributes agents appropriately", () => {
    render(<LifecycleBoard initialAgents={mockAgents} />);

    // Check all 6 columns exist
    expect(screen.getByText("Draft")).toBeDefined();
    expect(screen.getByText("Prototype")).toBeDefined();
    expect(screen.getByText("Staging")).toBeDefined();
    expect(screen.getByText("Production")).toBeDefined();
    expect(screen.getByText("Deprecated")).toBeDefined();
    expect(screen.getByText("Retired")).toBeDefined();

    // Check agent cards appear in correct columns
    expect(screen.getByText("lead-researcher")).toBeDefined();
    expect(screen.getByText("support-bot")).toBeDefined();
    expect(screen.getByText("v1.0.0")).toBeDefined();
    expect(screen.getByText("v2.1.0")).toBeDefined();
  });

  it("filters agents dynamically based on search query", () => {
    render(<LifecycleBoard initialAgents={mockAgents} />);

    const searchInput = screen.getByPlaceholderText("Filter by name or owner...");
    fireEvent.change(searchInput, { target: { value: "lead" } });

    expect(screen.getByText("lead-researcher")).toBeDefined();
    expect(screen.queryByText("support-bot")).toBeNull();
  });
});

describe("PromoteModal", () => {
  const mockAgent: Agent = {
    id: "agent-1",
    name: "lead-researcher",
    description: "Autonomous market research agent",
    owner: "alice@example.com",
    stage: "prototype",
    current_version: "1.0.0",
    created_at: "2026-10-15T10:00:00Z",
    updated_at: "2026-10-15T10:00:00Z",
    version_count: 1,
  };

  const passingEvaluation: GateEvaluation = {
    allowed: true,
    from_stage: "prototype",
    to_stage: "staging",
    is_rollback: false,
    checks: [
      { name: "Owner Verified", passed: true, message: "Valid owner alice@example.com" },
      { name: "Run Count", passed: true, message: "12 completed prototype runs" },
      { name: "Guardrails Configured", passed: true, message: "3 guardrails active" },
    ],
  };

  const failingEvaluation: GateEvaluation = {
    allowed: false,
    from_stage: "prototype",
    to_stage: "staging",
    is_rollback: false,
    checks: [
      { name: "Owner Verified", passed: true, message: "Valid owner" },
      { name: "Run Count", passed: false, message: "Minimum 5 runs required, found 1" },
    ],
    error_message: "Gate check failed: Run count insufficient",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("evaluates gates and enables confirmation when all gates pass", async () => {
    vi.mocked(api.getGateEvaluation).mockResolvedValue(passingEvaluation);

    render(
      <PromoteModal
        agent={mockAgent}
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    // Verify gate checks appear
    await waitFor(() => {
      expect(screen.getByText("Owner Verified")).toBeDefined();
      expect(screen.getByText("Run Count")).toBeDefined();
      expect(screen.getByText("All Gates Passed")).toBeDefined();
    });

    const confirmButton = screen.getByRole("button", { name: /execute promotion/i });
    expect(confirmButton.hasAttribute("disabled")).toBe(false);
  });

  it("disables confirmation button and shows error message when gates fail", async () => {
    vi.mocked(api.getGateEvaluation).mockResolvedValue(failingEvaluation);

    render(
      <PromoteModal
        agent={mockAgent}
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Gates Unsatisfied")).toBeDefined();
      expect(screen.getByText(/minimum 5 runs required/i)).toBeDefined();
    });

    const confirmButton = screen.getByRole("button", { name: /execute promotion/i });
    expect(confirmButton.hasAttribute("disabled")).toBe(true);
  });
});

describe("StageHistoryModal", () => {
  const mockAgent: Agent = {
    id: "agent-1",
    name: "lead-researcher",
    owner: "alice@example.com",
    stage: "staging",
    current_version: "1.0.0",
    created_at: "2026-10-15T10:00:00Z",
    updated_at: "2026-10-15T10:00:00Z",
    version_count: 1,
  };

  const mockHistory: StageTransition[] = [
    {
      id: "trans-1",
      agent_id: "agent-1",
      from_stage: "prototype",
      to_stage: "staging",
      promoted_by: "alice@example.com",
      reason: "Ready for shadow runs against live test data",
      gate_results: [
        { name: "Owner Check", passed: true },
        { name: "Runs Gate", passed: true },
      ],
      created_at: "2026-10-15T12:00:00Z",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders audit trail of historical stage transitions", async () => {
    vi.mocked(api.getStageHistory).mockResolvedValue(mockHistory);

    render(
      <StageHistoryModal
        agent={mockAgent}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Ready for shadow runs against live test data/i)).toBeDefined();
      expect(screen.getByText(/alice@example.com/i)).toBeDefined();
    });
  });
});

describe("VersionDiffModal", () => {
  const mockAgent: Agent = {
    id: "agent-1",
    name: "lead-researcher",
    owner: "alice@example.com",
    stage: "staging",
    current_version: "2.0.0",
    created_at: "2026-10-15T10:00:00Z",
    updated_at: "2026-10-15T10:00:00Z",
    version_count: 2,
  };

  const mockVersions = [
    { id: "v2", agent_id: "agent-1", version: "2.0.0", spec: {}, created_at: "2026-10-15T12:00:00Z" },
    { id: "v1", agent_id: "agent-1", version: "1.0.0", spec: {}, created_at: "2026-10-15T10:00:00Z" },
  ];

  const mockBreakingDiff: SpecDiff = {
    from_version: "1.0.0",
    to_version: "2.0.0",
    has_changes: true,
    has_breaking_changes: true,
    summary: { added: 0, removed: 0, modified: 2, breaking: 1 },
    entries: [
      {
        field: "runtime.autonomy",
        change_type: "modified",
        old_value: "L1",
        new_value: "L2",
        is_breaking: true,
        breaking_reason: "Autonomy escalation from L1 to L2 requires governance gate approval",
        description: "Autonomy escalated",
      },
      {
        field: "metadata.description",
        change_type: "modified",
        old_value: "Old desc",
        new_value: "New desc",
        is_breaking: false,
        breaking_reason: null,
        description: "Description updated",
      },
    ],
    breaking_entries: [
      {
        field: "runtime.autonomy",
        change_type: "modified",
        old_value: "L1",
        new_value: "L2",
        is_breaking: true,
        breaking_reason: "Autonomy escalation from L1 to L2 requires governance gate approval",
        description: "Autonomy escalated",
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders breaking changes banner and field deltas", async () => {
    vi.mocked(api.getAgentVersions).mockResolvedValue(mockVersions);
    vi.mocked(api.getVersionDiff).mockResolvedValue(mockBreakingDiff);

    render(
      <VersionDiffModal
        agent={mockAgent}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Breaking Changes Detected in Target Version")).toBeDefined();
      expect(screen.getByText("runtime.autonomy")).toBeDefined();
      expect(screen.getByText(/Autonomy escalation from L1 to L2/i)).toBeDefined();
    });
  });
});
