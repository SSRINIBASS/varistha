"use client";

/**
 * Run Detail & OpenTelemetry Trace View.
 * Displays execution metadata, cost/token metrics, inputs/outputs, and the custom Waterfall timeline.
 */

import React, { useEffect, useState, use, Suspense } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Clock,
  Coins,
  Cpu,
  Layers,
  RefreshCw,
  AlertCircle,
  Terminal,
  Code2,
} from "lucide-react";
import { getRun, getRunSpans } from "@/lib/api";
import type { Run, Span } from "@/lib/types";
import { StatusBadge } from "@/components/badges";
import { TraceWaterfall } from "@/components/trace-waterfall";
import { WaterfallSkeleton } from "@/components/loading-skeleton";
import { ErrorAlert } from "@/components/error-alert";

interface RunDetailPageProps {
  params: Promise<{ id: string }>;
}

function RunDetailInner({ params }: RunDetailPageProps) {
  const resolvedParams = use(params);
  const runId = resolvedParams.id;

  const [run, setRun] = useState<Run | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRunData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [runData, spansData] = await Promise.all([
        getRun(runId),
        getRunSpans(runId).catch(() => ({ items: [], total: 0 })),
      ]);
      setRun(runData);
      setSpans(spansData.items || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load run details"
      );
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      getRun(runId),
      getRunSpans(runId).catch(() => ({ items: [], total: 0 })),
    ])
      .then(([runData, spansData]) => {
        if (isMounted) {
          setRun(runData);
          setSpans(spansData.items || []);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Failed to load run details"
          );
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [runId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-36 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-card border border-border/60 rounded-xl animate-pulse" />
          ))}
        </div>
        <WaterfallSkeleton bars={5} />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="space-y-4">
        <Link
          href="/runs"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Runs</span>
        </Link>
        <ErrorAlert
          title="Could not load run execution"
          message={error || "Run not found"}
          onRetry={fetchRunData}
        />
      </div>
    );
  }

  // Calculate duration
  let durationStr = "N/A";
  if (run.started_at && run.completed_at) {
    const ms = new Date(run.completed_at).getTime() - new Date(run.started_at).getTime();
    durationStr = ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms}ms`;
  }

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <div>
        <Link
          href="/runs"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Runs</span>
        </Link>
      </div>

      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground font-mono">
              Run {run.id.slice(0, 8)}...
            </h1>
            <StatusBadge status={run.status} />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Agent ID: <span className="font-mono text-foreground">{run.agent_id}</span> | Trigger: <span className="capitalize">{run.trigger_type}</span>
          </p>
        </div>

        <button
          type="button"
          onClick={fetchRunData}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-border bg-card text-foreground hover:bg-muted transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Error Callout if Run Failed */}
      {run.error && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-500" />
          <div className="text-xs space-y-1">
            <div className="font-semibold text-rose-600 dark:text-rose-400">Execution Error</div>
            <div className="font-mono break-all">{run.error}</div>
          </div>
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/80 bg-card shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-1">
            <Clock className="w-4 h-4 text-primary" />
            <span>Duration</span>
          </div>
          <div className="text-lg font-bold font-mono text-foreground">{durationStr}</div>
        </div>

        <div className="p-4 rounded-xl border border-border/80 bg-card shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-1">
            <Cpu className="w-4 h-4 text-sky-500" />
            <span>Total Tokens</span>
          </div>
          <div className="text-lg font-bold font-mono text-foreground">
            {run.total_tokens ? run.total_tokens.toLocaleString() : "0"}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/80 bg-card shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-1">
            <Coins className="w-4 h-4 text-emerald-500" />
            <span>Cost (USD)</span>
          </div>
          <div className="text-lg font-bold font-mono text-foreground">
            ${Number(run.cost_usd || 0).toFixed(4)}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border/80 bg-card shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-1">
            <Layers className="w-4 h-4 text-indigo-500" />
            <span>Telemetry Spans</span>
          </div>
          <div className="text-lg font-bold font-mono text-foreground">
            {spans.length}
          </div>
        </div>
      </div>

      {/* OpenTelemetry Waterfall Timeline */}
      <div className="space-y-3">
        <h2 className="text-base font-bold tracking-tight text-foreground flex items-center gap-2">
          <Layers className="w-4 h-4 text-primary" />
          <span>OpenTelemetry Trace Waterfall</span>
        </h2>
        <TraceWaterfall spans={spans} />
      </div>

      {/* Inputs and Outputs Inspection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Input Card */}
        <div className="p-4 rounded-xl border border-border/80 bg-card space-y-2 shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Terminal className="w-3.5 h-3.5" />
            <span>Run Input Payload</span>
          </div>
          <pre className="p-3 rounded-lg bg-muted/40 font-mono text-xs overflow-x-auto text-foreground max-h-60">
            {JSON.stringify(run.input || {}, null, 2)}
          </pre>
        </div>

        {/* Output Card */}
        <div className="p-4 rounded-xl border border-border/80 bg-card space-y-2 shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Code2 className="w-3.5 h-3.5" />
            <span>Run Output Result</span>
          </div>
          <pre className="p-3 rounded-lg bg-muted/40 font-mono text-xs overflow-x-auto text-foreground max-h-60">
            {JSON.stringify(run.output || {}, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

export default function RunDetailPage(props: RunDetailPageProps) {
  return (
    <Suspense fallback={<WaterfallSkeleton bars={5} />}>
      <RunDetailInner {...props} />
    </Suspense>
  );
}

