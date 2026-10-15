"use client";

/**
 * Lifecycle Kanban Board.
 * Displays agents across the 6 lifecycle stages (Draft, Prototype, Staging,
 * Production, Deprecated, Retired) with promotion gating, immutable history,
 * and spec diff modals.
 *
 * Adheres strictly to docs/SPEC.md § 3.2, § 4.4, § 5 design system guidelines.
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Layers,
  Search,
  RefreshCw,
  ArrowUpRight,
  History,
  GitCompare,
  User,
  Clock,
  Table as TableIcon,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  Archive,
  Info,
  ExternalLink,
} from "lucide-react";
import type { Agent, AgentStage } from "@/lib/types";
import { getAgents } from "@/lib/api";
import { StageBadge } from "./badges";
import { PromoteModal } from "./promote-modal";
import { StageHistoryModal } from "./stage-history-modal";
import { VersionDiffModal } from "./version-diff-modal";
import { CardSkeleton } from "./loading-skeleton";

const STAGE_COLUMNS: Array<{
  stage: AgentStage;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}> = [
  {
    stage: "draft",
    label: "Draft",
    icon: Layers,
    description: "Spec authored. Local validation only, no live runs.",
  },
  {
    stage: "prototype",
    label: "Prototype",
    icon: Sparkles,
    description: "Dev environment executions with mock plugins.",
  },
  {
    stage: "staging",
    label: "Staging",
    icon: Clock,
    description: "Shadow runs with prod data and human output reviews.",
  },
  {
    stage: "production",
    label: "Production",
    icon: ShieldCheck,
    description: "Live deployment with assigned autonomy & SLAs.",
  },
  {
    stage: "deprecated",
    label: "Deprecated",
    icon: AlertTriangle,
    description: "Phase-out scheduled or superseded. No new runs.",
  },
  {
    stage: "retired",
    label: "Retired",
    icon: Archive,
    description: "Permanently decommissioned. Secrets revoked.",
  },
];

interface LifecycleBoardProps {
  initialAgents?: Agent[];
}

export function LifecycleBoard({ initialAgents }: LifecycleBoardProps) {
  const [agents, setAgents] = useState<Agent[]>(initialAgents || []);
  const [loading, setLoading] = useState<boolean>(!initialAgents);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals state
  const [agentForPromotion, setAgentForPromotion] = useState<Agent | null>(null);
  const [agentForHistory, setAgentForHistory] = useState<Agent | null>(null);
  const [agentForDiff, setAgentForDiff] = useState<Agent | null>(null);

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAgents(100, 0);
      setAgents(res.items);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load agent registry"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialAgents) return;
    let active = true;
    getAgents(100, 0)
      .then((res) => {
        if (active) {
          setAgents(res.items);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Failed to load agent registry"
          );
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [initialAgents]);

  const filteredAgents = useMemo(() => {
    if (!searchQuery.trim()) return agents;
    const q = searchQuery.toLowerCase();
    return agents.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        (a.owner ? a.owner.toLowerCase().includes(q) : false) ||
        (a.description && a.description.toLowerCase().includes(q))
    );
  }, [agents, searchQuery]);

  // Group agents by stage
  const agentsByStage = useMemo(() => {
    const map: Record<AgentStage, Agent[]> = {
      draft: [],
      prototype: [],
      staging: [],
      production: [],
      deprecated: [],
      retired: [],
    };

    for (const agent of filteredAgents) {
      const stage = (agent.stage?.toLowerCase() as AgentStage) || "draft";
      if (map[stage]) {
        map[stage].push(agent);
      } else {
        map.draft.push(agent);
      }
    }
    return map;
  }, [filteredAgents]);

  const handlePromoteSuccess = (updatedAgent: Agent) => {
    setAgents((prev) =>
      prev.map((a) => (a.id === updatedAgent.id ? updatedAgent : a))
    );
    // Refresh to get latest state
    fetchAgents();
  };

  return (
    <div className="space-y-6">
      {/* Header controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Agent Lifecycle Board
            </h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-primary/10 text-primary">
              {filteredAgents.length} Agents
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Govern agent lifecycle transitions with programmatic gate verification and immutable audits.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search bar */}
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter by name or owner..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-8 pl-8 pr-3 rounded-md border border-border bg-card text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-ring"
            />
          </div>

          {/* View toggle */}
          <Link
            href="/agents"
            className="flex items-center gap-1.5 h-8 px-3 rounded-md border border-border bg-card text-xs font-medium text-foreground hover:bg-muted transition-colors shadow-xs"
            title="Switch to Registry Table View"
          >
            <TableIcon className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="hidden sm:inline">Table View</span>
          </Link>

          {/* Refresh button */}
          <button
            type="button"
            onClick={fetchAgents}
            disabled={loading}
            className="flex items-center gap-1.5 h-8 px-3 rounded-md border border-border bg-card text-xs font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50 shadow-xs"
            title="Refresh agents"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-muted-foreground ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={fetchAgents}
            className="underline font-medium hover:opacity-80"
          >
            Retry
          </button>
        </div>
      )}

      {loading && !agents.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {STAGE_COLUMNS.map((col) => (
            <div key={col.stage} className="space-y-3">
              <div className="h-10 rounded-lg bg-muted/60 animate-pulse" />
              <CardSkeleton count={2} />
            </div>
          ))}
        </div>
      ) : (
        /* Kanban Columns Container: Fluid full-width on large screens with smooth horizontal scroll fallback */
        <div className="w-full overflow-x-auto pb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5 w-full min-w-[1050px] xl:min-w-0">
            {STAGE_COLUMNS.map((col) => {
              const stageAgents = agentsByStage[col.stage];
              const Icon = col.icon;

              return (
                <div
                  key={col.stage}
                  className="flex flex-col rounded-lg border border-border bg-card/60 shadow-2xs min-h-[550px]"
                >
                  {/* Column Header */}
                  <div className="p-3.5 border-b border-border bg-muted/30 rounded-t-xl space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <StageBadge stage={col.stage} />
                        <span className="text-xs font-mono font-semibold px-1.5 py-0.2 rounded-full bg-background border border-border text-foreground">
                          {stageAgents.length}
                        </span>
                      </div>
                      <div title={col.description} className="cursor-help text-muted-foreground hover:text-foreground">
                        <Info className="w-3.5 h-3.5" />
                      </div>
                    </div>
                    <p className="text-[11px] text-muted-foreground leading-tight line-clamp-2">
                      {col.description}
                    </p>
                  </div>

                  {/* Column Body / Agent Cards */}
                  <div className="p-2.5 flex-1 space-y-2.5 overflow-y-auto max-h-[calc(100vh-250px)]">
                    {stageAgents.length === 0 ? (
                      <div className="py-12 px-3 flex flex-col items-center justify-center text-center gap-2 border border-dashed border-border rounded-lg bg-muted/10">
                        <Icon className="w-5 h-5 text-muted-foreground/60" />
                        <span className="text-xs text-muted-foreground font-medium">
                          No {col.label} agents
                        </span>
                      </div>
                    ) : (
                      stageAgents.map((agent) => (
                        <div
                          key={agent.id}
                          className="group relative rounded-lg border border-border bg-card p-3 shadow-xs hover:border-primary/40 hover:shadow-sm transition-all space-y-2.5"
                        >
                          {/* Title & Version */}
                          <div className="flex items-start justify-between gap-1.5">
                            <Link
                              href={`/agents/${agent.id}`}
                              className="font-semibold text-xs text-foreground group-hover:text-primary transition-colors flex items-center gap-1 leading-snug break-all"
                            >
                              <span>{agent.name}</span>
                              <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                            </Link>
                            <span className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-muted text-muted-foreground border border-border">
                              v{agent.current_version}
                            </span>
                          </div>

                          {/* Description */}
                          {agent.description && (
                            <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                              {agent.description}
                            </p>
                          )}

                          {/* Metadata */}
                          <div className="space-y-1 pt-1 border-t border-border/60 text-[11px] text-muted-foreground font-mono">
                            <div className="flex items-center gap-1.5 truncate">
                              <User className="w-3 h-3 shrink-0" />
                              <span className="truncate" title={agent.owner ?? undefined}>
                                {agent.owner}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-[10px]">
                              <span>
                                {agent.version_count} {agent.version_count === 1 ? "version" : "versions"}
                              </span>
                              <span>
                                {new Date(agent.updated_at).toLocaleDateString(undefined, {
                                  month: "short",
                                  day: "numeric",
                                })}
                              </span>
                            </div>
                          </div>

                          {/* Card Action Buttons */}
                          <div className="flex items-center justify-between gap-1 pt-2 border-t border-border">
                            {/* Promote Button */}
                            <button
                              type="button"
                              onClick={() => setAgentForPromotion(agent)}
                              className="flex-1 flex items-center justify-center gap-1 h-6 px-1.5 rounded-md bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground text-[11px] font-medium transition-colors"
                              title="Promote or demote agent"
                            >
                              <ArrowUpRight className="w-3 h-3" />
                              <span>Promote</span>
                            </button>

                            {/* Spec Diff Button */}
                            <button
                              type="button"
                              onClick={() => setAgentForDiff(agent)}
                              className="flex items-center justify-center h-6 w-6 rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                              title="Compare spec versions"
                            >
                              <GitCompare className="w-3 h-3" />
                            </button>

                            {/* Stage Audit History Button */}
                            <button
                              type="button"
                              onClick={() => setAgentForHistory(agent)}
                              className="flex items-center justify-center h-6 w-6 rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                              title="View immutable stage transition audit history"
                            >
                              <History className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Promotion Modal */}
      {agentForPromotion && (
        <PromoteModal
          agent={agentForPromotion}
          isOpen={!!agentForPromotion}
          onClose={() => setAgentForPromotion(null)}
          onSuccess={handlePromoteSuccess}
        />
      )}

      {/* Stage History Modal */}
      {agentForHistory && (
        <StageHistoryModal
          agent={agentForHistory}
          isOpen={!!agentForHistory}
          onClose={() => setAgentForHistory(null)}
        />
      )}

      {/* Version Diff Modal */}
      {agentForDiff && (
        <VersionDiffModal
          agent={agentForDiff}
          isOpen={!!agentForDiff}
          onClose={() => setAgentForDiff(null)}
        />
      )}
    </div>
  );
}
