"use client";

/**
 * Plugin Card Component.
 * Displays discovered MCP/in-process plugin metadata, security risk level,
 * permission scopes, and untrusted execution boundaries.
 * Follows GitHub Primer aesthetic with semantic tokens.
 */

import React from "react";
import {
  Blocks,
  Terminal,
  Radio,
  Cpu,
  KeyRound,
  Wrench,
  AlertTriangle,
  FileJson,
} from "lucide-react";
import type { PluginInfo, PluginTransport } from "@/lib/types";
import { PluginRiskBadge, ApprovalRequiredBadge } from "@/components/badges";

interface PluginCardProps {
  plugin: PluginInfo;
  onInspect?: (plugin: PluginInfo) => void;
}

function getTransportBadge(transport: PluginTransport) {
  switch (transport) {
    case "in-process":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-muted text-muted-foreground border border-border">
          <Cpu className="w-3 h-3 text-muted-foreground" />
          <span>In-Process</span>
        </span>
      );
    case "mcp-stdio":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/30">
          <Terminal className="w-3 h-3 text-blue-500" />
          <span>MCP Stdio</span>
        </span>
      );
    case "mcp-sse":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/30">
          <Radio className="w-3 h-3 text-purple-500" />
          <span>MCP SSE</span>
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-muted text-muted-foreground border border-border">
          <span>{transport}</span>
        </span>
      );
  }
}

export function PluginCard({ plugin, onInspect }: PluginCardProps) {
  return (
    <div
      data-testid={`plugin-card-${plugin.name}`}
      className="flex flex-col justify-between rounded-xl border border-border bg-card p-5 text-card-foreground shadow-xs hover:border-foreground/20 transition-all duration-200"
    >
      <div className="space-y-4">
        {/* Top Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-muted text-foreground border border-border shrink-0">
              <Blocks className="w-5 h-5 text-foreground" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-mono font-semibold text-base text-foreground truncate">
                  {plugin.name}
                </h3>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/60">
                  v{plugin.version}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {plugin.tools.length} exposed {plugin.tools.length === 1 ? "capability" : "capabilities"}
              </p>
            </div>
          </div>
          <div className="shrink-0">{getTransportBadge(plugin.transport)}</div>
        </div>

        {/* Security & Risk Governance Flags */}
        <div className="flex items-center gap-2 flex-wrap pt-1">
          <PluginRiskBadge risk={plugin.risk} />
          <ApprovalRequiredBadge required={plugin.requires_approval} />
          {plugin.untrusted_output && (
            <span
              data-testid="untrusted-output-badge"
              className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30"
              title="Outputs from this plugin are treated as untrusted data and quarantined"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span>Untrusted Output</span>
            </span>
          )}
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground leading-relaxed">
          {plugin.description || "No description provided."}
        </p>

        {/* Permission Scopes */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
            <KeyRound className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Scopes</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {plugin.scopes && plugin.scopes.length > 0 ? (
              plugin.scopes.map((scope) => (
                <span
                  key={scope}
                  className="inline-flex items-center font-mono text-[11px] px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/50"
                >
                  {scope}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground italic">
                None (no elevated scopes requested)
              </span>
            )}
          </div>
        </div>

        {/* Exposed Tools */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
            <Wrench className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Tools</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {plugin.tools && plugin.tools.length > 0 ? (
              plugin.tools.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center font-mono text-[11px] px-2 py-0.5 rounded bg-secondary text-secondary-foreground border border-border/40"
                >
                  {t}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground italic">
                No tools registered
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Footer / Inspect Action */}
      <div className="pt-5 mt-4 border-t border-border flex items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground font-mono">
          {plugin.config_schema ? "Has Config Schema" : "No Custom Config"}
        </span>
        {onInspect && (
          <button
            type="button"
            onClick={() => onInspect(plugin)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-muted hover:bg-muted/80 text-foreground border border-border transition-colors cursor-pointer"
          >
            <FileJson className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Inspect Manifest</span>
          </button>
        )}
      </div>
    </div>
  );
}
