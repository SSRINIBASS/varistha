"use client";

/**
 * Plugins & Capability Management Page.
 * Follows GitHub Primer UI/UX design:
 * - Metric summary cards for total plugins, risk levels, and approval gating.
 * - Subnav tabs for Plugin Directory and Security Architecture.
 * - Semantic tokens, card borders, light and dark theme compatibility.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  Blocks,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Info,
  Lock,
  Cpu,
  Layers,
} from "lucide-react";
import { getPlugins } from "@/lib/api";
import type { PluginInfo } from "@/lib/types";
import { PluginExplorer } from "@/components/plugins/plugin-explorer";
import { CardSkeleton } from "@/components/loading-skeleton";
import { ErrorAlert } from "@/components/error-alert";

type PluginsTab = "directory" | "security";

export default function PluginsPage() {
  const [activeTab, setActiveTab] = useState<PluginsTab>("directory");
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshPlugins = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await getPlugins();
      setPlugins(res.plugins);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to refresh plugins");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    async function loadInitial() {
      try {
        const res = await getPlugins();
        if (!ignore) {
          setPlugins(res.plugins);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load plugins");
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadInitial();
    return () => {
      ignore = true;
    };
  }, []);

  // Derived metrics
  const totalPlugins = plugins.length;
  const lowRiskCount = plugins.filter((p) => p.risk === "low").length;
  const approvalGatedCount = plugins.filter((p) => p.requires_approval).length;
  const untrustedOutputCount = plugins.filter((p) => p.untrusted_output).length;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-lg bg-muted text-foreground border border-border">
                <Blocks className="w-5 h-5 text-foreground" />
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Plugin Ecosystem
              </h1>
            </div>
            <p className="mt-1 text-sm text-muted-foreground max-w-3xl">
              Self-contained capabilities exposed over Model Context Protocol (MCP) and in-process hosts.
              Governs tool execution boundaries, permission scopes, and untrusted output quarantine.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={refreshPlugins}
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-card hover:bg-muted text-foreground border border-border transition-colors cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && <ErrorAlert message={error} />}

        {/* Metric KPI Bento Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Installed Plugins</span>
              <Blocks className="w-4 h-4 text-foreground" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-foreground">
                {isLoading ? "..." : totalPlugins}
              </span>
              <span className="text-xs text-muted-foreground">manifests</span>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Low Risk</span>
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {isLoading ? "..." : lowRiskCount}
              </span>
              <span className="text-xs text-muted-foreground">read-only / safe</span>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Approval Gated</span>
              <ShieldAlert className="w-4 h-4 text-amber-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {isLoading ? "..." : approvalGatedCount}
              </span>
              <span className="text-xs text-muted-foreground">human-in-the-loop</span>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium">Untrusted Output</span>
              <AlertTriangle className="w-4 h-4 text-rose-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-rose-600 dark:text-rose-400">
                {isLoading ? "..." : untrustedOutputCount}
              </span>
              <span className="text-xs text-muted-foreground">quarantined</span>
            </div>
          </div>
        </div>

        {/* Subnav Underline Tabs */}
        <div className="border-b border-border flex items-center gap-6">
          <button
            type="button"
            onClick={() => setActiveTab("directory")}
            className={`pb-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "directory"
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Blocks className="w-4 h-4" />
            <span>Plugin Directory</span>
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-xs bg-muted text-muted-foreground">
              {plugins.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("security")}
            className={`pb-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "security"
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Lock className="w-4 h-4" />
            <span>Security Architecture</span>
          </button>
        </div>

        {/* Tab Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        ) : (
          <>
            {activeTab === "directory" && <PluginExplorer plugins={plugins} />}

            {activeTab === "security" && (
              <div className="space-y-6 max-w-4xl">
                <div className="rounded-xl border border-border bg-card p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-muted border border-border">
                      <Lock className="w-5 h-5 text-foreground" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-foreground">
                        Varistha Plugin Security Boundaries
                      </h2>
                      <p className="text-xs text-muted-foreground">
                        Enforced per docs/SPEC.md § 3.1 & Appendix A
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div className="p-4 rounded-lg bg-muted/20 border border-border space-y-2">
                      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                        <Cpu className="w-4 h-4 text-primary" />
                        <span>Deterministic Code Enforcement</span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Tool permissions, rate limits, and approval policies are never delegated to the LLM. They are evaluated and enforced in deterministic Python middleware before any tool call executes.
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-muted/20 border border-border space-y-2">
                      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        <span>Untrusted Output Quarantine</span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Data fetched from external websites, search engines, or public APIs is treated as untrusted. Output is isolated in quarantined data blocks to prevent prompt injection and instruction poisoning.
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-muted/20 border border-border space-y-2">
                      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                        <ShieldAlert className="w-4 h-4 text-rose-500" />
                        <span>SSRF & Private Network Defense</span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Network plugins (web-fetch, web-scrape) strictly prohibit requests to loopback (127.0.0.0/8), RFC 1918 private IP ranges, cloud instance metadata services (169.254.169.254), and local hostnames.
                      </p>
                    </div>

                    <div className="p-4 rounded-lg bg-muted/20 border border-border space-y-2">
                      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                        <Layers className="w-4 h-4 text-blue-500" />
                        <span>Model Context Protocol (MCP)</span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Plugins run as standalone MCP servers or in-process adapters with explicit JSON schemas. Core contains zero hardcoded vendor tool logic, ensuring modularity and clean architectural boundaries.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-6 flex items-start gap-4">
                  <Info className="w-5 h-5 text-muted-foreground shrink-0 mt-0.5" />
                  <div className="text-xs text-muted-foreground space-y-1">
                    <h3 className="font-semibold text-foreground text-sm">
                      Registering New Plugins
                    </h3>
                    <p>
                      To add a new capability, create a subdirectory under <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-foreground">plugins/&lt;plugin-name&gt;/</code> containing a <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-foreground">manifest.yaml</code> and an MCP entrypoint or in-process adapter. The Varistha registry dynamically discovers all manifests on startup.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
