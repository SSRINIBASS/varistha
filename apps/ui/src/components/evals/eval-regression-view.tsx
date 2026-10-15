"use client";

/**
 * Version-over-Version Evaluation Regression Comparator Component.
 * Detects regressions, improvements, pass rate delta, and execution latency delta.
 * Follows GitHub Primer aesthetic with semantic design tokens.
 */

import React, { useState } from "react";
import {
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Minus,
  AlertCircle,
  GitCompare,
  Loader2,
} from "lucide-react";
import type { EvalComparisonReport, EvalRun } from "@/lib/types";
import { compareEvalRuns } from "@/lib/api";
import { RegressionStatusBadge } from "@/components/badges";
import { EmptyState } from "@/components/empty-state";

interface EvalRegressionViewProps {
  runs: EvalRun[];
}

export function EvalRegressionView({ runs }: EvalRegressionViewProps) {
  const completedRuns = runs.filter((r) => r.status === "completed");

  const [baseRunId, setBaseRunId] = useState<string>(
    completedRuns.length > 1
      ? (completedRuns[1]?.id ?? "")
      : (completedRuns[0]?.id ?? "")
  );
  const [candidateRunId, setCandidateRunId] = useState<string>(
    completedRuns[0]?.id ?? ""
  );
  const [report, setReport] = useState<EvalComparisonReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!baseRunId || !candidateRunId) {
      setError("Please select both a Base Run and a Candidate Run to compare.");
      return;
    }
    if (baseRunId === candidateRunId) {
      setError("Base Run and Candidate Run must be different evaluation runs.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const res = await compareEvalRuns(baseRunId, candidateRunId);
      setReport(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to compare evaluation runs");
      setReport(null);
    } finally {
      setIsLoading(false);
    }
  };

  if (completedRuns.length < 2) {
    return (
      <EmptyState
        icon={GitCompare}
        title="Insufficient Evaluation Runs"
        description="At least two completed evaluation runs are required to perform version-over-version regression comparison."
      />
    );
  }

  const formatDelta = (delta: number) => {
    const pct = Math.round(delta * 100);
    if (pct > 0) return `+${pct}%`;
    return `${pct}%`;
  };

  return (
    <div className="space-y-6">
      {/* Comparator Selection Form */}
      <div className="p-5 rounded-xl border border-border bg-card shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <GitCompare className="w-5 h-5 text-foreground" />
          <h3 className="text-sm font-semibold text-foreground">
            Version-over-Version Regression Comparator
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
          {/* Base Run Selector */}
          <div className="lg:col-span-2 space-y-1">
            <label
              htmlFor="base-run-select"
              className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block"
            >
              Base Run (Reference Version)
            </label>
            <select
              id="base-run-select"
              value={baseRunId}
              onChange={(e) => setBaseRunId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-hidden focus:ring-2 focus:ring-ring"
            >
              <option value="">Select Base Run...</option>
              {completedRuns.map((r) => (
                <option key={r.id} value={r.id}>
                  {new Date(r.created_at).toLocaleDateString()} — Pass Rate:{" "}
                  {r.pass_rate !== null && r.pass_rate !== undefined ? `${Math.round(r.pass_rate * 100)}%` : "N/A"}{" "}
                  ({r.agent_version_id ? r.agent_version_id.slice(0, 8) : "Latest"})
                </option>
              ))}
            </select>
          </div>

          <div className="hidden lg:flex items-center justify-center pb-2">
            <ArrowRight className="w-4 h-4 text-muted-foreground" />
          </div>

          {/* Candidate Run Selector */}
          <div className="lg:col-span-2 space-y-1">
            <label
              htmlFor="candidate-run-select"
              className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block"
            >
              Candidate Run (New Version)
            </label>
            <select
              id="candidate-run-select"
              value={candidateRunId}
              onChange={(e) => setCandidateRunId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-hidden focus:ring-2 focus:ring-ring"
            >
              <option value="">Select Candidate Run...</option>
              {completedRuns.map((r) => (
                <option key={r.id} value={r.id}>
                  {new Date(r.created_at).toLocaleDateString()} — Pass Rate:{" "}
                  {r.pass_rate !== null && r.pass_rate !== undefined ? `${Math.round(r.pass_rate * 100)}%` : "N/A"}{" "}
                  ({r.agent_version_id ? r.agent_version_id.slice(0, 8) : "Latest"})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center justify-end pt-2">
          <button
            type="button"
            disabled={isLoading || !baseRunId || !candidateRunId}
            onClick={handleCompare}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Comparing Versions...</span>
              </>
            ) : (
              <>
                <GitCompare className="w-3.5 h-3.5" />
                <span>Compare Versions</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Comparison Report Overview */}
      {report && (
        <div className="space-y-6 animate-in fade-in">
          {/* Net Verdict Banner */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${
              report.status === "improved"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-200"
                : report.status === "regressed"
                ? "bg-rose-500/10 border-rose-500/30 text-rose-800 dark:text-rose-200"
                : "bg-muted/60 border-border text-foreground"
            }`}
          >
            <div className="flex items-center gap-3">
              {report.status === "improved" ? (
                <div className="w-9 h-9 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                  <TrendingUp className="w-5 h-5" />
                </div>
              ) : report.status === "regressed" ? (
                <div className="w-9 h-9 rounded-full bg-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400">
                  <TrendingDown className="w-5 h-5" />
                </div>
              ) : (
                <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                  <Minus className="w-5 h-5" />
                </div>
              )}
              <div>
                <h4 className="text-sm font-semibold capitalize">
                  Version Verdict: {report.status}
                </h4>
                <p className="text-xs opacity-80 mt-0.5">
                  {report.status === "improved"
                    ? "Candidate version demonstrates positive progression across test suites."
                    : report.status === "regressed"
                    ? "Regression detected! Assertions that previously passed are now failing in candidate."
                    : "No net change in assertion pass rate between these two evaluation runs."}
                </p>
              </div>
            </div>

            <RegressionStatusBadge status={report.status} />
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                Pass Rate Delta
              </span>
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-2xl font-bold font-mono ${
                    report.pass_rate_delta > 0
                      ? "text-emerald-500"
                      : report.pass_rate_delta < 0
                      ? "text-rose-500"
                      : "text-foreground"
                  }`}
                >
                  {formatDelta(report.pass_rate_delta)}
                </span>
                <span className="text-xs text-muted-foreground font-mono">
                  ({Math.round(report.base_pass_rate * 100)}% →{" "}
                  {Math.round(report.candidate_pass_rate * 100)}%)
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                Regressions
              </span>
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-2xl font-bold font-mono ${
                    report.regressions_count > 0 ? "text-rose-500" : "text-foreground"
                  }`}
                >
                  {report.regressions_count}
                </span>
                <span className="text-xs text-muted-foreground">regressed cases</span>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                Improvements
              </span>
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-2xl font-bold font-mono ${
                    report.improvements_count > 0 ? "text-emerald-500" : "text-foreground"
                  }`}
                >
                  {report.improvements_count}
                </span>
                <span className="text-xs text-muted-foreground">improved cases</span>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                Latency Delta
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-foreground">
                  {report.latency_delta_ms > 0
                    ? `+${report.latency_delta_ms} ms`
                    : `${report.latency_delta_ms} ms`}
                </span>
              </div>
            </div>
          </div>

          {/* Granular Test Cases Comparison Table */}
          <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-3">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Comparative Test Case Assertions ({report.cases.length})
            </h4>

            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/60 text-muted-foreground font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Case ID</th>
                    <th className="py-2.5 px-4">Scenario / Name</th>
                    <th className="py-2.5 px-4 text-center">Base Result</th>
                    <th className="py-2.5 px-4 text-center">Candidate Result</th>
                    <th className="py-2.5 px-4 text-right">Base Score</th>
                    <th className="py-2.5 px-4 text-right">Candidate Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {report.cases.map((c) => (
                    <tr
                      key={c.case_id}
                      className={
                        c.status === "regressed"
                          ? "bg-rose-500/5 hover:bg-rose-500/10"
                          : c.status === "improved"
                          ? "bg-emerald-500/5 hover:bg-emerald-500/10"
                          : "hover:bg-muted/40"
                      }
                    >
                      <td className="py-2.5 px-4">
                        <RegressionStatusBadge status={c.status} />
                      </td>
                      <td className="py-2.5 px-4 font-mono font-medium text-foreground">
                        {c.case_id}
                      </td>
                      <td className="py-2.5 px-4 text-foreground font-medium max-w-xs truncate">
                        {c.case_name}
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono">
                        {c.base_passed === null || c.base_passed === undefined ? (
                          <span className="text-muted-foreground">—</span>
                        ) : c.base_passed ? (
                          <span className="text-emerald-500 font-semibold">PASS</span>
                        ) : (
                          <span className="text-rose-500 font-semibold">FAIL</span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono">
                        {c.candidate_passed === null || c.candidate_passed === undefined ? (
                          <span className="text-muted-foreground">—</span>
                        ) : c.candidate_passed ? (
                          <span className="text-emerald-500 font-semibold">PASS</span>
                        ) : (
                          <span className="text-rose-500 font-semibold">FAIL</span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-muted-foreground">
                        {c.base_score !== null && c.base_score !== undefined
                          ? c.base_score.toFixed(2)
                          : "—"}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono">
                        <span
                          className={
                            c.candidate_score !== null && c.candidate_score !== undefined
                              ? c.candidate_score >= (c.base_score || 0)
                                ? "text-emerald-600 dark:text-emerald-400 font-semibold"
                                : "text-rose-600 dark:text-rose-400 font-semibold"
                              : "text-muted-foreground"
                          }
                        >
                          {c.candidate_score !== null && c.candidate_score !== undefined
                            ? c.candidate_score.toFixed(2)
                            : "—"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
