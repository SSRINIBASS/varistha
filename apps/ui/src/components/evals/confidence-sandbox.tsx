"use client";

/**
 * Verifiable Review-Priority & Confidence Engine Sandbox Component.
 * Derives uncalibrated LLM confidence from verifiable signals:
 * schema validation, grounding citations, offline eval benchmarks, and approval history.
 * Follows GitHub Primer aesthetic with semantic design tokens.
 */

import React, { useState } from "react";
import {
  ShieldCheck,
  AlertCircle,
  Cpu,
  FileCheck,
  History,
  Link as LinkIcon,
  Loader2,
  Sparkles,
} from "lucide-react";
import type { Agent, ReviewPriorityOutcome } from "@/lib/types";
import { evaluateConfidence } from "@/lib/api";
import { ReviewPriorityBadge } from "@/components/badges";

interface ConfidenceSandboxProps {
  agents: Agent[];
}

export function ConfidenceSandbox({ agents }: ConfidenceSandboxProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>(
    agents[0]?.id ?? ""
  );
  const [outputPayload, setOutputPayload] = useState<string>(
    JSON.stringify(
      {
        lead_name: "Acme Corp",
        qualification_score: 9.2,
        rationale: "High intent demonstrated through multiple inbound visits.",
      },
      null,
      2
    )
  );
  const [inputContext, setInputContext] = useState<string>(
    "Acme Corp visited pricing page 3 times, requested demo, and matches B2B ICP."
  );
  const [schemaDef, setSchemaDef] = useState<string>(
    JSON.stringify(
      {
        type: "object",
        required: ["lead_name", "qualification_score"],
        properties: {
          lead_name: { type: "string" },
          qualification_score: { type: "number" },
        },
      },
      null,
      2
    )
  );

  const [outcome, setOutcome] = useState<ReviewPriorityOutcome | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    if (!selectedAgentId) {
      setError("Please select a target agent.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      let parsedOutput: unknown = outputPayload;
      try {
        parsedOutput = JSON.parse(outputPayload);
      } catch {
        // Leave as string if not valid JSON
      }

      let parsedSchema: Record<string, unknown> | null = null;
      if (schemaDef.trim()) {
        try {
          parsedSchema = JSON.parse(schemaDef);
        } catch {
          throw new Error("Expected Schema must be a valid JSON Schema object.");
        }
      }

      const res = await evaluateConfidence({
        agent_id: selectedAgentId,
        output: parsedOutput,
        input_context: inputContext.trim() || undefined,
        schema_def: parsedSchema,
      });

      setOutcome(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to evaluate confidence signals");
    } finally {
      setIsLoading(false);
    }
  };

  const getSignalIcon = (name: string) => {
    switch (name) {
      case "schema_validation":
        return FileCheck;
      case "grounding_citation":
        return LinkIcon;
      case "eval_benchmark":
        return Cpu;
      case "approval_history":
        return History;
      default:
        return Sparkles;
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration & Inputs Card */}
      <div className="p-5 rounded-xl border border-border bg-card shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <ShieldCheck className="w-5 h-5 text-foreground" />
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              Verifiable Confidence & Review-Priority Sandbox
            </h3>
            <p className="text-xs text-muted-foreground">
              Evaluate candidate agent output across multi-source verifiable signals rather than trusting uncalibrated model self-reports.
            </p>
          </div>
        </div>

        <div className="space-y-4 text-xs">
          <div>
            <label
              htmlFor="agent-target-select"
              className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1"
            >
              Target Agent
            </label>
            <select
              id="agent-target-select"
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full max-w-sm px-3 py-2 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-hidden focus:ring-2 focus:ring-ring"
            >
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.stage})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Candidate Output */}
            <div>
              <label
                htmlFor="candidate-output-input"
                className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1"
              >
                Candidate Agent Output (JSON or Text)
              </label>
              <textarea
                id="candidate-output-input"
                rows={6}
                value={outputPayload}
                onChange={(e) => setOutputPayload(e.target.value)}
                className="w-full p-3 rounded-lg bg-background border border-border font-mono text-[11px] text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Input Context for Grounding */}
            <div>
              <label
                htmlFor="input-context-input"
                className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1"
              >
                Input Context / Grounding Source
              </label>
              <textarea
                id="input-context-input"
                rows={6}
                value={inputContext}
                onChange={(e) => setInputContext(e.target.value)}
                className="w-full p-3 rounded-lg bg-background border border-border font-mono text-[11px] text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>

          {/* Optional JSON Schema */}
          <div>
            <label
              htmlFor="schema-def-input"
              className="font-semibold text-muted-foreground uppercase tracking-wider block mb-1"
            >
              Expected JSON Schema (Optional)
            </label>
            <textarea
              id="schema-def-input"
              rows={4}
              value={schemaDef}
              onChange={(e) => setSchemaDef(e.target.value)}
              className="w-full p-3 rounded-lg bg-background border border-border font-mono text-[11px] text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        <div className="flex items-center justify-end pt-2 border-t border-border">
          <button
            type="button"
            disabled={isLoading || !selectedAgentId}
            onClick={handleEvaluate}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Evaluating Signals...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Calculate Review Priority</span>
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

      {/* Outcome Dashboard */}
      {outcome && (
        <div className="space-y-6 animate-in fade-in">
          {/* Main Review-Priority Card */}
          <div className="p-6 rounded-2xl border border-border bg-card shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Derived Review Priority
              </span>
              <div className="flex items-center gap-3">
                <ReviewPriorityBadge priority={outcome.review_priority} />
                <span className="text-2xl font-bold font-mono text-foreground">
                  {(outcome.confidence_score * 100).toFixed(1)}% Confidence
                </span>
              </div>
              <p className="text-xs text-muted-foreground max-w-xl">
                {outcome.rationale}
              </p>
            </div>

            <div className="w-full md:w-56 space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground font-mono">
                <span>Confidence Gauge</span>
                <span>{(outcome.confidence_score * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-2.5 rounded-full transition-all duration-500 ${
                    outcome.confidence_score >= 0.8
                      ? "bg-emerald-500"
                      : outcome.confidence_score >= 0.6
                      ? "bg-blue-500"
                      : outcome.confidence_score >= 0.4
                      ? "bg-amber-500"
                      : "bg-rose-500"
                  }`}
                  style={{ width: `${Math.min(Math.max(outcome.confidence_score * 100, 0), 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* 4 Signals Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {outcome.signals.map((sig) => {
              const Icon = getSignalIcon(sig.name);
              const scorePct = Math.round(sig.score * 100);

              return (
                <div
                  key={sig.name}
                  className="p-4 rounded-xl border border-border bg-card shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center text-foreground">
                        <Icon className="w-4 h-4 text-purple-500" />
                      </div>
                      <span
                        className={`text-xs font-semibold font-mono px-2 py-0.5 rounded-full ${
                          sig.passed
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {sig.passed ? "PASSED" : "FAILED"}
                      </span>
                    </div>

                    <h4 className="text-xs font-semibold text-foreground capitalize mt-2">
                      {sig.name.replace(/_/g, " ")}
                    </h4>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      Weight: {(sig.weight * 100).toFixed(0)}%
                    </span>

                    <p className="text-xs text-muted-foreground my-2 line-clamp-3">
                      {sig.details}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-border mt-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-muted-foreground">Score</span>
                      <span className="font-semibold text-foreground">{scorePct}%</span>
                    </div>
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
