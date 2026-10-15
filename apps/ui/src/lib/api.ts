/**
 * Varistha Control Plane API Client.
 */

import type {
  AgentDetail,
  AgentListResponse,
  AgentVersion,
  GateEvaluation,
  HealthStatus,
  PromoteAgentRequest,
  PromoteAgentResponse,
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

