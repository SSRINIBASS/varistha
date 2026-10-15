"use client";

/**
 * Eval Run Detail Component.
 * Displays granular per-test-case assertions, scoring, latency, token usage, and failure explanations.
 * Follows GitHub Primer aesthetic with semantic design tokens.
 */

import React, { useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Clock,
  Search,
  Check,
  X,
} from "lucide-react";
import type { EvalResult, EvalRunDetail } from "@/lib/types";

interface EvalRunDetailViewProps {
  run: EvalRunDetail;
  onBack?: () => void;
}

export function EvalRunDetailView({ run, onBack }: EvalRunDetailViewProps) {
  const [filter, setFilter] = useState<"all" | "passed" | "failed">("all");
  const [search, setSearch] = useState<string>("");
  const [inspectedCase, setInspectedCase] = useState<EvalResult | null>(null);

  const results = run.results || [];
  const filteredResults = results.filter((r) => {
    if (filter === "passed" && !r.passed) return false;
    if (filter === "failed" && r.passed) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        r.case_id.toLowerCase().includes(q) ||
        r.case_name.toLowerCase().includes(q) ||
        r.evaluator_name.toLowerCase().includes(q) ||
        r.evaluator_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const passRate = run.pass_rate !== null && run.pass_rate !== undefined
    ? Math.round(run.pass_rate * 100)
    : 0;

  return (
    <div className="space-y-6">
      {onBack && (
        <div>
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Suite Runs</span>
          </button>
        </div>
      )}

      {/* Top Banner / Metrics Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pass Rate Metric */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Pass Rate
          </span>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold font-mono ${
                passRate >= 80 ? "text-emerald-500" : "text-rose-500"
              }`}
            >
              {passRate}%
            </span>
            <span className="text-xs text-muted-foreground">
              ({run.passed_cases}/{run.total_cases} passed)
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className={`h-1.5 rounded-full ${
                passRate >= 80 ? "bg-emerald-500" : "bg-rose-500"
              }`}
              style={{ width: `${Math.min(Math.max(passRate, 0), 100)}%` }}
            />
          </div>
        </div>

        {/* Total Assertions */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Assertions
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-foreground">
              {run.total_cases}
            </span>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
              <span className="text-emerald-500 font-medium">✓ {run.passed_cases}</span>
              <span>•</span>
              <span className="text-rose-500 font-medium">✗ {run.failed_cases}</span>
            </div>
          </div>
          <span className="text-xs text-muted-foreground mt-3 block">
            Target Version: {run.agent_version_id ? run.agent_version_id.slice(0, 8) : "Latest"}
          </span>
        </div>

        {/* Latency / Execution Time */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Duration
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-foreground">
              {run.duration_ms !== null && run.duration_ms !== undefined
                ? `${run.duration_ms} ms`
                : "—"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-3">
            <Clock className="w-3.5 h-3.5" />
            <span>Trigger: {run.trigger}</span>
          </div>
        </div>

        {/* Execution Status */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Run Status
          </span>
          <div className="flex items-center gap-2 mt-1">
            {run.status === "completed" ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Completed</span>
              </span>
            ) : run.status === "failed" ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/30">
                <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                <span>Failed</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/30">
                <Clock className="w-3.5 h-3.5 text-blue-500 animate-spin" />
                <span>{run.status}</span>
              </span>
            )}
          </div>
          <span className="text-[11px] font-mono text-muted-foreground mt-3 block truncate">
            ID: {run.id}
          </span>
        </div>
      </div>

      {/* Test Cases Table Filter & Controls */}
      <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1 bg-muted p-1 rounded-lg border border-border">
            <button
              type="button"
              onClick={() => setFilter("all")}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                filter === "all"
                  ? "bg-card text-foreground shadow-xs font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All ({results.length})
            </button>
            <button
              type="button"
              onClick={() => setFilter("passed")}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                filter === "passed"
                  ? "bg-card text-emerald-600 dark:text-emerald-400 shadow-xs font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Passed ({run.passed_cases})
            </button>
            <button
              type="button"
              onClick={() => setFilter("failed")}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                filter === "failed"
                  ? "bg-card text-rose-600 dark:text-rose-400 shadow-xs font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Failed ({run.failed_cases})
            </button>
          </div>

          <div className="relative max-w-xs w-full">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search assertions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-hidden focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        {/* Assertions Table */}
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/60 text-muted-foreground font-semibold border-b border-border">
              <tr>
                <th className="py-2.5 px-4 w-12">Result</th>
                <th className="py-2.5 px-4">Test Case ID</th>
                <th className="py-2.5 px-4">Scenario / Name</th>
                <th className="py-2.5 px-4">Evaluator</th>
                <th className="py-2.5 px-4 text-right">Score</th>
                <th className="py-2.5 px-4 text-right">Latency</th>
                <th className="py-2.5 px-4 text-right">Tokens</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredResults.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-muted-foreground">
                    No assertion results match your search or filter.
                  </td>
                </tr>
              ) : (
                filteredResults.map((r) => (
                  <tr
                    key={r.id}
                    className="hover:bg-muted/40 transition-colors cursor-pointer"
                    onClick={() => setInspectedCase(r)}
                  >
                    <td className="py-2.5 px-4">
                      {r.passed ? (
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </span>
                      ) : (
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-rose-500/15 text-rose-600 dark:text-rose-400">
                          <X className="w-3 h-3 stroke-[3]" />
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-mono font-medium text-foreground">
                      {r.case_id}
                    </td>
                    <td className="py-2.5 px-4 text-foreground font-medium max-w-xs truncate">
                      {r.case_name}
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-muted text-muted-foreground border border-border">
                        {r.evaluator_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono">
                      <span
                        className={
                          r.score >= 0.8
                            ? "text-emerald-600 dark:text-emerald-400 font-semibold"
                            : r.score > 0
                            ? "text-amber-600 dark:text-amber-400 font-semibold"
                            : "text-rose-600 dark:text-rose-400 font-semibold"
                        }
                      >
                        {r.score.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-muted-foreground">
                      {r.latency_ms !== null && r.latency_ms !== undefined
                        ? `${r.latency_ms}ms`
                        : "—"}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-muted-foreground">
                      {r.tokens_used !== null && r.tokens_used !== undefined
                        ? r.tokens_used
                        : "—"}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectedCase(r);
                        }}
                        className="text-xs text-foreground font-medium hover:underline"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Case Details Modal / Inspector */}
      {inspectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 rounded-2xl border border-border bg-card shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-border pb-3">
              <div>
                <div className="flex items-center gap-2">
                  {inspectedCase.passed ? (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Passed</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/30">
                      <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                      <span>Failed</span>
                    </span>
                  )}
                  <h3 className="text-base font-semibold text-foreground">
                    {inspectedCase.case_name}
                  </h3>
                </div>
                <span className="text-xs font-mono text-muted-foreground mt-1 block">
                  Case ID: {inspectedCase.case_id} • Evaluator: {inspectedCase.evaluator_name} ({inspectedCase.evaluator_type})
                </span>
              </div>
              <button
                type="button"
                onClick={() => setInspectedCase(null)}
                className="text-muted-foreground hover:text-foreground text-sm font-medium"
              >
                ✕
              </button>
            </div>

            {inspectedCase.failure_reason && (
              <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-300 text-xs">
                <span className="font-semibold block mb-1">Failure Reason:</span>
                <span className="font-mono whitespace-pre-wrap">{inspectedCase.failure_reason}</span>
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <span className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                  Input Context / Test Case Payload
                </span>
                <pre className="p-3 rounded-lg bg-muted border border-border font-mono text-[11px] overflow-x-auto text-foreground">
                  {JSON.stringify(inspectedCase.input_data, null, 2)}
                </pre>
              </div>

              {inspectedCase.expected_output !== undefined && (
                <div>
                  <span className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                    Expected Output
                  </span>
                  <pre className="p-3 rounded-lg bg-muted border border-border font-mono text-[11px] overflow-x-auto text-foreground">
                    {typeof inspectedCase.expected_output === "object"
                      ? JSON.stringify(inspectedCase.expected_output, null, 2)
                      : String(inspectedCase.expected_output)}
                  </pre>
                </div>
              )}

              <div>
                <span className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                  Actual Agent Output
                </span>
                <pre className="p-3 rounded-lg bg-muted border border-border font-mono text-[11px] overflow-x-auto text-foreground">
                  {typeof inspectedCase.actual_output === "object"
                    ? JSON.stringify(inspectedCase.actual_output, null, 2)
                    : String(inspectedCase.actual_output || "No output recorded")}
                </pre>
              </div>
            </div>

            <div className="flex items-center justify-end pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setInspectedCase(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition-opacity"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
