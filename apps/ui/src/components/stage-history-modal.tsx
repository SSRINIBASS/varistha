"use client";

/**
 * Stage History Modal.
 * Displays the immutable audit trail of lifecycle stage transitions for an agent,
 * including operator identity, timestamps, justifications, and gate outcomes.
 */

import React, { useEffect, useState } from "react";
import {
  X,
  History,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Loader2,
  Calendar,
  User,
  ArrowRight,
} from "lucide-react";
import type { Agent, StageTransition } from "@/lib/types";
import { getStageHistory } from "@/lib/api";
import { StageBadge } from "./badges";

interface StageHistoryModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
}

export function StageHistoryModal({
  agent,
  isOpen,
  onClose,
}: StageHistoryModalProps) {
  const [history, setHistory] = useState<StageTransition[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    getStageHistory(agent.id)
      .then((data) => {
        if (active) {
          setHistory(data);
          if (data.length > 0 && data[0]) {
            setExpandedId(data[0].id);
          }
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Failed to load stage audit history"
          );
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [isOpen, agent.id]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-xl border border-border bg-card shadow-2xl text-card-foreground overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-tight text-foreground">
                Lifecycle Audit Log
              </h2>
              <p className="text-xs text-muted-foreground">
                Immutable transition history for <span className="font-mono text-foreground font-semibold">{agent.name}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <p className="text-xs">Loading immutable audit log...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg border border-destructive/30 bg-destructive/10 text-destructive text-xs">
              {error}
            </div>
          ) : history.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground space-y-2">
              <History className="w-8 h-8 mx-auto opacity-40" />
              <p className="text-sm font-medium text-foreground">No stage transitions recorded yet</p>
              <p className="text-xs max-w-xs mx-auto">
                Promote this agent to start accumulating verified audit records.
              </p>
            </div>
          ) : (
            <div className="relative border-l border-border/80 ml-3 space-y-6">
              {history.map((record) => {
                const isExpanded = expandedId === record.id;
                const formattedDate = new Date(record.created_at).toLocaleString();
                const gateList = record.gate_results || [];

                return (
                  <div key={record.id} className="relative pl-6">
                    {/* Timeline Node */}
                    <div className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full border-2 border-background bg-primary shadow-xs" />

                    <div className="rounded-lg border border-border bg-muted/20 p-4 space-y-3">
                      {/* Top Bar: Stages and Date */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <StageBadge stage={record.from_stage} />
                          <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />
                          <StageBadge stage={record.to_stage} />
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            {formattedDate}
                          </span>
                        </div>
                      </div>

                      {/* Operator & Reason */}
                      <div className="text-xs text-muted-foreground flex flex-wrap items-center gap-x-4 gap-y-1">
                        <span className="inline-flex items-center gap-1 text-foreground">
                          <User className="w-3.5 h-3.5 text-muted-foreground" />
                          <span className="font-semibold">Operator:</span> {record.promoted_by}
                        </span>
                        {record.reason && (
                          <div className="w-full mt-1.5 p-2 rounded bg-background border border-border/60 text-foreground text-xs italic">
                            &quot;{record.reason}&quot;
                          </div>
                        )}
                      </div>

                      {/* Expandable Gate Results */}
                      {gateList.length > 0 && (
                        <div className="pt-2 border-t border-border/50">
                          <button
                            type="button"
                            onClick={() => setExpandedId(isExpanded ? null : record.id)}
                            className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
                          >
                            {isExpanded ? (
                              <ChevronDown className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronRight className="w-3.5 h-3.5" />
                            )}
                            <span>Gate Check Results ({gateList.length})</span>
                          </button>

                          {isExpanded && (
                            <div className="mt-2.5 space-y-1.5">
                              {gateList.map((g, idx) => {
                                const passed = Boolean(g.passed);
                                const name = String(g.name || `check-${idx}`);
                                const msg = String(g.message || "");

                                return (
                                  <div
                                    key={idx}
                                    className="flex items-start gap-2 text-xs p-1.5 rounded bg-background/80 border border-border/40"
                                  >
                                    {passed ? (
                                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                                    ) : (
                                      <XCircle className="w-3.5 h-3.5 text-destructive mt-0.5 shrink-0" />
                                    )}
                                    <div className="flex-1">
                                      <span className="font-mono font-medium text-foreground">
                                        {name}
                                      </span>
                                      {msg && (
                                        <p className="text-[11px] text-muted-foreground">
                                          {msg}
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-3 border-t border-border bg-muted/20">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-background hover:bg-muted text-foreground transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
