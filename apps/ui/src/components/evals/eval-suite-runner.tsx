"use client";

/**
 * Eval Suite Runner Component.
 * Allows viewing registered evaluation suites and executing them against agent versions.
 * Follows GitHub Primer aesthetic with semantic design tokens.
 */

import React, { useState } from "react";
import {
  Play,
  FlaskConical,
  AlertCircle,
  FileCode,
  Loader2,
  Clock,
} from "lucide-react";
import type { Agent, EvalRunDetail, EvalSuite } from "@/lib/types";
import { executeEvalSuite } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";

interface EvalSuiteRunnerProps {
  suites: EvalSuite[];
  agents: Agent[];
  onRunCompleted: (run: EvalRunDetail) => void;
}

export function EvalSuiteRunner({
  suites,
  agents,
  onRunCompleted,
}: EvalSuiteRunnerProps) {
  const [selectedSuite, setSelectedSuite] = useState<EvalSuite | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const agentMap = new Map<string, Agent>(agents.map((a) => [a.id, a]));

  const handleStartRun = async (suite: EvalSuite) => {
    try {
      setIsRunning(true);
      setError(null);
      const res = await executeEvalSuite(
        suite.id,
        selectedVersionId || undefined,
        "manual_ui"
      );
      onRunCompleted(res);
      setSelectedSuite(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to execute eval suite");
    } finally {
      setIsRunning(false);
    }
  };

  if (!suites || suites.length === 0) {
    return (
      <EmptyState
        icon={FlaskConical}
        title="No Evaluation Suites Registered"
        description="Register an eval suite via CLI ('varistha eval run') or specify an eval suite path in your agent spec."
      />
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {suites.map((suite) => {
          const agent = agentMap.get(suite.agent_id);
          const config = suite.config as {
            test_cases?: Array<unknown>;
            evaluators?: Record<string, unknown>;
          };
          const testCaseCount = config?.test_cases?.length || 0;
          const evaluatorCount = config?.evaluators
            ? Object.keys(config.evaluators).length
            : 0;

          return (
            <div
              key={suite.id}
              className="flex flex-col justify-between p-5 rounded-xl border border-border bg-card hover:border-border/80 transition-all shadow-xs"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-foreground shrink-0">
                      <FlaskConical className="w-4 h-4 text-purple-500" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-foreground leading-tight">
                        {suite.name}
                      </h3>
                      <span className="text-xs text-muted-foreground font-mono">
                        {agent ? agent.name : suite.agent_id.slice(0, 8)}
                      </span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-muted text-muted-foreground border border-border">
                    {testCaseCount} {testCaseCount === 1 ? "case" : "cases"}
                  </span>
                </div>

                <p className="text-xs text-muted-foreground line-clamp-2 my-3">
                  {suite.description || "Continuous evaluation benchmark for agent capabilities."}
                </p>

                <div className="flex items-center gap-4 text-xs text-muted-foreground border-t border-border pt-3 mt-3">
                  <div className="flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5" />
                    <span>{evaluatorCount} evaluators</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(suite.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-2 border-t border-border flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setSelectedSuite(suite)}
                  className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Execute Suite</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Execute Run Modal */}
      {selectedSuite && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md p-6 rounded-2xl border border-border bg-card shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-5 h-5 text-purple-500" />
                <h3 className="text-base font-semibold text-foreground">
                  Run Evaluation Suite
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedSuite(null)}
                className="text-muted-foreground hover:text-foreground text-sm font-medium"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                  Target Suite
                </span>
                <div className="p-2.5 rounded-lg bg-muted border border-border font-medium text-foreground">
                  {selectedSuite.name}
                </div>
              </div>

              <div>
                <label
                  htmlFor="version-id-input"
                  className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1"
                >
                  Target Version UUID (Optional)
                </label>
                <input
                  id="version-id-input"
                  type="text"
                  placeholder="Leave empty for latest version snapshot"
                  value={selectedVersionId}
                  onChange={(e) => setSelectedVersionId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-hidden focus:ring-2 focus:ring-ring"
                />
              </div>

              <div className="p-3 rounded-lg bg-muted/50 border border-border text-xs text-muted-foreground space-y-1">
                <p>
                  • Evaluates all assertions configured in the suite.
                </p>
                <p>
                  • Records latency, token consumption, and per-assertion outcomes.
                </p>
                <p>
                  • Enforces promotion gates for prototype and staging promotions.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                disabled={isRunning}
                onClick={() => setSelectedSuite(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isRunning}
                onClick={() => handleStartRun(selectedSuite)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Executing Suite...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5" />
                    <span>Start Evaluation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
