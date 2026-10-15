"use client";

/**
 * Execution Runs Page.
 * Styled with authentic GitHub Actions Workflow Runs UI/UX:
 * - GitHub Box pattern with header counters and status filters
 * - Step icons with pulsing live states
 * - Detailed duration, token counts, and cost telemetry
 */

import React, { useEffect, useState, Suspense, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Activity,
  ArrowRight,
  RefreshCw,
  Search,
  CheckCircle2,
  Clock,
  Radio,
  AlertCircle,
  FileCode,
} from "lucide-react";
import { getRuns } from "@/lib/api";
import type { Run } from "@/lib/types";
import { StatusBadge } from "@/components/badges";
import { TableSkeleton } from "@/components/loading-skeleton";
import { EmptyState } from "@/components/empty-state";
import { ErrorAlert } from "@/components/error-alert";

function RunsContent() {
  const searchParams = useSearchParams();
  const agentFilter = searchParams.get("agent_id") || undefined;

  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchRunsList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusParam = selectedStatus !== "all" ? selectedStatus : undefined;
      const res = await getRuns({
        agent_id: agentFilter,
        status: statusParam,
      });
      setRuns(res.items || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load runs from API"
      );
    } finally {
      setLoading(false);
    }
  }, [agentFilter, selectedStatus]);

  useEffect(() => {
    let isMounted = true;
    const statusParam = selectedStatus !== "all" ? selectedStatus : undefined;
    getRuns({
      agent_id: agentFilter,
      status: statusParam,
    })
      .then((res) => {
        if (isMounted) {
          setRuns(res.items || []);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Failed to load runs from API"
          );
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [agentFilter, selectedStatus]);

  const filteredRuns = runs.filter((r) => {
    if (!searchQuery) return true;
    return (
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.trigger_type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const statuses = [
    { id: "all", label: "All Runs" },
    { id: "completed", label: "Completed" },
    { id: "running", label: "In Progress" },
    { id: "failed", label: "Failed" },
    { id: "waiting_approval", label: "Approval Required" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              <span>Execution Runs</span>
            </h1>
            <span className="gh-counter">{filteredRuns.length}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {agentFilter
              ? `Filtered by agent ID: ${agentFilter}`
              : "Live telemetry, OpenTelemetry spans, and audit logs for AI employee runs."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {agentFilter && (
            <Link
              href="/runs"
              className="gh-btn-secondary"
            >
              Clear Agent Filter
            </Link>
          )}
          <button
            type="button"
            onClick={fetchRunsList}
            disabled={loading}
            className="gh-btn-secondary"
            title="Refresh runs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar (GitHub Actions style) */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Filter by run ID or trigger..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-md border border-border bg-card text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-ring"
          />
        </div>

        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {statuses.map((st) => (
            <button
              key={st.id}
              type="button"
              onClick={() => setSelectedStatus(st.id)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                selectedStatus === st.id
                  ? "bg-secondary text-secondary-foreground font-semibold shadow-2xs border border-border"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <TableSkeleton rows={6} columns={7} />
      ) : error ? (
        <ErrorAlert
          title="Could not connect to Varistha API"
          message={error}
          onRetry={fetchRunsList}
        />
      ) : filteredRuns.length === 0 ? (
        <EmptyState
          title="No Execution Runs Found"
          description={
            agentFilter || selectedStatus !== "all"
              ? "No runs match the specified filter criteria."
              : "No execution runs recorded yet. Trigger a run from the Agents page or run 'varistha run <name>'."
          }
          icon={Activity}
          action={{
            label: "Go to Agents",
            href: "/agents",
          }}
        />
      ) : (
        /* GitHub Actions Style Box */
        <div className="gh-box w-full shadow-2xs">
          <div className="gh-box-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-foreground text-xs">
                {filteredRuns.length} Total Runs
              </span>
            </div>
            <div className="text-[11px] text-muted-foreground font-mono">
              OpenTelemetry Instrumented
            </div>
          </div>

          <div className="divide-y divide-border/60">
            {filteredRuns.map((run) => {
              const isSuccess = run.status === "completed";
              const isRunning = run.status === "running";
              const isFailed = run.status === "failed";

              return (
                <div
                  key={run.id}
                  className="p-3.5 hover:bg-muted/30 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    {/* Status Icon */}
                    <div className="mt-0.5 shrink-0">
                      {isSuccess ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : isRunning ? (
                        <Radio className="w-4 h-4 text-blue-500 animate-pulse" />
                      ) : isFailed ? (
                        <AlertCircle className="w-4 h-4 text-rose-500" />
                      ) : (
                        <Clock className="w-4 h-4 text-amber-500" />
                      )}
                    </div>

                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link
                          href={`/runs/${run.id}`}
                          className="font-semibold text-foreground hover:text-accent-foreground hover:underline transition-colors font-mono"
                        >
                          run-{run.id.slice(0, 8)}
                        </Link>
                        <StatusBadge status={run.status} />
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-muted text-muted-foreground border border-border">
                          {run.trigger_type}
                        </span>
                      </div>

                      <div className="text-[11px] text-muted-foreground flex items-center gap-3 flex-wrap">
                        <span>
                          Started {new Date(run.started_at || run.created_at).toLocaleString()}
                        </span>
                        <span>•</span>
                        <span className="font-mono">
                          {run.total_tokens ? run.total_tokens.toLocaleString() : "0"} tokens
                        </span>
                        <span>•</span>
                        <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                          ${Number(run.cost_usd || 0).toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right side: View Trace Button */}
                  <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                    <Link
                      href={`/runs/${run.id}`}
                      className="gh-btn-secondary"
                    >
                      <FileCode className="w-3.5 h-3.5 text-muted-foreground" />
                      <span>View Trace</span>
                      <ArrowRight className="w-3 h-3 text-muted-foreground" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function RunsPage() {
  return (
    <Suspense fallback={<TableSkeleton rows={6} columns={7} />}>
      <RunsContent />
    </Suspense>
  );
}
