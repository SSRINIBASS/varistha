"use client";

/**
 * Promote Agent Modal.
 * Evaluates verifiable programmatic promotion gates in real-time, displays
 * pass/fail checklist criteria, captures operator confirmations, and executes transitions.
 */

import React, { useEffect, useState } from "react";
import {
  X,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Loader2,
  Lock,
  ArrowRight,
} from "lucide-react";
import type { Agent, AgentStage, GateEvaluation } from "@/lib/types";
import { getGateEvaluation, promoteAgent, ApiError } from "@/lib/api";
import { StageBadge } from "./badges";

interface PromoteModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
  onPromoted?: () => void;
  onSuccess?: (agent: Agent) => void;
}

const STAGES: AgentStage[] = [
  "draft",
  "prototype",
  "staging",
  "production",
  "deprecated",
  "retired",
];

const CANONICAL_ORDER: Record<AgentStage, number> = {
  draft: 0,
  prototype: 1,
  staging: 2,
  production: 3,
  deprecated: 4,
  retired: 5,
};

function getNextStage(current: AgentStage): AgentStage {
  const currentIdx = CANONICAL_ORDER[current] ?? 0;
  if (currentIdx < STAGES.length - 1) {
    const next = STAGES[currentIdx + 1];
    if (next) return next;
  }
  return current;
}

export function PromoteModal({
  agent,
  isOpen,
  onClose,
  onPromoted,
  onSuccess,
}: PromoteModalProps) {
  const currentStage = agent.stage.toLowerCase() as AgentStage;
  const [targetStage, setTargetStage] = useState<AgentStage>(() =>
    getNextStage(currentStage)
  );
  const [promotedBy, setPromotedBy] = useState<string>("operator@varistha.local");
  const [reason, setReason] = useState<string>("");
  const [replacement, setReplacement] = useState<string>("");
  const [killSwitchVerified, setKillSwitchVerified] = useState<boolean>(false);
  const [secretsRevoked, setSecretsRevoked] = useState<boolean>(false);

  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<GateEvaluation | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isRollback =
    (CANONICAL_ORDER[targetStage] ?? 0) < (CANONICAL_ORDER[currentStage] ?? 0);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    getGateEvaluation(agent.id, targetStage, {
      replacement: replacement.trim() || undefined,
      kill_switch_verified: killSwitchVerified,
      secrets_revoked: secretsRevoked,
    })
      .then((res) => {
        if (active) {
          setEvaluation(res);
          setEvaluating(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setEvalError(
            err instanceof Error ? err.message : "Failed to evaluate promotion gates"
          );
          setEvaluation(null);
          setEvaluating(false);
        }
      });

    return () => {
      active = false;
    };
  }, [agent.id, targetStage, replacement, killSwitchVerified, secretsRevoked, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evaluation?.allowed && !isRollback) return;
    if (isRollback && !reason.trim()) {
      setSubmitError("A justification reason is mandatory for stage rollbacks.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await promoteAgent(agent.id, {
        to_stage: targetStage,
        promoted_by: promotedBy.trim(),
        reason: reason.trim() || undefined,
        replacement: replacement.trim() || undefined,
        kill_switch_verified: killSwitchVerified,
        secrets_revoked: secretsRevoked,
      });
      if (onSuccess) onSuccess(res.agent);
      if (onPromoted) onPromoted();
      onClose();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.details) {
        setSubmitError(err.message);
      } else {
        setSubmitError(
          err instanceof Error ? err.message : "Failed to execute promotion"
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
      <div className="gh-modal max-w-xl max-h-[90vh]">
        {/* Header */}
        <div className="gh-box-header px-6 py-3.5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary" />
            <div>
              <h2 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
                <span>Lifecycle Stage Transition</span>
                <span className="font-mono text-xs font-normal text-muted-foreground">
                  {agent.name}
                </span>
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="gh-btn-subtle p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Transition Visualizer */}
          <div className="flex items-center justify-between p-3 rounded-md border border-border bg-muted/40">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">Current:</span>
              <StageBadge stage={agent.stage} />
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">Target:</span>
              <StageBadge stage={targetStage} />
            </div>
          </div>

          {/* Target Stage Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Select Target Stage
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
              {STAGES.map((s) => {
                const isSelected = s === targetStage;
                const isCurrent = s === currentStage;
                return (
                  <button
                    key={s}
                    type="button"
                    disabled={isCurrent}
                    onClick={() => setTargetStage(s)}
                    className={`px-2 py-1.5 text-xs font-medium rounded-md border text-center capitalize transition-all cursor-pointer ${
                      isSelected
                        ? "bg-primary text-primary-foreground border-primary font-bold shadow-xs"
                        : isCurrent
                        ? "opacity-40 border-border bg-muted text-muted-foreground cursor-not-allowed"
                        : "border-border bg-card text-foreground hover:bg-muted"
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Rollback Alert */}
          {isRollback && (
            <div className="flex items-start gap-2.5 p-3 rounded-md border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 text-xs">
              <RotateCcw className="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <span className="font-semibold">Demotion / Rollback Notice:</span> Moving backward
                from {currentStage} to {targetStage} is permitted with a mandatory explanatory
                justification recorded in the audit log.
              </div>
            </div>
          )}

          {/* Gate Verification Checklist */}
          <div className="gh-box p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <span>Programmatic Gate Verification</span>
                {evaluating && <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />}
              </h3>
              {evaluation && (
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                    evaluation.allowed
                      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                      : "bg-destructive/15 text-destructive border border-destructive/30"
                  }`}
                >
                  {evaluation.allowed ? "All Gates Passed" : "Gates Unsatisfied"}
                </span>
              )}
            </div>

            {evalError && (
              <p className="text-xs text-destructive">{evalError}</p>
            )}

            {evaluation && evaluation.checks.length > 0 ? (
              <div className="space-y-1.5">
                {evaluation.checks.map((check) => (
                  <div
                    key={check.name}
                    className="flex items-start gap-2 text-xs p-2 rounded-md bg-muted/40 border border-border/50"
                  >
                    {check.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-destructive mt-0.5 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <span className="font-mono font-medium text-foreground text-xs">
                        {check.name}
                      </span>
                      <p className="text-muted-foreground text-[11px] mt-0.5">
                        {check.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : !evaluating ? (
              <p className="text-xs text-muted-foreground">No gates configured for this transition.</p>
            ) : null}
          </div>

          {/* Operator Affirmations & Options */}
          <div className="space-y-3">
            {targetStage === "production" && (
              <label className="flex items-start gap-2.5 p-2.5 rounded-md border border-border bg-muted/20 cursor-pointer hover:bg-muted/40 transition-colors">
                <input
                  type="checkbox"
                  checked={killSwitchVerified}
                  onChange={(e) => setKillSwitchVerified(e.target.checked)}
                  className="mt-0.5 rounded border-border text-primary focus:ring-primary"
                />
                <span className="text-xs text-foreground">
                  <span className="font-semibold">Verify Emergency Kill Switch:</span> I confirm
                  that the emergency stop mechanism and runtime budget limits have been tested and
                  verified.
                </span>
              </label>
            )}

            {targetStage === "deprecated" && (
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1">
                  Replacement Agent Slug (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. lead-researcher-v2"
                  value={replacement}
                  onChange={(e) => setReplacement(e.target.value)}
                  className="gh-input w-full font-mono text-xs"
                />
              </div>
            )}

            {targetStage === "retired" && (
              <label className="flex items-start gap-2.5 p-2.5 rounded-md border border-border bg-muted/20 cursor-pointer hover:bg-muted/40 transition-colors">
                <input
                  type="checkbox"
                  checked={secretsRevoked}
                  onChange={(e) => setSecretsRevoked(e.target.checked)}
                  className="mt-0.5 rounded border-border text-primary focus:ring-primary"
                />
                <span className="text-xs text-foreground">
                  <span className="font-semibold">Revoke Secrets & Credentials:</span> I confirm
                  that all API tokens, database keys, and integration credentials for this agent
                  have been revoked.
                </span>
              </label>
            )}

            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">
                Promoted By (Operator Email) <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                required
                value={promotedBy}
                onChange={(e) => setPromotedBy(e.target.value)}
                className="gh-input w-full"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">
                Reason / Migration Notes {isRollback && <span className="text-destructive">(Required for rollback)</span>}
              </label>
              <textarea
                rows={2}
                placeholder={isRollback ? "Required explanation for demoting this agent..." : "Optional rationale for the audit record..."}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="gh-input w-full resize-none font-sans"
              />
            </div>
          </div>

          {submitError && (
            <div className="flex items-center gap-2 p-2.5 rounded-md border border-destructive/30 bg-destructive/10 text-destructive text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{submitError}</span>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="gh-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || (!evaluation?.allowed && !isRollback) || (isRollback && !reason.trim())}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all shadow-xs cursor-pointer ${
                (!evaluation?.allowed && !isRollback) || (isRollback && !reason.trim())
                  ? "bg-muted text-muted-foreground cursor-not-allowed border border-border"
                  : isRollback
                  ? "gh-btn-danger"
                  : "gh-btn-primary"
              }`}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Promoting...</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Execute {isRollback ? "Rollback" : "Promotion"}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
