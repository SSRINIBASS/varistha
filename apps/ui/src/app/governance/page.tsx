"use client";

/**
 * Governance & Human-in-the-Loop Control Room.
 * Follows GitHub Primer aesthetic: full-width span, card borders, and semantic tokens.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  ShieldAlert,
  Clock,
  DollarSign,
  ShieldCheck,
  Power,
} from "lucide-react";
import {
  getAgents,
  getApprovals,
  getAgentBudget,
  getGlobalKillSwitch,
  getPolicies,
} from "@/lib/api";
import type {
  Agent,
  AgentBudgetStatus,
  ApprovalItem,
  GlobalKillSwitchStatus,
  PolicyInfo,
} from "@/lib/types";
import { ApprovalsInbox } from "@/components/governance/approvals-inbox";
import { BudgetsDashboard } from "@/components/governance/budgets-dashboard";
import { GuardrailsExplorer } from "@/components/governance/guardrails-explorer";
import { CardSkeleton } from "@/components/loading-skeleton";
import { ErrorAlert } from "@/components/error-alert";

type GovernanceTab = "approvals" | "budgets" | "policies";

export default function GovernancePage() {
  const [activeTab, setActiveTab] = useState<GovernanceTab>("approvals");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [budgets, setBudgets] = useState<Record<string, AgentBudgetStatus>>({});
  const [globalKillSwitch, setGlobalKillSwitchState] = useState<GlobalKillSwitchStatus>({
    enabled: false,
    reason: null,
    tripped_at: null,
    operator: null,
  });
  const [policies, setPolicies] = useState<PolicyInfo[]>([]);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [approvalsRes, agentsRes, globalKsRes, policiesRes] = await Promise.all([
        getApprovals({ limit: 100 }),
        getAgents(100),
        getGlobalKillSwitch(),
        getPolicies(),
      ]);

      setApprovals(approvalsRes.items);
      setAgents(agentsRes.items);
      setGlobalKillSwitchState(globalKsRes);
      setPolicies(policiesRes.policies);

      // Fetch individual budgets for agents
      const budgetEntries = await Promise.allSettled(
        agentsRes.items.map(async (agent) => {
          const b = await getAgentBudget(agent.name);
          return { key: agent.name, idKey: agent.id, data: b };
        })
      );

      const budgetMap: Record<string, AgentBudgetStatus> = {};
      for (const res of budgetEntries) {
        if (res.status === "fulfilled") {
          budgetMap[res.value.key] = res.value.data;
          budgetMap[res.value.idKey] = res.value.data;
        }
      }
      setBudgets(budgetMap);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load governance data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    async function initialize() {
      try {
        const [approvalsRes, agentsRes, globalKsRes, policiesRes] = await Promise.all([
          getApprovals({ limit: 100 }),
          getAgents(100),
          getGlobalKillSwitch(),
          getPolicies(),
        ]);

        if (ignore) return;

        setApprovals(approvalsRes.items);
        setAgents(agentsRes.items);
        setGlobalKillSwitchState(globalKsRes);
        setPolicies(policiesRes.policies);

        const budgetEntries = await Promise.allSettled(
          agentsRes.items.map(async (agent) => {
            const b = await getAgentBudget(agent.name);
            return { key: agent.name, idKey: agent.id, data: b };
          })
        );

        if (ignore) return;

        const budgetMap: Record<string, AgentBudgetStatus> = {};
        for (const res of budgetEntries) {
          if (res.status === "fulfilled") {
            budgetMap[res.value.key] = res.value.data;
            budgetMap[res.value.idKey] = res.value.data;
          }
        }
        setBudgets(budgetMap);
        setIsLoading(false);
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load governance data");
          setIsLoading(false);
        }
      }
    }

    initialize();

    return () => {
      ignore = true;
    };
  }, []);

  // Derived metrics
  const pendingApprovalsCount = approvals.filter((a) => a.status === "pending").length;
  const haltedAgentsCount = Object.values(budgets).filter((b) => b.kill_switch_tripped).length;
  const totalDailySpend = Object.values(budgets).reduce(
    (sum, b) => sum + (b.daily_spend_usd || 0),
    0
  );

  return (
    <div className="w-full min-h-[calc(100vh-3.5rem)] px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Page Title & Breadcrumb */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-primary" />
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Governance & Boundaries
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-muted-foreground">
          Human-in-the-loop approvals, budget enforcement, kill-switch circuit breakers, and guardrail policies.
        </p>
      </div>

      {error && (
        <ErrorAlert
          message={error}
          onRetry={loadData}
        />
      )}

      {/* Overview Metric Bento Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Pending Approvals */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold">Pending Approvals</span>
            <Clock
              className={`w-4 h-4 ${
                pendingApprovalsCount > 0 ? "text-amber-500 animate-pulse" : "text-muted-foreground"
              }`}
            />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {pendingApprovalsCount}
          </div>
          <div className="text-[11px] text-muted-foreground">
            {pendingApprovalsCount > 0
              ? "Human review required"
              : "All actions approved"}
          </div>
        </div>

        {/* Circuit Breakers / Halted */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold">Circuit Breakers</span>
            <ShieldCheck className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {haltedAgentsCount}
          </div>
          <div className="text-[11px] text-muted-foreground">
            {haltedAgentsCount > 0 ? "Halted agents" : "All agents active"}
          </div>
        </div>

        {/* Global Emergency Stop */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold">Emergency Stop</span>
            <Power
              className={`w-4 h-4 ${
                globalKillSwitch.enabled ? "text-rose-500 animate-pulse" : "text-emerald-500"
              }`}
            />
          </div>
          <div
            className={`text-sm font-bold font-mono uppercase truncate ${
              globalKillSwitch.enabled ? "text-rose-600 dark:text-rose-400" : "text-emerald-600 dark:text-emerald-400"
            }`}
          >
            {globalKillSwitch.enabled ? "TRIPPED" : "NORMAL"}
          </div>
          <div className="text-[11px] text-muted-foreground">
            {globalKillSwitch.enabled ? "All dispatches blocked" : "Platform operational"}
          </div>
        </div>

        {/* Daily Spend */}
        <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold">Daily Rolling Spend</span>
            <DollarSign className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            ${totalDailySpend.toFixed(4)}
          </div>
          <div className="text-[11px] text-muted-foreground">
            Across {agents.length} registered agents
          </div>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="border-b border-border flex items-center gap-2 overflow-x-auto text-xs font-medium">
        <button
          type="button"
          onClick={() => setActiveTab("approvals")}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all whitespace-nowrap ${
            activeTab === "approvals"
              ? "border-[#fd8c73] dark:border-[#f78166] text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Human Approvals</span>
          {pendingApprovalsCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
              {pendingApprovalsCount}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("budgets")}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all whitespace-nowrap ${
            activeTab === "budgets"
              ? "border-[#fd8c73] dark:border-[#f78166] text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
          }`}
        >
          <DollarSign className="w-3.5 h-3.5" />
          <span>Budgets & Circuit Breakers</span>
          {haltedAgentsCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-semibold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
              {haltedAgentsCount}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("policies")}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 transition-all whitespace-nowrap ${
            activeTab === "policies"
              ? "border-[#fd8c73] dark:border-[#f78166] text-foreground font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Guardrails & Policies</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-muted text-muted-foreground border border-border">
            {policies.length}
          </span>
        </button>
      </div>

      {/* Main Tab Content */}
      {isLoading ? (
        <CardSkeleton count={4} />
      ) : (
        <div className="pt-2">
          {activeTab === "approvals" && (
            <ApprovalsInbox
              approvals={approvals}
              onRefresh={loadData}
              isLoading={isLoading}
            />
          )}

          {activeTab === "budgets" && (
            <BudgetsDashboard
              agents={agents}
              budgets={budgets}
              globalKillSwitch={globalKillSwitch}
              onRefresh={loadData}
              isLoading={isLoading}
            />
          )}

          {activeTab === "policies" && (
            <GuardrailsExplorer policies={policies} />
          )}
        </div>
      )}
    </div>
  );
}
