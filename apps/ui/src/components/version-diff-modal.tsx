"use client";

/**
 * Version Diff Modal.
 * Side-by-side spec diff viewer highlighting field-level deltas and breaking changes.
 * Follows docs/SPEC.md § 3.2, § 4.4, § 5 design system rules.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  X,
  GitCompare,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ArrowRight,
  ShieldAlert,
  FileCode,
} from "lucide-react";
import type { Agent, AgentVersion, SpecDiff, DiffEntry } from "@/lib/types";
import { getAgentVersions, getVersionDiff } from "@/lib/api";

interface VersionDiffModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
  initialV1?: string;
  initialV2?: string;
}

export function VersionDiffModal({
  agent,
  isOpen,
  onClose,
  initialV1,
  initialV2,
}: VersionDiffModalProps) {
  const [versions, setVersions] = useState<AgentVersion[]>([]);
  const [v1, setV1] = useState<string>("");
  const [v2, setV2] = useState<string>("");
  const [diff, setDiff] = useState<SpecDiff | null>(null);
  const [loadingVersions, setLoadingVersions] = useState<boolean>(true);
  const [loadingDiff, setLoadingDiff] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    getAgentVersions(agent.id)
      .then((vers) => {
        if (!active) return;
        setVersions(vers);
        if (vers.length >= 2 && vers[0] && vers[1]) {
          setV1(initialV1 || vers[1].version);
          setV2(initialV2 || vers[0].version);
        } else if (vers.length === 1 && vers[0]) {
          setV1(vers[0].version);
          setV2(vers[0].version);
        }
        setLoadingVersions(false);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(
          err instanceof Error ? err.message : "Failed to load agent versions"
        );
        setLoadingVersions(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, agent.id, initialV1, initialV2]);

  const fetchDiff = useCallback(async (baseV: string, targetV: string) => {
    if (baseV === targetV) {
      setDiff({
        from_version: baseV,
        to_version: targetV,
        has_changes: false,
        has_breaking_changes: false,
        summary: { added: 0, removed: 0, modified: 0, breaking: 0 },
        entries: [],
        breaking_entries: [],
      });
      return;
    }
    setLoadingDiff(true);
    setError(null);
    try {
      const result = await getVersionDiff(agent.id, baseV, targetV);
      setDiff(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to compute version spec diff"
      );
      setDiff(null);
    } finally {
      setLoadingDiff(false);
    }
  }, [agent.id]);

  useEffect(() => {
    if (!isOpen || !v1 || !v2) return;
    if (v1 === v2) {
      queueMicrotask(() => {
        setDiff({
          from_version: v1,
          to_version: v2,
          has_changes: false,
          has_breaking_changes: false,
          summary: { added: 0, removed: 0, modified: 0, breaking: 0 },
          entries: [],
          breaking_entries: [],
        });
      });
      return;
    }

    let active = true;
    getVersionDiff(agent.id, v1, v2)
      .then((result) => {
        if (active) {
          setDiff(result);
          setLoadingDiff(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Failed to compute version spec diff"
          );
          setDiff(null);
          setLoadingDiff(false);
        }
      });

    return () => {
      active = false;
    };
  }, [isOpen, agent.id, v1, v2]);

  if (!isOpen) return null;

  const renderValue = (val: unknown) => {
    if (val === undefined || val === null) {
      return <span className="text-muted-foreground italic">none</span>;
    }
    if (typeof val === "object") {
      return (
        <pre className="font-mono text-xs bg-muted/60 p-1.5 rounded max-h-32 overflow-auto text-foreground whitespace-pre-wrap">
          {JSON.stringify(val, null, 2)}
        </pre>
      );
    }
    return <span className="font-mono text-xs text-foreground">{String(val)}</span>;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
      <div className="gh-modal max-w-5xl max-h-[90vh]">
        {/* Header */}
        <div className="gh-box-header px-6 py-3.5">
          <div className="flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-primary" />
            <div>
              <h2 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
                <span>Spec Diff Viewer</span>
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

        {/* Version Pickers Bar (GitHub Branch/Commit Compare Style) */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border bg-muted/40 px-6 py-2.5">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground">base:</span>
              <select
                aria-label="Base Version (v1)"
                value={v1}
                onChange={(e) => setV1(e.target.value)}
                disabled={loadingVersions}
                className="gh-input h-7 py-0.5 text-xs font-mono font-medium"
              >
                {versions.map((ver) => (
                  <option key={ver.version} value={ver.version}>
                    v{ver.version}
                  </option>
                ))}
              </select>
            </div>

            <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground">compare:</span>
              <select
                aria-label="Target Version (v2)"
                value={v2}
                onChange={(e) => setV2(e.target.value)}
                disabled={loadingVersions}
                className="gh-input h-7 py-0.5 text-xs font-mono font-medium"
              >
                {versions.map((ver) => (
                  <option key={ver.version} value={ver.version}>
                    v{ver.version}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Change Summary Badges */}
          {diff && !loadingDiff && (
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                +{diff.summary?.added ?? 0}
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                -{diff.summary?.removed ?? 0}
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                ~{diff.summary?.modified ?? 0}
              </span>
              {diff.has_breaking_changes && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-red-500/10 text-destructive border border-destructive/30 font-semibold">
                  <AlertTriangle className="w-3 h-3" />
                  {diff.summary?.breaking ?? 0} breaking
                </span>
              )}
            </div>
          )}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive flex items-center justify-between">
              <span>{error}</span>
              <button
                type="button"
                onClick={() => fetchDiff(v1, v2)}
                className="underline hover:opacity-80 font-medium"
              >
                Retry
              </button>
            </div>
          )}

          {loadingVersions || loadingDiff ? (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <p className="text-xs">Computing version differences and breaking changes...</p>
            </div>
          ) : !diff ? null : (
            <>
              {/* Breaking changes alert banner */}
              {diff.has_breaking_changes && (
                <div className="rounded-xl border border-red-200 dark:border-red-900/60 bg-red-50 dark:bg-red-950/40 p-4 space-y-3">
                  <div className="flex items-center gap-2.5 text-red-800 dark:text-red-300 font-semibold text-sm">
                    <ShieldAlert className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0" />
                    <span>Breaking Changes Detected in Target Version</span>
                  </div>
                  <p className="text-xs text-red-700 dark:text-red-300/90 leading-relaxed">
                    This version transition introduces breaking modifications according to Varistha spec
                    safety policies. Ensure that downstream integrations and autonomous operations are reviewed.
                  </p>
                  <div className="space-y-1.5 pt-1">
                    {diff.breaking_entries.map((b: DiffEntry, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-xs bg-card/60 rounded-md p-2 border border-red-200 dark:border-red-900/40"
                      >
                        <span className="font-mono font-semibold text-red-700 dark:text-red-300 shrink-0">
                          {b.field}:
                        </span>
                        <span className="text-foreground">{b.breaking_reason || b.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No changes empty state */}
              {!diff.has_changes ? (
                <div className="py-12 flex flex-col items-center justify-center text-center gap-3 border border-dashed border-border rounded-xl bg-muted/20">
                  <div className="p-3 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">
                    Identical Versions
                  </h3>
                  <p className="text-xs text-muted-foreground max-w-sm">
                    No spec differences were detected between v{v1} and v{v2}.
                  </p>
                </div>
              ) : (
                /* Field Diff Table */
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                      <FileCode className="w-3.5 h-3.5" />
                      Field-Level Changes ({diff.entries.length})
                    </h3>
                  </div>

                  <div className="gh-box">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-border bg-muted/60 font-semibold text-muted-foreground">
                          <th className="py-2 px-3">Field</th>
                          <th className="py-2 px-3">Change</th>
                          <th className="py-2 px-3">Old Value (v{v1})</th>
                          <th className="py-2 px-3">New Value (v{v2})</th>
                          <th className="py-2 px-3">Impact</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {diff.entries.map((entry: DiffEntry, i: number) => {
                          const isBreaking = entry.is_breaking;
                          const diffClass =
                            entry.change_type === "added"
                              ? "gh-diff-add"
                              : entry.change_type === "removed"
                              ? "gh-diff-delete"
                              : "";
                          return (
                            <tr
                              key={i}
                              className={`transition-colors hover:bg-muted/30 ${diffClass} ${
                                isBreaking ? "ring-1 ring-destructive/40" : ""
                              }`}
                            >
                              <td className="py-2.5 px-3 font-mono font-medium text-foreground align-top">
                                {entry.field}
                              </td>
                              <td className="py-2.5 px-3 align-top">
                                <span
                                  className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold ${
                                    entry.change_type === "added"
                                      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                                      : entry.change_type === "removed"
                                      ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30"
                                      : "bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30"
                                  }`}
                                >
                                  {entry.change_type}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 align-top max-w-[200px]">
                                {renderValue(entry.old_value)}
                              </td>
                              <td className="py-2.5 px-3 align-top max-w-[200px]">
                                {renderValue(entry.new_value)}
                              </td>
                              <td className="py-2.5 px-3 align-top">
                                {isBreaking ? (
                                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-red-500/10 text-destructive border border-destructive/30">
                                    <AlertTriangle className="w-3 h-3 text-destructive" />
                                    Breaking
                                  </span>
                                ) : (
                                  <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground border border-border">
                                    Safe
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end border-t border-border px-6 py-3 bg-muted/30">
          <button
            type="button"
            onClick={onClose}
            className="gh-btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
