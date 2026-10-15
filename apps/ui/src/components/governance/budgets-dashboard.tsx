"use client";

/**
 * Budgets, Rate Limits, and Circuit Breakers Dashboard.
 * Displays agent daily spend vs caps, per-run limits, kill switches, and platform emergency stop.
 */

import React, { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ShieldAlert,
  Power,
  RotateCcw,
  RefreshCw,
  ExternalLink,
  DollarSign,
  Info,
} from "lucide-react";
import type { Agent, AgentBudgetStatus, GlobalKillSwitchStatus } from "@/lib/types";
import {
  tripAgentKillSwitch,
  resumeAgent,
  setGlobalKillSwitch,
} from "@/lib/api";
import { KillSwitchBadge, StageBadge } from "@/components/badges";

interface BudgetsDashboardProps {
  agents: Agent[];
  budgets: Record<string, AgentBudgetStatus>;
  globalKillSwitch: GlobalKillSwitchStatus;
  onRefresh: () => void;
  isLoading?: boolean;
}

export function BudgetsDashboard({
  agents,
  budgets,
  globalKillSwitch,
  onRefresh,
  isLoading = false,
}: BudgetsDashboardProps) {
  const [targetAgent, setTargetAgent] = useState<Agent | null>(null);
  const [killReason, setKillReason] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showGlobalModal, setShowGlobalModal] = useState<boolean>(false);
  const [globalReason, setGlobalReason] = useState<string>("");

  const handleTripAgent = async () => {
    if (!targetAgent) return;
    setIsSubmitting(true);
    try {
      await tripAgentKillSwitch(targetAgent.name, killReason || "Operator tripped kill switch");
      setTargetAgent(null);
      setKillReason("");
      onRefresh();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to trip kill switch");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResumeAgent = async (agentName: string) => {
    setIsSubmitting(true);
    try {
      await resumeAgent(agentName, "operator");
      onRefresh();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to resume agent");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleGlobal = async () => {
    setIsSubmitting(true);
    try {
      const willEnable = !globalKillSwitch.enabled;
      await setGlobalKillSwitch(
        willEnable,
        willEnable ? globalReason || "Platform emergency stop" : undefined,
        "operator"
      );
      setShowGlobalModal(false);
      setGlobalReason("");
      onRefresh();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to update emergency stop");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Global Emergency Stop Control Banner */}
      <div
        className={`rounded-xl border p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all shadow-xs ${
          globalKillSwitch.enabled
            ? "border-rose-500/50 bg-rose-500/10 dark:bg-rose-950/20 text-rose-800 dark:text-rose-200"
            : "border-border bg-card text-foreground"
        }`}
      >
        <div className="flex items-start sm:items-center gap-3.5">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
              globalKillSwitch.enabled
                ? "bg-rose-500 text-white animate-pulse"
                : "bg-muted text-muted-foreground"
            }`}
          >
            <Power className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 font-bold text-sm">
              <span>Global Emergency Stop</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider font-semibold ${
                  globalKillSwitch.enabled
                    ? "bg-rose-500 text-white"
                    : "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                }`}
              >
                {globalKillSwitch.enabled ? "ACTIVE (ALL AGENTS HALTED)" : "INACTIVE (NORMAL)"}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {globalKillSwitch.enabled
                ? `Emergency stop engaged: "${globalKillSwitch.reason || "Manual trip"}" (${
                    globalKillSwitch.tripped_at
                      ? new Date(globalKillSwitch.tripped_at).toLocaleTimeString()
                      : "Active"
                  })`
                : "Tripping the global emergency stop halts all agent triggers across the entire platform immediately outside the model."}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => {
            setErrorMsg(null);
            setShowGlobalModal(true);
          }}
          className={`px-4 py-2 rounded-lg font-semibold text-xs whitespace-nowrap transition-colors self-start sm:self-auto shadow-xs ${
            globalKillSwitch.enabled
              ? "bg-emerald-600 hover:bg-emerald-700 text-white"
              : "bg-rose-600 hover:bg-rose-700 text-white"
          }`}
        >
          {globalKillSwitch.enabled ? "Deactivate Emergency Stop" : "Activate Emergency Stop"}
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs font-mono">
          {errorMsg}
        </div>
      )}

      {/* Agents Budget & Circuit Breakers Grid Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <h3 className="text-sm font-bold text-foreground">Agent Budgets & Circuit Breakers</h3>
          <p className="text-xs text-muted-foreground">
            Monitors rolling UTC daily spend against budget caps and enforces per-run ceilings.
          </p>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Agent Budget Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const budget = budgets[agent.id] || budgets[agent.name];
          const dailySpend = budget?.daily_spend_usd ?? 0;
          const dailyLimit = budget?.daily_budget_usd ?? null;
          const maxPerRun = budget?.max_usd_per_run ?? null;
          const isHalted = budget?.kill_switch_tripped ?? false;

          const pctUsed = dailyLimit && dailyLimit > 0
            ? Math.min(100, Math.round((dailySpend / dailyLimit) * 100))
            : 0;

          return (
            <div
              key={agent.id}
              className={`rounded-xl border bg-card p-5 space-y-4 transition-all shadow-xs flex flex-col justify-between ${
                isHalted ? "border-rose-500/40 bg-rose-500/5" : "border-border"
              }`}
            >
              <div className="space-y-3">
                {/* Card Header */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <Link
                      href={`/agents/${agent.name}`}
                      className="font-bold text-sm text-foreground hover:underline flex items-center gap-1"
                    >
                      <span>{agent.name}</span>
                      <ExternalLink className="w-3 h-3 text-muted-foreground" />
                    </Link>
                    <div className="text-[11px] text-muted-foreground font-mono">
                      v{agent.current_version}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <StageBadge stage={agent.stage} />
                    <KillSwitchBadge tripped={isHalted} />
                  </div>
                </div>

                {/* Daily Spend Progress */}
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <DollarSign className="w-3.5 h-3.5 text-muted-foreground/70" />
                      Daily Spend:
                    </span>
                    <span className="font-mono font-semibold text-foreground">
                      ${dailySpend.toFixed(4)}
                      {dailyLimit ? ` / $${dailyLimit.toFixed(2)}` : " (Unlimited)"}
                    </span>
                  </div>

                  {dailyLimit && dailyLimit > 0 ? (
                    <div className="space-y-1">
                      <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            pctUsed >= 90
                              ? "bg-rose-500"
                              : pctUsed >= 70
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                          }`}
                          style={{ width: `${pctUsed}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-right text-muted-foreground font-mono">
                        {pctUsed}% utilized
                      </div>
                    </div>
                  ) : (
                    <div className="text-[11px] text-muted-foreground italic flex items-center gap-1">
                      <Info className="w-3 h-3" />
                      No daily USD budget cap declared
                    </div>
                  )}
                </div>

                {/* Per-Run Limit */}
                <div className="flex items-center justify-between text-xs pt-1 border-t border-border/50">
                  <span className="text-muted-foreground">Max Per Run:</span>
                  <span className="font-mono font-medium text-foreground">
                    {maxPerRun ? `$${maxPerRun.toFixed(2)}` : "No cap"}
                  </span>
                </div>

                {/* Kill Switch Reason */}
                {isHalted && budget?.kill_switch_reason && (
                  <div className="p-2 rounded-md bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-700 dark:text-rose-300">
                    <span className="font-semibold">Reason: </span>
                    {budget.kill_switch_reason}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-border/60 flex items-center justify-end gap-2">
                {isHalted ? (
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => handleResumeAgent(agent.name)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors shadow-xs"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Resume Agent</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setTargetAgent(agent);
                      setKillReason("");
                      setErrorMsg(null);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-700 dark:text-rose-300 text-xs font-semibold transition-colors"
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                    <span>Trip Kill Switch</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Trip Kill Switch Confirmation Modal */}
      {targetAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-rose-500/40 bg-card p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-rose-600 dark:text-rose-400">
              <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-rose-500" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-foreground">
                  Halt Agent: {targetAgent.name}
                </h3>
                <p className="text-xs text-muted-foreground">
                  Circuit breaker will block all subsequent runs outside the model.
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="kill-reason" className="text-xs font-semibold text-muted-foreground">
                Justification / Trip Reason:
              </label>
              <input
                id="kill-reason"
                type="text"
                value={killReason}
                onChange={(e) => setKillReason(e.target.value)}
                placeholder="e.g. Unusual tool error rate or budget anomaly"
                className="w-full px-3 py-2 text-xs rounded-md border border-border bg-muted/10 text-foreground focus:outline-hidden focus:ring-1 focus:ring-rose-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setTargetAgent(null)}
                className="px-4 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={handleTripAgent}
                className="px-4 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold transition-colors shadow-xs"
              >
                Confirm Halt
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Global Emergency Stop Modal */}
      {showGlobalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                <Power className="w-5 h-5 text-foreground" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-foreground">
                  {globalKillSwitch.enabled
                    ? "Deactivate Platform Emergency Stop"
                    : "Activate Platform Emergency Stop"}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {globalKillSwitch.enabled
                    ? "Resumes normal dispatching for all active agents."
                    : "Immediately halts ALL agent triggers across the entire platform."}
                </p>
              </div>
            </div>

            {!globalKillSwitch.enabled && (
              <div className="space-y-1.5">
                <label htmlFor="global-reason" className="text-xs font-semibold text-muted-foreground">
                  Emergency Justification Reason:
                </label>
                <input
                  id="global-reason"
                  type="text"
                  value={globalReason}
                  onChange={(e) => setGlobalReason(e.target.value)}
                  placeholder="e.g. Critical downstream incident or security audit"
                  className="w-full px-3 py-2 text-xs rounded-md border border-border bg-muted/10 text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
                />
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowGlobalModal(false)}
                className="px-4 py-1.5 rounded-md border border-border bg-card hover:bg-muted text-xs font-medium text-foreground transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={handleToggleGlobal}
                className={`px-4 py-1.5 rounded-md text-white text-xs font-semibold transition-colors shadow-xs ${
                  globalKillSwitch.enabled
                    ? "bg-emerald-600 hover:bg-emerald-700"
                    : "bg-rose-600 hover:bg-rose-700"
                }`}
              >
                {globalKillSwitch.enabled ? "Confirm Resume" : "Confirm Emergency Halt"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
