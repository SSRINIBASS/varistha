/**
 * Varistha Control Plane API Client.
 */

import type {
  AgentDetail,
  AgentListResponse,
  AgentVersion,
  AgentBudgetStatus,
  ApprovalItem,
  ApprovalsListResponse,
  ApprovalResolveRequest,
  ConfidenceEvaluationRequest,
  EvalComparisonReport,
  EvalRunDetail,
  EvalRunListResponse,
  EvalSuite,
  EvalSuiteListResponse,
  GateEvaluation,
  GlobalKillSwitchStatus,
  HealthStatus,
  PluginInfo,
  PluginListResponse,
  PolicyListResponse,
  PolicyTestResponse,
  PromoteAgentRequest,
  PromoteAgentResponse,
  ReviewPriorityOutcome,
  Run,
  RunListResponse,
  SpanListResponse,
  SpecDiff,
  StageTransition,
  TraceDetailResponse,
} from "./types";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...options.headers,
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
      let errorDetail: unknown = undefined;
      try {
        const body = await res.json();
        errorMsg = body.detail || body.message || errorMsg;
        errorDetail = body;
      } catch {
        // use fallback statusText
      }
      throw new ApiError(res.status, errorMsg, errorDetail);
    }
    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message =
      err instanceof Error ? err.message : "Failed to connect to API";
    throw new ApiError(0, message);
  }
}

export async function checkHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health");
}

export async function getAgents(
  limit = 50,
  offset = 0
): Promise<AgentListResponse> {
  return request<AgentListResponse>(
    `/api/v1/agents?limit=${limit}&offset=${offset}`
  );
}

export async function getAgent(idOrName: string): Promise<AgentDetail> {
  return request<AgentDetail>(`/api/v1/agents/${encodeURIComponent(idOrName)}`);
}

export async function getAgentVersions(
  idOrName: string
): Promise<AgentVersion[]> {
  const res = await request<AgentVersion[] | { items: AgentVersion[] }>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/versions`
  );
  if (Array.isArray(res)) {
    return res;
  }
  return res?.items || [];
}

export async function triggerRun(
  idOrName: string,
  inputData: Record<string, unknown> = {},
  triggerType = "manual"
): Promise<Run> {
  return request<Run>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/runs`,
    {
      method: "POST",
      body: JSON.stringify({ input: inputData, trigger_type: triggerType }),
    }
  );
}

export async function getRuns(params: {
  agent_id?: string | undefined;
  status?: string | undefined;
  limit?: number | undefined;
  offset?: number | undefined;
} = {}): Promise<RunListResponse> {
  const searchParams = new URLSearchParams();
  if (params.agent_id) searchParams.set("agent_id", params.agent_id);
  if (params.status) searchParams.set("status", params.status);
  searchParams.set("limit", String(params.limit ?? 50));
  searchParams.set("offset", String(params.offset ?? 0));

  return request<RunListResponse>(`/api/v1/runs?${searchParams.toString()}`);
}

export async function getAgentRuns(
  idOrName: string,
  limit = 50,
  offset = 0
): Promise<RunListResponse> {
  return request<RunListResponse>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/runs?limit=${limit}&offset=${offset}`
  );
}

export async function getRun(runId: string): Promise<Run> {
  return request<Run>(`/api/v1/runs/${encodeURIComponent(runId)}`);
}

export async function getRunSpans(runId: string): Promise<SpanListResponse> {
  return request<SpanListResponse>(
    `/api/v1/runs/${encodeURIComponent(runId)}/spans`
  );
}

export async function getTrace(traceId: string): Promise<TraceDetailResponse> {
  return request<TraceDetailResponse>(
    `/api/v1/traces/${encodeURIComponent(traceId)}`
  );
}

export async function getGateEvaluation(
  idOrName: string,
  targetStage: string,
  options?: {
    replacement?: string | null | undefined;
    kill_switch_verified?: boolean | null | undefined;
    secrets_revoked?: boolean | null | undefined;
  }
): Promise<GateEvaluation> {
  const params = new URLSearchParams();
  if (options?.replacement) params.set("replacement", options.replacement);
  if (options?.kill_switch_verified !== undefined)
    params.set("kill_switch_verified", String(options.kill_switch_verified));
  if (options?.secrets_revoked !== undefined)
    params.set("secrets_revoked", String(options.secrets_revoked));

  const query = params.toString() ? `?${params.toString()}` : "";
  return request<GateEvaluation>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/gates/${encodeURIComponent(targetStage)}${query}`
  );
}

export async function promoteAgent(
  idOrName: string,
  payload: PromoteAgentRequest
): Promise<PromoteAgentResponse> {
  return request<PromoteAgentResponse>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/promote`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function getStageHistory(
  idOrName: string
): Promise<StageTransition[]> {
  return request<StageTransition[]>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/history`
  );
}

export async function getVersionDiff(
  idOrName: string,
  v1: string,
  v2: string
): Promise<SpecDiff> {
  return request<SpecDiff>(
    `/api/v1/agents/${encodeURIComponent(idOrName)}/versions/${encodeURIComponent(v1)}/diff/${encodeURIComponent(v2)}`
  );
}

// --- Governance: Approvals, Budgets, Policies ---

export async function getApprovals(params?: {
  status?: string;
  agentId?: string;
  runId?: string;
  limit?: number;
  offset?: number;
}): Promise<ApprovalsListResponse> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.agentId) q.set("agent_id", params.agentId);
  if (params?.runId) q.set("run_id", params.runId);
  if (params?.limit !== undefined) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));

  const query = q.toString() ? `?${q.toString()}` : "";
  return request<ApprovalsListResponse>(`/api/v1/approvals${query}`);
}

export async function getApproval(id: string): Promise<ApprovalItem> {
  return request<ApprovalItem>(`/api/v1/approvals/${encodeURIComponent(id)}`);
}

export async function resolveApproval(
  id: string,
  payload: ApprovalResolveRequest
): Promise<ApprovalItem> {
  return request<ApprovalItem>(`/api/v1/approvals/${encodeURIComponent(id)}/resolve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getAgentBudget(idOrName: string): Promise<AgentBudgetStatus> {
  return request<AgentBudgetStatus>(`/api/v1/agents/${encodeURIComponent(idOrName)}/budget`);
}

export async function tripAgentKillSwitch(
  idOrName: string,
  reason?: string,
  operator?: string
): Promise<AgentBudgetStatus> {
  return request<AgentBudgetStatus>(`/api/v1/agents/${encodeURIComponent(idOrName)}/kill`, {
    method: "POST",
    body: JSON.stringify({ reason: reason || "Emergency stop", operator: operator || "operator" }),
  });
}

export async function resumeAgent(
  idOrName: string,
  operator?: string
): Promise<AgentBudgetStatus> {
  return request<AgentBudgetStatus>(`/api/v1/agents/${encodeURIComponent(idOrName)}/resume`, {
    method: "POST",
    body: JSON.stringify({ operator: operator || "operator" }),
  });
}

export async function getGlobalKillSwitch(): Promise<GlobalKillSwitchStatus> {
  return request<GlobalKillSwitchStatus>("/api/v1/system/kill-switch");
}

export async function setGlobalKillSwitch(
  enabled: boolean,
  reason?: string,
  operator?: string
): Promise<GlobalKillSwitchStatus> {
  return request<GlobalKillSwitchStatus>("/api/v1/system/kill-switch", {
    method: "POST",
    body: JSON.stringify({ enabled, reason: reason || null, operator: operator || "operator" }),
  });
}

export async function getPolicies(): Promise<PolicyListResponse> {
  return request<PolicyListResponse>("/api/v1/policies");
}

export async function testPolicy(
  policyName: string,
  payload: unknown,
  hook: string = "input"
): Promise<PolicyTestResponse> {
  return request<PolicyTestResponse>("/api/v1/policies/test", {
    method: "POST",
    body: JSON.stringify({ policy_name: policyName, payload, hook }),
  });
}

// --- Evals & Confidence API Methods ---

export async function getEvalSuites(agentId?: string): Promise<EvalSuiteListResponse> {
  const query = agentId ? `?agent_id=${encodeURIComponent(agentId)}` : "";
  return request<EvalSuiteListResponse>(`/api/v1/evals/suites${query}`);
}

export async function getEvalSuite(suiteId: string): Promise<EvalSuite> {
  return request<EvalSuite>(`/api/v1/evals/suites/${encodeURIComponent(suiteId)}`);
}

export async function createEvalSuite(payload: {
  name: string;
  agent_id: string;
  description?: string;
  config?: Record<string, unknown>;
}): Promise<EvalSuite> {
  return request<EvalSuite>("/api/v1/evals/suites", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function executeEvalSuite(
  suiteId: string,
  agentVersionId?: string,
  trigger: string = "manual"
): Promise<EvalRunDetail> {
  const query = new URLSearchParams({ trigger });
  if (agentVersionId) query.set("agent_version_id", agentVersionId);
  return request<EvalRunDetail>(
    `/api/v1/evals/suites/${encodeURIComponent(suiteId)}/execute?${query.toString()}`,
    { method: "POST" }
  );
}

export async function getEvalRuns(params?: {
  agent_id?: string;
  suite_id?: string;
  limit?: number;
  offset?: number;
}): Promise<EvalRunListResponse> {
  const query = new URLSearchParams();
  if (params?.agent_id) query.set("agent_id", params.agent_id);
  if (params?.suite_id) query.set("suite_id", params.suite_id);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const qs = query.toString() ? `?${query.toString()}` : "";
  return request<EvalRunListResponse>(`/api/v1/evals/runs${qs}`);
}

export async function getEvalRun(runId: string): Promise<EvalRunDetail> {
  return request<EvalRunDetail>(`/api/v1/evals/runs/${encodeURIComponent(runId)}`);
}

export async function compareEvalRuns(
  baseRunId: string,
  candidateRunId: string
): Promise<EvalComparisonReport> {
  const query = new URLSearchParams({
    base_run_id: baseRunId,
    candidate_run_id: candidateRunId,
  });
  return request<EvalComparisonReport>(`/api/v1/evals/compare?${query.toString()}`);
}

export async function evaluateConfidence(
  payload: ConfidenceEvaluationRequest
): Promise<ReviewPriorityOutcome> {
  return request<ReviewPriorityOutcome>("/api/v1/governance/confidence/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPlugins(): Promise<PluginListResponse> {
  return request<PluginListResponse>("/api/v1/plugins");
}

export async function getPlugin(name: string): Promise<PluginInfo> {
  return request<PluginInfo>(`/api/v1/plugins/${encodeURIComponent(name)}`);
}


