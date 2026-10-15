"use client";

/**
 * Plugin Explorer Component.
 * Searchable, filterable catalogue of all installed plugins.
 * Follows GitHub Primer aesthetic with semantic tokens.
 */

import React, { useState, useMemo } from "react";
import {
  Search,
  Filter,
  Blocks,
  X,
  SlidersHorizontal,
} from "lucide-react";
import type { PluginInfo, PluginRiskLevel, PluginTransport } from "@/lib/types";
import { PluginCard } from "./plugin-card";
import { PluginInspector } from "./plugin-inspector";
import { EmptyState } from "@/components/empty-state";

interface PluginExplorerProps {
  plugins: PluginInfo[];
}

export function PluginExplorer({ plugins }: PluginExplorerProps) {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedRisk, setSelectedRisk] = useState<PluginRiskLevel | "all">("all");
  const [selectedTransport, setSelectedTransport] = useState<PluginTransport | "all">("all");
  const [selectedApproval, setSelectedApproval] = useState<"all" | "required" | "auto">("all");
  const [inspectingPlugin, setInspectingPlugin] = useState<PluginInfo | null>(null);

  const filteredPlugins = useMemo(() => {
    return plugins.filter((plugin) => {
      // Search query matches name, description, tools, scopes
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesName = plugin.name.toLowerCase().includes(q);
        const matchesDesc = (plugin.description || "").toLowerCase().includes(q);
        const matchesScopes = plugin.scopes?.some((s) => s.toLowerCase().includes(q));
        const matchesTools = plugin.tools?.some((t) => t.toLowerCase().includes(q));
        if (!matchesName && !matchesDesc && !matchesScopes && !matchesTools) {
          return false;
        }
      }

      // Risk filter
      if (selectedRisk !== "all" && plugin.risk !== selectedRisk) {
        return false;
      }

      // Transport filter
      if (selectedTransport !== "all" && plugin.transport !== selectedTransport) {
        return false;
      }

      // Approval filter
      if (selectedApproval === "required" && !plugin.requires_approval) {
        return false;
      }
      if (selectedApproval === "auto" && plugin.requires_approval) {
        return false;
      }

      return true;
    });
  }, [plugins, searchQuery, selectedRisk, selectedTransport, selectedApproval]);

  const hasActiveFilters =
    Boolean(searchQuery.trim()) ||
    selectedRisk !== "all" ||
    selectedTransport !== "all" ||
    selectedApproval !== "all";

  const clearFilters = () => {
    setSearchQuery("");
    setSelectedRisk("all");
    setSelectedTransport("all");
    setSelectedApproval("all");
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar: Search & Filters */}
      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4 text-card-foreground shadow-xs">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search plugins by name, scope, tool, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground text-sm focus:outline-hidden focus:ring-1 focus:ring-ring"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Quick counts */}
          <div className="text-xs text-muted-foreground shrink-0 flex items-center gap-2 self-end sm:self-center">
            <span>
              Showing <strong className="text-foreground">{filteredPlugins.length}</strong> of{" "}
              <strong>{plugins.length}</strong> plugins
            </span>
            {hasActiveFilters && (
              <button
                type="button"
                onClick={clearFilters}
                className="text-primary hover:underline font-medium cursor-pointer"
              >
                Reset filters
              </button>
            )}
          </div>
        </div>

        {/* Filter Badges Row */}
        <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-border text-xs">
          {/* Risk Filter */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-muted-foreground font-medium flex items-center gap-1">
              <Filter className="w-3 h-3" /> Risk:
            </span>
            {(["all", "low", "medium", "high"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setSelectedRisk(r)}
                className={`px-2.5 py-1 rounded-md capitalize transition-colors cursor-pointer ${
                  selectedRisk === r
                    ? "bg-foreground text-background font-medium"
                    : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
                }`}
              >
                {r === "all" ? "All Risks" : r}
              </button>
            ))}
          </div>

          {/* Transport Filter */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-muted-foreground font-medium flex items-center gap-1">
              <SlidersHorizontal className="w-3 h-3" /> Transport:
            </span>
            {(["all", "in-process", "mcp-stdio", "mcp-sse"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setSelectedTransport(t)}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  selectedTransport === t
                    ? "bg-foreground text-background font-medium"
                    : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
                }`}
              >
                {t === "all"
                  ? "All Transports"
                  : t === "in-process"
                  ? "In-Process"
                  : t === "mcp-stdio"
                  ? "MCP Stdio"
                  : "MCP SSE"}
              </button>
            ))}
          </div>

          {/* Approval Filter */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-muted-foreground font-medium">Policy:</span>
            {(["all", "required", "auto"] as const).map((a) => (
              <button
                key={a}
                type="button"
                onClick={() => setSelectedApproval(a)}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  selectedApproval === a
                    ? "bg-foreground text-background font-medium"
                    : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
                }`}
              >
                {a === "all"
                  ? "All Policies"
                  : a === "required"
                  ? "Approval Gated"
                  : "Auto-Executable"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Plugins Grid */}
      {filteredPlugins.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredPlugins.map((plugin) => (
            <PluginCard
              key={plugin.name}
              plugin={plugin}
              onInspect={(p) => setInspectingPlugin(p)}
            />
          ))}
        </div>
      ) : hasActiveFilters ? (
        <EmptyState
          icon={Blocks}
          title="No Matching Plugins"
          description="No plugins match your active filter criteria. Try adjusting your search query or reset the filters."
          action={{
            label: "Clear Filters",
            onClick: clearFilters,
          }}
        />
      ) : (
        <EmptyState
          icon={Blocks}
          title="No Plugins Discovered"
          description="No plugin manifests found in plugins/ directory. Place plugin folders with manifest.yaml to register capabilities."
        />
      )}

      {/* Inspector Modal */}
      <PluginInspector
        plugin={inspectingPlugin}
        isOpen={Boolean(inspectingPlugin)}
        onClose={() => setInspectingPlugin(null)}
      />
    </div>
  );
}
