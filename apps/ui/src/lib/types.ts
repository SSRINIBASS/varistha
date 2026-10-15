/**
 * Varistha Control Plane — Shared Domain Types for UI.
 */

export type AgentStage =
  | "draft"
  | "prototype"
  | "staging"
  | "production"
  | "deprecated"
  | "retired";

export type AutonomyLevel = "L0" | "L1" | "L2" | "L3";

export type RunStatus =
  | "running"
  | "completed"
  | "failed"
  | "waiting_approval";

export interface Agent {
  id: string;
  name: string;
  description?: string | null;
  owner?: string | null;
  stage: AgentStage;
  current_version: string;
  created_at: string;
  updated_at: string;
  version_count: number;
}

export interface AgentVersion {
  id: string;
  agent_id: string;
  version: string;
  spec: Record<string, unknown>;
  changelog?: string | null;
  created_at: string;
}

export interface AgentDetail extends Agent {
  spec: Record<string, unknown>;
  versions: AgentVersion[];
}

export interface AgentListResponse {
  items: Agent[];
  total: number;
  limit: number;
  offset: number;
}

export interface Run {
  id: string;
  agent_id: string;
  agent_version_id: string;
  status: RunStatus;
  trigger_type: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error?: string | null;
  started_at: string;
  completed_at?: string | null;
  cost_usd: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface RunListResponse {
  items: Run[];
  total: number;
  limit: number;
  offset: number;
}

export interface Span {
  id: string;
  trace_id: string;
  parent_span_id?: string | null;
  run_id?: string | null;
  name: string;
  kind: string;
  start_time: string;
  end_time?: string | null;
  duration_ms?: number | null;
  status_code: string;
  status_message?: string | null;
  attributes: Record<string, unknown>;
  events: Array<Record<string, unknown>>;
}

export interface SpanListResponse {
  items: Span[];
  total: number;
}

export interface TraceDetailResponse {
  trace_id: string;
  spans: Span[];
  total_spans: number;
  root_span?: Span | null;
  duration_ms?: number | null;
}

export interface HealthStatus {
  status: string;
  service: string;
}

export interface GateCheck {
  name: string;
  passed: boolean;
  message: string;
}

export interface GateEvaluation {
  allowed: boolean;
  from_stage: string;
  to_stage: string;
  is_rollback: boolean;
  checks: GateCheck[];
  error_message?: string | null;
}

export interface StageTransition {
  id: string;
  agent_id: string;
  from_stage: string;
  to_stage: string;
  promoted_by: string;
  reason?: string | null;
  gate_results: Array<Record<string, unknown>>;
  created_at: string;
}

export interface PromoteAgentRequest {
  to_stage: string;
  promoted_by: string;
  reason?: string | null | undefined;
  replacement?: string | null | undefined;
  kill_switch_verified?: boolean | null | undefined;
  secrets_revoked?: boolean | null | undefined;
}

export interface PromoteAgentResponse {
  agent: AgentDetail;
  transition: StageTransition;
  evaluation: GateEvaluation;
}

export interface DiffEntry {
  field: string;
  change_type: string;
  old_value?: unknown;
  new_value?: unknown;
  is_breaking: boolean;
  breaking_reason?: string | null;
  description: string;
}

export interface SpecDiff {
  from_version?: string | null;
  to_version?: string | null;
  has_changes: boolean;
  has_breaking_changes: boolean;
  summary: Record<string, number>;
  entries: DiffEntry[];
  breaking_entries: DiffEntry[];
}

// --- Governance: Approvals, Budgets, Policies ---

export type ApprovalStatus = "pending" | "approved" | "rejected" | "edited";

export interface ApprovalItem {
  id: string;
  run_id: string;
  agent_id: string;
  agent_name?: string;
  status: ApprovalStatus;
  action_type: string;
  tool_name?: string | null;
  description: string;
  proposed_payload: Record<string, unknown>;
  approved_payload?: Record<string, unknown> | null;
  diff?: Record<string, unknown> | null;
  reviewer?: string | null;
  review_notes?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface ApprovalsListResponse {
  items: ApprovalItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApprovalResolveRequest {
  action: "approve" | "reject" | "edit";
  modified_payload?: Record<string, unknown>;
  reviewer?: string;
  notes?: string;
}

export interface AgentBudgetStatus {
  agent_id: string;
  agent_name: string;
  daily_spend_usd: number;
  daily_budget_usd: number | null;
  remaining_daily_budget_usd: number | null;
  max_usd_per_run: number | null;
  is_active: boolean;
  kill_switch_tripped: boolean;
  kill_switch_reason?: string | null;
  kill_switch_tripped_at?: string | null;
}

export interface GlobalKillSwitchStatus {
  enabled: boolean;
  reason?: string | null;
  tripped_at?: string | null;
  operator?: string | null;
}

export interface PolicyInfo {
  name: string;
  description: string;
  supported_hooks: string[];
}

export interface PolicyListResponse {
  policies: PolicyInfo[];
  total: number;
}

export interface PolicyTestRequest {
  policy_name: string;
  payload: unknown;
  hook?: string;
}

export interface PolicyTestResponse {
  policy_name: string;
  passed: boolean;
  action: string;
  modified_data?: unknown;
  violations: string[];
  metadata: Record<string, unknown>;
}

// --- Evals & Confidence Domain Models ---

export interface EvalSuite {
  id: string;
  name: string;
  agent_id: string;
  description?: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EvalSuiteListResponse {
  suites: EvalSuite[];
  total: number;
}

export interface EvalRun {
  id: string;
  suite_id: string;
  agent_id: string;
  agent_version_id?: string | null;
  status: "pending" | "running" | "completed" | "failed";
  trigger: string;
  pass_rate?: number | null;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  duration_ms?: number | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface EvalRunListResponse {
  runs: EvalRun[];
  total: number;
}

export interface EvalResult {
  id: string;
  eval_run_id: string;
  case_id: string;
  case_name: string;
  input_data: Record<string, unknown>;
  expected_output?: unknown;
  actual_output?: unknown;
  passed: boolean;
  score: number;
  evaluator_name: string;
  evaluator_type: string;
  failure_reason?: string | null;
  latency_ms?: number | null;
  tokens_used?: number | null;
  created_at: string;
}

export interface EvalRunDetail extends EvalRun {
  results: EvalResult[];
}

export interface TestCaseComparison {
  case_id: string;
  case_name: string;
  base_passed?: boolean | null;
  base_score?: number | null;
  candidate_passed?: boolean | null;
  candidate_score?: number | null;
  status: "regressed" | "improved" | "unchanged" | "added" | "removed";
}

export interface EvalComparisonReport {
  suite_id: string;
  base_run_id: string;
  candidate_run_id: string;
  base_version_id?: string | null;
  candidate_version_id?: string | null;
  base_pass_rate: number;
  candidate_pass_rate: number;
  pass_rate_delta: number;
  status: "improved" | "regressed" | "unchanged";
  total_cases_compared: number;
  regressions_count: number;
  improvements_count: number;
  latency_delta_ms: number;
  cases: TestCaseComparison[];
}

export interface ConfidenceSignal {
  name: string;
  weight: number;
  score: number;
  passed: boolean;
  details: string;
}

export interface ReviewPriorityOutcome {
  confidence_score: number;
  review_priority: "low" | "medium" | "high" | "critical";
  signals: ConfidenceSignal[];
  rationale: string;
}

export interface ConfidenceEvaluationRequest {
  agent_id: string;
  version_id?: string | null;
  output: unknown;
  input_context?: unknown;
  schema_def?: Record<string, unknown> | null;
}

// --- Plugin Ecosystem Domain Models ---

export type PluginRiskLevel = "low" | "medium" | "high";
export type PluginTransport = "in-process" | "mcp-stdio" | "mcp-sse";

export interface PluginInfo {
  name: string;
  version: string;
  description: string;
  transport: PluginTransport;
  risk: PluginRiskLevel;
  scopes: string[];
  requires_approval: boolean;
  untrusted_output: boolean;
  config_schema?: Record<string, unknown> | null;
  tools: string[];
}

export interface PluginListResponse {
  plugins: PluginInfo[];
  total: number;
}


