"use client";

/**
 * Execution Runs Page.
 * Lists all historical and live agent execution runs across the control plane.
 */

import React, { useEffect, useState, Suspense, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Activity,
  ArrowRight,
  RefreshCw,
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

  const statuses = ["all", "completed", "running", "failed", "waiting_approval"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Activity className="w-6 h-6 text-primary" />
            <span>Execution Runs</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {agentFilter
              ? `Filtered by agent ID: ${agentFilter}`
              : "All operational agent execution runs and traces."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {agentFilter && (
            <Link
              href="/runs"
              className="px-3 py-2 rounded-lg text-xs font-medium border border-border bg-card text-foreground hover:bg-muted transition-colors"
            >
              Clear Agent Filter
            </Link>
          )}
          <button
            type="button"
            onClick={fetchRunsList}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-border bg-card text-foreground hover:bg-muted transition-colors cursor-pointer"
            title="Refresh runs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-border/60">
        {statuses.map((st) => (
          <button
            key={st}
            type="button"
            onClick={() => setSelectedStatus(st)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors cursor-pointer ${
              selectedStatus === st
                ? "bg-secondary text-secondary-foreground font-semibold shadow-xs"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            {st.replace("_", " ")}
          </button>
        ))}
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
      ) : runs.length === 0 ? (
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
        <div className="border border-border/80 rounded-xl bg-card overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border/80 bg-muted/40 font-medium text-muted-foreground">
                  <th className="py-3 px-4">Run ID</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Trigger</th>
                  <th className="py-3 px-4">Tokens</th>
                  <th className="py-3 px-4">Cost (USD)</th>
                  <th className="py-3 px-4">Started At</th>
                  <th className="py-3 px-4 text-right">Trace View</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    className="hover:bg-muted/30 transition-colors group"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-foreground">
                      <Link
                        href={`/runs/${run.id}`}
                        className="hover:underline flex items-center gap-1.5"
                      >
                        <span>{run.id.slice(0, 8)}...</span>
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="py-3 px-4 font-mono text-muted-foreground capitalize">
                      {run.trigger_type}
                    </td>
                    <td className="py-3 px-4 font-mono text-muted-foreground">
                      {run.total_tokens ? run.total_tokens.toLocaleString() : "0"}
                    </td>
                    <td className="py-3 px-4 font-mono text-muted-foreground">
                      ${Number(run.cost_usd || 0).toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">
                      {new Date(run.started_at || run.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/runs/${run.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                      >
                        <span>View Trace</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
