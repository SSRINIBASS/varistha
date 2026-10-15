/**
 * Semantic Stage and Status Badges.
 * Follows docs/SPEC.md § 4.4 design rules:
 * - Stage badges: Draft grey, Prototype blue, Staging violet, Production green, Deprecated amber, Retired slate.
 * - Always pair color with an icon or label, never color alone.
 */

import React from "react";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  AlertTriangle,
  Layers,
  Sparkles,
  ShieldCheck,
  Archive,
  Ban,
  Radio,
} from "lucide-react";
import type { AgentStage, AutonomyLevel, RunStatus } from "@/lib/types";

interface StageBadgeProps {
  stage: AgentStage | string;
  className?: string;
}

export function StageBadge({ stage, className = "" }: StageBadgeProps) {
  const normalized = stage.toLowerCase() as AgentStage;

  switch (normalized) {
    case "draft":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 ${className}`}
        >
          <Layers className="w-3 h-3 text-zinc-500" />
          <span>Draft</span>
        </span>
      );
    case "prototype":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60 ${className}`}
        >
          <Sparkles className="w-3 h-3 text-blue-500" />
          <span>Prototype</span>
        </span>
      );
    case "staging":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-200 dark:border-purple-800/60 ${className}`}
        >
          <Clock className="w-3 h-3 text-purple-500" />
          <span>Staging</span>
        </span>
      );
    case "production":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 ${className}`}
        >
          <ShieldCheck className="w-3 h-3 text-emerald-500" />
          <span>Production</span>
        </span>
      );
    case "deprecated":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 ${className}`}
        >
          <AlertTriangle className="w-3 h-3 text-amber-500" />
          <span>Deprecated</span>
        </span>
      );
    case "retired":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700 ${className}`}
        >
          <Archive className="w-3 h-3 text-slate-500" />
          <span>Retired</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 ${className}`}
        >
          <span>{stage}</span>
        </span>
      );
  }
}

interface StatusBadgeProps {
  status: RunStatus | string;
  className?: string;
}

export function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  const normalized = status.toLowerCase() as RunStatus;

  switch (normalized) {
    case "completed":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/50 ${className}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Completed</span>
        </span>
      );
    case "running":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border border-blue-200 dark:border-blue-800/50 ${className}`}
        >
          <Radio className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
          <span>Running</span>
        </span>
      );
    case "failed":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border border-rose-200 dark:border-rose-800/50 ${className}`}
        >
          <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
          <span>Failed</span>
        </span>
      );
    case "waiting_approval":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border border-amber-200 dark:border-amber-800/50 ${className}`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          <span>Waiting Approval</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 ${className}`}
        >
          <Ban className="w-3 h-3 text-zinc-400" />
          <span>{status}</span>
        </span>
      );
  }
}

interface AutonomyBadgeProps {
  autonomy: AutonomyLevel | string;
  className?: string;
}

export function AutonomyBadge({ autonomy, className = "" }: AutonomyBadgeProps) {
  const descriptions: Record<string, string> = {
    L0: "L0 Suggest: Agent proposes, human acts",
    L1: "L1 Act with approval: Agent acts after human approval",
    L2: "L2 Sampled review: Sampled post-execution review",
    L3: "L3 Autonomous: Acts within policy & budget limits",
  };

  const title = descriptions[autonomy] || `Autonomy ${autonomy}`;

  return (
    <span
      title={title}
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200 border border-zinc-200/80 dark:border-zinc-700/80 cursor-help ${className}`}
    >
      {autonomy}
    </span>
  );
}

interface ApprovalStatusBadgeProps {
  status: string;
  className?: string;
}

export function ApprovalStatusBadge({ status, className = "" }: ApprovalStatusBadgeProps) {
  const s = status.toLowerCase();

  switch (s) {
    case "pending":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30 ${className}`}
        >
          <Clock className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
          <span>Pending</span>
        </span>
      );
    case "approved":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 ${className}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Approved</span>
        </span>
      );
    case "rejected":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/30 ${className}`}
        >
          <Ban className="w-3.5 h-3.5 text-rose-500" />
          <span>Rejected</span>
        </span>
      );
    case "edited":
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/30 ${className}`}
        >
          <Sparkles className="w-3.5 h-3.5 text-blue-500" />
          <span>Edited</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border ${className}`}
        >
          <span>{status}</span>
        </span>
      );
  }
}

interface KillSwitchBadgeProps {
  tripped: boolean;
  className?: string;
}

export function KillSwitchBadge({ tripped, className = "" }: KillSwitchBadgeProps) {
  if (tripped) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-500/30 ${className}`}
      >
        <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
        <span>Halted</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/25 ${className}`}
    >
      <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
      <span>Active</span>
    </span>
  );
}
