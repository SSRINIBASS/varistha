"use client";

/**
 * Plugin Inspector Modal Component.
 * Inspects plugin manifest definition, configuration JSON schema,
 * permission scopes, and untrusted quarantine requirements.
 * Follows GitHub Primer aesthetic with semantic design tokens.
 */

import React, { useState } from "react";
import {
  X,
  FileCode,
  Sliders,
  Shield,
  KeyRound,
  Wrench,
  AlertTriangle,
  Blocks,
  Copy,
  Check,
} from "lucide-react";
import type { PluginInfo } from "@/lib/types";
import { PluginRiskBadge, ApprovalRequiredBadge } from "@/components/badges";

interface PluginInspectorProps {
  plugin: PluginInfo | null;
  isOpen: boolean;
  onClose: () => void;
}

export function PluginInspector({
  plugin,
  isOpen,
  onClose,
}: PluginInspectorProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "schema" | "manifest">(
    "overview"
  );
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen || !plugin) return null;

  const handleCopyManifest = () => {
    navigator.clipboard.writeText(JSON.stringify(plugin, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      data-testid="plugin-inspector-modal"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-3xl rounded-xl border border-border bg-card shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/40">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-background border border-border shrink-0">
              <Blocks className="w-5 h-5 text-foreground" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-mono font-semibold text-lg text-foreground truncate">
                  {plugin.name}
                </h2>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border">
                  v{plugin.version}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5 truncate">
                {plugin.description || "Plugin Manifest Inspector"}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-4 px-6 border-b border-border bg-card">
          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "overview"
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Governance & Capabilities</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("schema")}
            className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "schema"
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Config Schema</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("manifest")}
            className={`py-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "manifest"
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span>Raw Manifest</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm text-foreground">
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Security Boundary Alert */}
              {plugin.untrusted_output && (
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-200 text-xs sm:text-sm space-y-1">
                  <div className="flex items-center gap-2 font-medium">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                    <span>Untrusted Output Enforcement</span>
                  </div>
                  <p className="text-muted-foreground">
                    Content returned by this plugin is treated as external, untrusted input. The Varistha runtime enforces boundary sanitization outside the model to prevent prompt injection and privilege escalation.
                  </p>
                </div>
              )}

              {/* Governance Properties Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-1.5">
                  <span className="text-xs text-muted-foreground font-medium">Risk Level</span>
                  <div>
                    <PluginRiskBadge risk={plugin.risk} />
                  </div>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-1.5">
                  <span className="text-xs text-muted-foreground font-medium">Approval Policy</span>
                  <div>
                    <ApprovalRequiredBadge required={plugin.requires_approval} />
                  </div>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-1.5">
                  <span className="text-xs text-muted-foreground font-medium">Transport Mechanism</span>
                  <div className="font-mono text-xs font-semibold text-foreground">
                    {plugin.transport}
                  </div>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-1.5">
                  <span className="text-xs text-muted-foreground font-medium">Output Quarantine</span>
                  <div className="text-xs font-semibold text-foreground">
                    {plugin.untrusted_output ? "Quarantine Active" : "Trusted Source"}
                  </div>
                </div>
              </div>

              {/* Scopes & Permissions */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 font-medium text-foreground">
                  <KeyRound className="w-4 h-4 text-muted-foreground" />
                  <span>Required Scopes & Permissions</span>
                </div>
                <div className="p-4 rounded-lg border border-border bg-muted/10">
                  {plugin.scopes && plugin.scopes.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {plugin.scopes.map((s) => (
                        <span
                          key={s}
                          className="font-mono text-xs px-2.5 py-1 rounded bg-muted text-foreground border border-border"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">
                      No elevated network, system, or storage scopes declared.
                    </p>
                  )}
                </div>
              </div>

              {/* Exposed Tools */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 font-medium text-foreground">
                  <Wrench className="w-4 h-4 text-muted-foreground" />
                  <span>Exposed Tool Functions</span>
                </div>
                <div className="p-4 rounded-lg border border-border bg-muted/10 space-y-2">
                  {plugin.tools && plugin.tools.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {plugin.tools.map((tool) => (
                        <div
                          key={tool}
                          className="flex items-center gap-2 px-3 py-2 rounded border border-border bg-card font-mono text-xs text-foreground"
                        >
                          <span className="w-2 h-2 rounded-full bg-emerald-500" />
                          <span>{tool}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">
                      No tool functions exposed directly.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === "schema" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  Configuration schema defined in plugin manifest:
                </span>
              </div>
              {plugin.config_schema && Object.keys(plugin.config_schema).length > 0 ? (
                <pre className="font-mono text-xs p-4 rounded-lg bg-muted/60 border border-border text-foreground overflow-x-auto max-h-[350px]">
                  {JSON.stringify(plugin.config_schema, null, 2)}
                </pre>
              ) : (
                <div className="p-8 text-center rounded-lg border border-dashed border-border text-muted-foreground text-xs">
                  This plugin does not require or declare a custom configuration schema.
                </div>
              )}
            </div>
          )}

          {activeTab === "manifest" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  Complete plugin manifest payload:
                </span>
                <button
                  type="button"
                  onClick={handleCopyManifest}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs bg-muted hover:bg-muted/80 text-foreground border border-border transition-colors cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                      <span>Copy JSON</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="font-mono text-xs p-4 rounded-lg bg-muted/60 border border-border text-foreground overflow-x-auto max-h-[350px]">
                {JSON.stringify(plugin, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-border bg-muted/20 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-muted hover:bg-muted/80 text-foreground border border-border transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
