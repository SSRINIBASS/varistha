"use client";

/**
 * Agents Registry Page.
 * Lists all registered AI employees, stage lifecycle tags, and run triggers.
 */

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bot,
  Play,
  Activity,
  RefreshCw,
  Search,
  Layers,
} from "lucide-react";
import { getAgents } from "@/lib/api";
import type { Agent } from "@/lib/types";
import { StageBadge, AutonomyBadge } from "@/components/badges";
import { TableSkeleton } from "@/components/loading-skeleton";
import { EmptyState } from "@/components/empty-state";
import { ErrorAlert } from "@/components/error-alert";
import { TriggerRunModal } from "@/components/trigger-run-modal";

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedStage, setSelectedStage] = useState<string>("all");
  const [activeModalAgent, setActiveModalAgent] = useState<Agent | null>(null);

  const fetchAgentList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAgents();
      setAgents(res.items || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load agents from API"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    getAgents()
      .then((res) => {
        if (isMounted) {
          setAgents(res.items || []);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(
            err instanceof Error ? err.message : "Failed to load agents from API"
          );
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const matchesSearch =
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (agent.description &&
          agent.description.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStage =
        selectedStage === "all" ||
        agent.stage.toLowerCase() === selectedStage.toLowerCase();

      return matchesSearch && matchesStage;
    });
  }, [agents, searchQuery, selectedStage]);

  const stages = ["all", "prototype", "staging", "production", "draft"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Bot className="w-6 h-6 text-primary" />
            <span>AI Employees</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Active agents registered in the Varistha control plane.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/lifecycle"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-border bg-card text-foreground hover:bg-muted transition-colors cursor-pointer shadow-xs"
            title="Switch to Lifecycle Kanban view"
          >
            <Layers className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Lifecycle Board</span>
          </Link>
          <button
            type="button"
            onClick={fetchAgentList}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-border bg-card text-foreground hover:bg-muted transition-colors cursor-pointer"
            title="Refresh agents"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search agents by name or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-input bg-card text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {stages.map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setSelectedStage(st)}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-colors cursor-pointer ${
                selectedStage === st
                  ? "bg-secondary text-secondary-foreground font-semibold shadow-xs"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <TableSkeleton rows={5} columns={6} />
      ) : error ? (
        <ErrorAlert
          title="Could not connect to Varistha API"
          message={error}
          onRetry={fetchAgentList}
        />
      ) : filteredAgents.length === 0 ? (
        <EmptyState
          title={agents.length === 0 ? "No AI Employees Registered" : "No Matching Agents"}
          description={
            agents.length === 0
              ? "Initialize an agent using the Varistha CLI to register your first AI employee."
              : "No agents match the current filter or search criteria."
          }
          icon={Bot}
          action={
            agents.length === 0
              ? {
                  label: "Copy varistha init command",
                  onClick: () => {
                    navigator.clipboard?.writeText("varistha init my-agent");
                  },
                }
              : {
                  label: "Clear filters",
                  onClick: () => {
                    setSearchQuery("");
                    setSelectedStage("all");
                  },
                }
          }
        />
      ) : (
        <div className="gh-box w-full shadow-2xs">
          {/* GitHub Box Header */}
          <div className="gh-box-header flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-muted-foreground" />
              <span className="font-semibold text-foreground text-xs">
                {filteredAgents.length} {filteredAgents.length === 1 ? "AI Employee" : "AI Employees"}
              </span>
            </div>

            <div className="text-[11px] text-muted-foreground font-mono">
              Auto-updating via Varistha Control Plane
            </div>
          </div>

          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/20 font-medium text-muted-foreground">
                  <th className="py-2.5 px-4 font-semibold">Agent Name</th>
                  <th className="py-2.5 px-4 font-semibold">Stage</th>
                  <th className="py-2.5 px-4 font-semibold">Autonomy</th>
                  <th className="py-2.5 px-4 font-semibold">Version</th>
                  <th className="py-2.5 px-4 font-semibold">Owner</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredAgents.map((agent) => (
                  <tr
                    key={agent.id}
                    className="hover:bg-muted/30 transition-colors group"
                  >
                    <td className="py-3 px-4">
                      <div className="font-semibold text-foreground text-sm hover:text-accent-foreground transition-colors">
                        <Link href={`/agents/${agent.id}`}>
                          {agent.name}
                        </Link>
                      </div>
                      {agent.description && (
                        <div className="text-muted-foreground text-[11px] line-clamp-1 max-w-2xl mt-0.5">
                          {agent.description}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <StageBadge stage={agent.stage} />
                    </td>
                    <td className="py-3 px-4">
                      <AutonomyBadge autonomy="L1" />
                    </td>
                    <td className="py-3 px-4 font-mono text-muted-foreground">
                      v{agent.current_version}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground font-mono text-[11px]">
                      {agent.owner || "team@example.com"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          href={`/runs?agent_id=${agent.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-border bg-card text-foreground hover:bg-muted/80 transition-colors shadow-2xs"
                          title="View execution runs"
                        >
                          <Activity className="w-3.5 h-3.5 text-muted-foreground" />
                          <span>Runs</span>
                        </Link>
                        <button
                          type="button"
                          onClick={() => setActiveModalAgent(agent)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-primary text-primary-foreground hover:brightness-110 transition-all cursor-pointer shadow-2xs"
                          title="Execute run"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span>Run</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Trigger Run Dialog */}
      {activeModalAgent && (
        <TriggerRunModal
          agent={activeModalAgent}
          isOpen={Boolean(activeModalAgent)}
          onClose={() => setActiveModalAgent(null)}
          onSuccess={(runId) => {
            setActiveModalAgent(null);
            router.push(`/runs/${runId}`);
          }}
        />
      )}
    </div>
  );
}
