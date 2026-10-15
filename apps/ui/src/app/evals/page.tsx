"use client";

/**
 * Evals & Verifiable Confidence Hub.
 * Follows GitHub Primer UI/UX design:
 * - Subnav tabs for Suites, Run History, Regression Comparison, and Review Priority.
 * - Semantic tokens, card borders, light and dark theme compatibility.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  FlaskConical,
  Play,
  Activity,
  GitCompare,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
} from "lucide-react";
import {
  getAgents,
  getEvalSuites,
  getEvalRuns,
  getEvalRun,
} from "@/lib/api";
import type {
  Agent,
  EvalRun,
  EvalRunDetail,
  EvalSuite,
} from "@/lib/types";
import { EvalSuiteRunner } from "@/components/evals/eval-suite-runner";
import { EvalRunDetailView } from "@/components/evals/eval-run-detail";
import { EvalRegressionView } from "@/components/evals/eval-regression-view";
import { ConfidenceSandbox } from "@/components/evals/confidence-sandbox";
import { CardSkeleton } from "@/components/loading-skeleton";
import { ErrorAlert } from "@/components/error-alert";
import { EmptyState } from "@/components/empty-state";

type EvalsTab = "suites" | "runs" | "comparator" | "confidence";

export default function EvalsPage() {
  const [activeTab, setActiveTab] = useState<EvalsTab>("suites");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [suites, setSuites] = useState<EvalSuite[]>([]);
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [selectedRunDetail, setSelectedRunDetail] = useState<EvalRunDetail | null>(null);
  const [loadingRunDetail, setLoadingRunDetail] = useState<boolean>(false);

  const refreshData = useCallback(async () => {
    try {
      setError(null);
      const [agentsRes, suitesRes, runsRes] = await Promise.all([
        getAgents(100),
        getEvalSuites(),
        getEvalRuns({ limit: 50 }),
      ]);
      setAgents(agentsRes.items);
      setSuites(suitesRes.suites);
      setRuns(runsRes.runs);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to refresh evaluation data");
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    async function initialize() {
      try {
        setIsLoading(true);
        setError(null);

        const [agentsRes, suitesRes, runsRes] = await Promise.all([
          getAgents(100),
          getEvalSuites(),
          getEvalRuns({ limit: 50 }),
        ]);

        if (ignore) return;

        setAgents(agentsRes.items);
        setSuites(suitesRes.suites);
        setRuns(runsRes.runs);

        if (runsRes.runs.length > 0 && runsRes.runs[0]) {
          try {
            const detail = await getEvalRun(runsRes.runs[0].id);
            if (!ignore) {
              setSelectedRunDetail(detail);
            }
          } catch {
            // If first run detail fails, proceed without breaking
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load evaluation data");
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    initialize();

    return () => {
      ignore = true;
    };
  }, []);

  const handleSelectRun = async (runId: string) => {
    try {
      setLoadingRunDetail(true);
      const detail = await getEvalRun(runId);
      setSelectedRunDetail(detail);
      setActiveTab("runs");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load run details");
    } finally {
      setLoadingRunDetail(false);
    }
  };

  const handleRunCompleted = (runDetail: EvalRunDetail) => {
    setSelectedRunDetail(runDetail);
    setRuns((prev) => [runDetail, ...prev]);
    setActiveTab("runs");
  };

  // Compute summary stats
  const completedRuns = runs.filter((r) => r.status === "completed");
  const totalPassRate = completedRuns.reduce(
    (acc, r) => acc + (r.pass_rate || 0),
    0
  );
  const meanPassRate = completedRuns.length > 0
    ? Math.round((totalPassRate / completedRuns.length) * 100)
    : 0;

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/20">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">
              Evaluations & Verifiable Confidence
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Deterministic assertions, LLM-as-judge scoring, version regression comparisons, and promotion gate criteria.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => refreshData()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-border bg-card text-foreground hover:bg-muted transition-colors shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("suites")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Run Test Suite</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Registered Suites
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-foreground">
              {suites.length}
            </span>
            <span className="text-xs text-muted-foreground">across {agents.length} agents</span>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Completed Eval Runs
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-foreground">
              {completedRuns.length}
            </span>
            <span className="text-xs text-muted-foreground">({runs.length} total)</span>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Average Pass Rate
          </span>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold font-mono ${
                meanPassRate >= 80 ? "text-emerald-500" : "text-amber-500"
              }`}
            >
              {meanPassRate}%
            </span>
            <span className="text-xs text-muted-foreground">benchmark score</span>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-border bg-card shadow-xs">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
            Gate Readiness
          </span>
          <div className="flex items-center gap-2 mt-1">
            {meanPassRate >= 80 ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Gates Passing</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                <span>Below Threshold</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* UnderlineNav Tab Switcher */}
      <div className="border-b border-border flex items-center gap-6 text-sm">
        <button
          type="button"
          onClick={() => setActiveTab("suites")}
          className={`flex items-center gap-2 pb-3 font-medium border-b-2 transition-all ${
            activeTab === "suites"
              ? "border-foreground text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FlaskConical className="w-4 h-4" />
          <span>Suites & Runner</span>
          <span className="ml-1 px-1.5 py-0.2 rounded-full text-[11px] bg-muted text-muted-foreground font-mono">
            {suites.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("runs")}
          className={`flex items-center gap-2 pb-3 font-medium border-b-2 transition-all ${
            activeTab === "runs"
              ? "border-foreground text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Run History & Assertions</span>
          <span className="ml-1 px-1.5 py-0.2 rounded-full text-[11px] bg-muted text-muted-foreground font-mono">
            {runs.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("comparator")}
          className={`flex items-center gap-2 pb-3 font-medium border-b-2 transition-all ${
            activeTab === "comparator"
              ? "border-foreground text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <GitCompare className="w-4 h-4" />
          <span>Version Regression Comparator</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("confidence")}
          className={`flex items-center gap-2 pb-3 font-medium border-b-2 transition-all ${
            activeTab === "confidence"
              ? "border-foreground text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Review Priority Sandbox</span>
        </button>
      </div>

      {error && <ErrorAlert message={error} />}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : (
        <div>
          {/* Tab 1: Suites & Runner */}
          {activeTab === "suites" && (
            <EvalSuiteRunner
              suites={suites}
              agents={agents}
              onRunCompleted={handleRunCompleted}
            />
          )}

          {/* Tab 2: Run History & Assertions */}
          {activeTab === "runs" && (
            <div className="space-y-6">
              {runs.length === 0 ? (
                <EmptyState
                  icon={Activity}
                  title="No Evaluation Runs Yet"
                  description="Execute an evaluation suite from the Suites tab or via CLI to see assertion results."
                />
              ) : (
                <div className="space-y-6">
                  {/* Select Run Selector Bar */}
                  <div className="p-4 rounded-xl border border-border bg-card shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-xs font-semibold text-foreground">
                        Select Evaluation Run to Inspect:
                      </span>
                    </div>

                    <select
                      value={selectedRunDetail?.id || ""}
                      onChange={(e) => handleSelectRun(e.target.value)}
                      className="px-3 py-1.5 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-hidden focus:ring-2 focus:ring-ring max-w-md w-full"
                    >
                      {runs.map((r) => (
                        <option key={r.id} value={r.id}>
                          {new Date(r.created_at).toLocaleString()} — Pass Rate:{" "}
                          {r.pass_rate !== null && r.pass_rate !== undefined
                            ? `${Math.round(r.pass_rate * 100)}%`
                            : "N/A"}{" "}
                          ({r.passed_cases}/{r.total_cases} passed) — [{r.status}]
                        </option>
                      ))}
                    </select>
                  </div>

                  {loadingRunDetail ? (
                    <CardSkeleton />
                  ) : selectedRunDetail ? (
                    <EvalRunDetailView run={selectedRunDetail} />
                  ) : (
                    <div className="p-8 text-center text-muted-foreground text-sm">
                      Select an evaluation run to view its granular assertions.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Version Regression Comparator */}
          {activeTab === "comparator" && <EvalRegressionView runs={runs} />}

          {/* Tab 4: Review Priority / Confidence Sandbox */}
          {activeTab === "confidence" && <ConfidenceSandbox agents={agents} />}
        </div>
      )}
    </div>
  );
}
