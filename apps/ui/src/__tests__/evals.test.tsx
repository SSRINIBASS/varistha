import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { ReviewPriorityBadge, RegressionStatusBadge } from "@/components/badges";
import { EvalSuiteRunner } from "@/components/evals/eval-suite-runner";
import { EvalRunDetailView } from "@/components/evals/eval-run-detail";
import { EvalRegressionView } from "@/components/evals/eval-regression-view";
import { ConfidenceSandbox } from "@/components/evals/confidence-sandbox";
import type {
  Agent,
  EvalComparisonReport,
  EvalResult,
  EvalRun,
  EvalRunDetail,
  EvalSuite,
  ReviewPriorityOutcome,
} from "@/lib/types";
import * as api from "@/lib/api";

// Mock API module
vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    executeEvalSuite: vi.fn(),
    compareEvalRuns: vi.fn(),
    evaluateConfidence: vi.fn(),
  };
});

describe("Eval Badges", () => {
  it("renders ReviewPriorityBadge variants correctly", () => {
    const { rerender } = render(<ReviewPriorityBadge priority="low" />);
    expect(screen.getByText("Low Priority")).toBeDefined();

    rerender(<ReviewPriorityBadge priority="medium" />);
    expect(screen.getByText("Medium Priority")).toBeDefined();

    rerender(<ReviewPriorityBadge priority="high" />);
    expect(screen.getByText("High Priority")).toBeDefined();

    rerender(<ReviewPriorityBadge priority="critical" />);
    expect(screen.getByText("Critical")).toBeDefined();
  });

  it("renders RegressionStatusBadge variants correctly", () => {
    const { rerender } = render(<RegressionStatusBadge status="improved" />);
    expect(screen.getByText("Improved")).toBeDefined();

    rerender(<RegressionStatusBadge status="regressed" />);
    expect(screen.getByText("Regressed")).toBeDefined();

    rerender(<RegressionStatusBadge status="added" />);
    expect(screen.getByText("Added")).toBeDefined();

    rerender(<RegressionStatusBadge status="removed" />);
    expect(screen.getByText("Removed")).toBeDefined();

    rerender(<RegressionStatusBadge status="unchanged" />);
    expect(screen.getByText("Unchanged")).toBeDefined();
  });
});

describe("EvalSuiteRunner", () => {
  const mockSuites: EvalSuite[] = [
    {
      id: "suite-1",
      name: "SDR Lead Qualification Suite",
      description: "Verifies lead qualification accuracy and grounding.",
      agent_id: "agent-1",
      config: {
        test_cases: [
          {
            id: "tc-1",
            name: "High intent lead",
            input: { lead: "Acme Corp" },
          },
        ],
      },
      created_at: "2026-03-30T10:00:00Z",
      updated_at: "2026-03-30T10:00:00Z",
    },
  ];

  const mockAgents: Agent[] = [
    {
      id: "agent-1",
      name: "SDR Inbound Lead Qualifier",
      description: "Qualifies inbound inquiries",
      stage: "staging",
      current_version: "1.0.0",
      version_count: 1,
      created_at: "2026-03-30T10:00:00Z",
      updated_at: "2026-03-30T10:00:00Z",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders suite cards and handles run suite trigger", async () => {
    const mockOnRunCompleted = vi.fn();
    const mockRunDetail: EvalRunDetail = {
      id: "run-123",
      suite_id: "suite-1",
      agent_id: "agent-1",
      agent_version_id: "v1.2.0",
      status: "running",
      trigger: "manual_ui",
      passed_cases: 0,
      failed_cases: 0,
      total_cases: 1,
      pass_rate: 0,
      duration_ms: 120,
      created_at: "2026-03-30T11:00:00Z",
      results: [],
    };

    vi.mocked(api.executeEvalSuite).mockResolvedValueOnce(mockRunDetail);

    render(
      <EvalSuiteRunner
        suites={mockSuites}
        agents={mockAgents}
        onRunCompleted={mockOnRunCompleted}
      />
    );

    expect(screen.getByText("SDR Lead Qualification Suite")).toBeDefined();
    expect(screen.getByText("SDR Inbound Lead Qualifier")).toBeDefined();

    // Click "Execute Suite"
    const runBtn = screen.getByText("Execute Suite");
    fireEvent.click(runBtn);

    // Modal opens
    expect(screen.getByText("Run Evaluation Suite")).toBeDefined();
    const confirmBtn = screen.getByText("Start Evaluation");
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.executeEvalSuite).toHaveBeenCalledWith("suite-1", undefined, "manual_ui");
      expect(mockOnRunCompleted).toHaveBeenCalledWith(mockRunDetail);
    });
  });
});

describe("EvalRunDetailView", () => {
  const mockResults: EvalResult[] = [
    {
      id: "res-1",
      eval_run_id: "run-100",
      case_id: "tc-1",
      case_name: "High Intent Enterprise",
      passed: true,
      score: 1.0,
      evaluator_name: "json_validator",
      evaluator_type: "json_schema",
      input_data: { lead: "Acme Corp" },
      actual_output: { qualified: true, score: 9.5 },
      latency_ms: 340,
      tokens_used: 420,
      created_at: "2026-03-30T11:00:00Z",
    },
    {
      id: "res-2",
      eval_run_id: "run-100",
      case_id: "tc-2",
      case_name: "Incomplete Contact Data",
      passed: false,
      score: 0.0,
      evaluator_name: "grounding_checker",
      evaluator_type: "grounding",
      input_data: { lead: "Unknown Inc" },
      actual_output: { error: "schema_mismatch" },
      failure_reason: "Missing required key 'qualification_score' in output schema.",
      latency_ms: 210,
      tokens_used: 310,
      created_at: "2026-03-30T11:00:00Z",
    },
  ];

  const mockRunDetail: EvalRunDetail = {
    id: "run-100",
    suite_id: "suite-1",
    agent_id: "agent-1",
    agent_version_id: "v1.2.0",
    status: "completed",
    trigger: "manual",
    passed_cases: 1,
    failed_cases: 1,
    total_cases: 2,
    pass_rate: 0.5,
    duration_ms: 550,
    created_at: "2026-03-30T11:00:00Z",
    completed_at: "2026-03-30T11:00:01Z",
    results: mockResults,
  };

  it("renders metric cards and allows filtering assertions", () => {
    render(<EvalRunDetailView run={mockRunDetail} />);

    // Metric cards
    expect(screen.getByText("50%")).toBeDefined();
    expect(screen.getByText("550 ms")).toBeDefined();
    expect(screen.getByText("All (2)")).toBeDefined();

    // Table rows
    expect(screen.getByText("High Intent Enterprise")).toBeDefined();
    expect(screen.getByText("Incomplete Contact Data")).toBeDefined();

    // Filter by "Failed"
    const failedFilterBtn = screen.getByText("Failed (1)");
    fireEvent.click(failedFilterBtn);

    // High Intent Enterprise should now be filtered out
    expect(screen.queryByText("High Intent Enterprise")).toBeNull();
    expect(screen.getByText("Incomplete Contact Data")).toBeDefined();
  });

  it("opens assertion inspector modal when Inspect is clicked", () => {
    render(<EvalRunDetailView run={mockRunDetail} />);

    const inspectButtons = screen.getAllByText("Inspect");
    expect(inspectButtons.length).toBeGreaterThan(0);
    const firstInspect = inspectButtons[1]; // inspect the failed one
    if (firstInspect) {
      fireEvent.click(firstInspect);
    }

    expect(screen.getAllByText("Incomplete Contact Data").length).toBeGreaterThan(1);
    expect(screen.getByText("Missing required key 'qualification_score' in output schema.")).toBeDefined();

    // Close modal
    const closeBtn = screen.getByText("Close Inspector");
    fireEvent.click(closeBtn);
    expect(screen.queryByText("Close Inspector")).toBeNull();
  });
});

describe("EvalRegressionView", () => {
  const mockRuns: EvalRun[] = [
    {
      id: "run-base",
      suite_id: "suite-1",
      agent_id: "agent-1",
      agent_version_id: "v1.0.0",
      status: "completed",
      trigger: "manual",
      passed_cases: 8,
      failed_cases: 2,
      total_cases: 10,
      pass_rate: 0.8,
      duration_ms: 1200,
      created_at: "2026-03-29T10:00:00Z",
    },
    {
      id: "run-candidate",
      suite_id: "suite-1",
      agent_id: "agent-1",
      agent_version_id: "v1.1.0",
      status: "completed",
      trigger: "manual",
      passed_cases: 10,
      failed_cases: 0,
      total_cases: 10,
      pass_rate: 1.0,
      duration_ms: 950,
      created_at: "2026-03-30T10:00:00Z",
    },
  ];

  const mockComparisonReport: EvalComparisonReport = {
    suite_id: "suite-1",
    base_run_id: "run-base",
    candidate_run_id: "run-candidate",
    base_pass_rate: 0.8,
    candidate_pass_rate: 1.0,
    pass_rate_delta: 0.2,
    status: "improved",
    total_cases_compared: 2,
    regressions_count: 0,
    improvements_count: 1,
    latency_delta_ms: -250,
    cases: [
      {
        case_id: "tc-edge-1",
        case_name: "Edge Case Incomplete",
        base_passed: false,
        candidate_passed: true,
        base_score: 0.0,
        candidate_score: 1.0,
        status: "improved",
      },
      {
        case_id: "tc-standard",
        case_name: "Standard Inbound",
        base_passed: true,
        candidate_passed: true,
        base_score: 1.0,
        candidate_score: 1.0,
        status: "unchanged",
      },
    ],
  };

  it("handles version comparison and renders regression diff cards", async () => {
    vi.mocked(api.compareEvalRuns).mockResolvedValueOnce(mockComparisonReport);

    render(<EvalRegressionView runs={mockRuns} />);

    // Select candidate and base
    const compareBtn = screen.getByText("Compare Versions");
    fireEvent.click(compareBtn);

    await waitFor(() => {
      expect(api.compareEvalRuns).toHaveBeenCalled();
      expect(screen.getByText("+20%")).toBeDefined();
      expect(screen.getByText("Version Verdict: improved")).toBeDefined();
      expect(screen.getByText("Edge Case Incomplete")).toBeDefined();
      expect(screen.getByText("Standard Inbound")).toBeDefined();
    });
  });
});

describe("ConfidenceSandbox", () => {
  const mockAgents: Agent[] = [
    {
      id: "agent-1",
      name: "SDR Agent",
      description: "Inbound SDR",
      stage: "staging",
      current_version: "1.0.0",
      version_count: 1,
      created_at: "2026-03-30T10:00:00Z",
      updated_at: "2026-03-30T10:00:00Z",
    },
  ];

  const mockOutcome: ReviewPriorityOutcome = {
    review_priority: "low",
    confidence_score: 0.94,
    rationale: "All structural schema and grounding checks succeeded with high margin.",
    signals: [
      {
        name: "json_schema_validation",
        weight: 0.25,
        score: 1.0,
        passed: true,
        details: "Valid JSON conforms exactly to schema specification.",
      },
      {
        name: "grounding_similarity",
        weight: 0.35,
        score: 0.92,
        passed: true,
        details: "Output claims are fully grounded in provided context.",
      },
    ],
  };

  it("evaluates confidence and renders signal breakdown", async () => {
    vi.mocked(api.evaluateConfidence).mockResolvedValueOnce(mockOutcome);

    render(<ConfidenceSandbox agents={mockAgents} />);

    expect(screen.getByText("Verifiable Confidence & Review-Priority Sandbox")).toBeDefined();

    const evalBtn = screen.getByText("Calculate Review Priority");
    fireEvent.click(evalBtn);

    await waitFor(() => {
      expect(api.evaluateConfidence).toHaveBeenCalled();
      expect(screen.getByText("94.0% Confidence")).toBeDefined();
      expect(screen.getByText("Low Priority")).toBeDefined();
      expect(screen.getByText("json schema validation")).toBeDefined();
      expect(screen.getByText("grounding similarity")).toBeDefined();
    });
  });
});
