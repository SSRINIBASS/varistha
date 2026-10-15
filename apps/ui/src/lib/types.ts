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

