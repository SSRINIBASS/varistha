"use client";

/**
 * Custom Trace Waterfall Component.
 * Follows SPEC.md § 4.4 design rules:
 * - "Trace waterfall: Custom component, since spans are time bars and no library fits"
 * - Displays hierarchical spans with timeline offsets, duration bars, and attribute inspector.
 */

import React, { useMemo, useState } from "react";
import {
  Clock,
  Cpu,
  Layers,
  Sparkles,
  Wrench,
  ShieldCheck,
  AlertCircle,
  ChevronRight,
  Code2,
} from "lucide-react";
import type { Span } from "@/lib/types";

interface TraceWaterfallProps {
  spans: Span[];
  className?: string;
}

export function TraceWaterfall({ spans, className = "" }: TraceWaterfallProps) {
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(
    spans[0]?.id ?? null
  );

  // Compute timeline boundaries and durations
  const { sortedSpans, traceStartMs, totalDurationMs, selectedSpan } = useMemo(() => {
    if (!spans || spans.length === 0) {
      return {
        sortedSpans: [],
        traceStartMs: 0,
        totalDurationMs: 0,
        selectedSpan: null,
      };
    }

    // Sort by start_time ascending
    const sorted = [...spans].sort((a, b) => {
      const timeA = new Date(a.start_time).getTime();
      const timeB = new Date(b.start_time).getTime();
      return timeA - timeB;
    });

    const startTimes = sorted.map((s) => new Date(s.start_time).getTime());
    const endTimes = sorted.map((s) => {
      if (s.end_time) return new Date(s.end_time).getTime();
      if (s.duration_ms) return new Date(s.start_time).getTime() + s.duration_ms;
      return new Date(s.start_time).getTime() + 1;
    });

    const minStart = Math.min(...startTimes);
    const maxEnd = Math.max(...endTimes);
    const duration = Math.max(maxEnd - minStart, 1);

    const active = sorted.find((s) => s.id === selectedSpanId) ?? sorted[0] ?? null;

    return {
      sortedSpans: sorted,
      traceStartMs: minStart,
      totalDurationMs: duration,
      selectedSpan: active,
    };
  }, [spans, selectedSpanId]);

  if (spans.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground border border-dashed rounded-xl bg-card">
        No OpenTelemetry spans recorded for this execution trace.
      </div>
    );
  }

  function getSpanStyle(name: string, statusCode: string) {
    if (statusCode === "ERROR" || statusCode === "2") {
      return {
        bg: "bg-rose-500",
        badge: "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200",
        icon: AlertCircle,
        label: "Error",
      };
    }
    if (name.includes("llm") || name.includes("model")) {
      return {
        bg: "bg-sky-500",
        badge: "bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300 border-sky-200",
        icon: Sparkles,
        label: "LLM Call",
      };
    }
    if (name.includes("tool") || name.includes("fetch") || name.includes("plugin")) {
      return {
        bg: "bg-emerald-500",
        badge: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200",
        icon: Wrench,
        label: "Tool Call",
      };
    }
    if (name.includes("guardrail") || name.includes("policy")) {
      return {
        bg: "bg-amber-500",
        badge: "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200",
        icon: ShieldCheck,
        label: "Guardrail",
      };
    }
    return {
      bg: "bg-indigo-500",
      badge: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-200",
      icon: Cpu,
      label: "Workflow",
    };
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Waterfall Visualizer */}
      <div className="gh-box w-full shadow-2xs">
        <div className="gh-box-header px-4 py-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" />
            <span className="font-semibold text-foreground text-xs">Execution Timeline</span>
            <span className="gh-counter">
              {spans.length} {spans.length === 1 ? "span" : "spans"}
            </span>
          </div>
          <div className="flex items-center gap-1 font-mono text-[11px] text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span>Total: {totalDurationMs.toFixed(1)}ms</span>
          </div>
        </div>

        {/* Timeline Header Ruler */}
        <div className="grid grid-cols-12 px-4 py-2 border-b border-border/40 text-[10px] font-mono text-muted-foreground bg-muted/10">
          <div className="col-span-5 md:col-span-4 font-sans font-medium">Operation</div>
          <div className="col-span-7 md:col-span-8 flex justify-between pr-2">
            <span>0ms</span>
            <span>{(totalDurationMs * 0.25).toFixed(0)}ms</span>
            <span>{(totalDurationMs * 0.5).toFixed(0)}ms</span>
            <span>{(totalDurationMs * 0.75).toFixed(0)}ms</span>
            <span>{totalDurationMs.toFixed(0)}ms</span>
          </div>
        </div>

        {/* Span Waterfall Rows */}
        <div className="divide-y divide-border/40">
          {sortedSpans.map((span) => {
            const spanStart = new Date(span.start_time).getTime();
            const spanEnd = span.end_time
              ? new Date(span.end_time).getTime()
              : span.duration_ms
              ? spanStart + span.duration_ms
              : spanStart + 1;

            const durationMs = span.duration_ms ?? Math.max(spanEnd - spanStart, 0.1);
            const offsetMs = Math.max(0, spanStart - traceStartMs);
            const leftPercent = Math.min(100, Math.max(0, (offsetMs / totalDurationMs) * 100));
            const widthPercent = Math.min(
              100 - leftPercent,
              Math.max(2, (durationMs / totalDurationMs) * 100)
            );

            const isSelected = selectedSpan?.id === span.id;
            const style = getSpanStyle(span.name, span.status_code);
            const Icon = style.icon;
            const isChild = Boolean(span.parent_span_id);

            return (
              <div
                key={span.id}
                onClick={() => setSelectedSpanId(span.id)}
                className={`grid grid-cols-12 px-4 py-2 items-center gap-2 cursor-pointer transition-colors ${
                  isSelected
                    ? "bg-primary/5 dark:bg-primary/10 border-l-3 border-l-primary"
                    : "hover:bg-muted/40"
                }`}
              >
                {/* Span Identity & Indent */}
                <div className="col-span-5 md:col-span-4 flex items-center gap-2 min-w-0 pr-2">
                  <div
                    className="flex items-center gap-1.5 min-w-0"
                    style={{ paddingLeft: isChild ? "1rem" : "0" }}
                  >
                    {isChild && <ChevronRight className="w-3 h-3 text-muted-foreground/60 shrink-0" />}
                    <Icon className="w-3.5 h-3.5 shrink-0 text-muted-foreground" />
                    <span className="font-mono text-xs font-semibold truncate text-foreground" title={span.name}>
                      {span.name}
                    </span>
                  </div>
                </div>

                {/* Duration Bar */}
                <div className="col-span-7 md:col-span-8 relative h-6 flex items-center">
                  <div className="w-full h-2 rounded bg-muted/40 relative">
                    <div
                      className={`absolute h-full rounded transition-all ${style.bg}`}
                      style={{
                        left: `${leftPercent}%`,
                        width: `${widthPercent}%`,
                        minWidth: "6px",
                      }}
                      title={`${span.name}: ${durationMs.toFixed(1)}ms`}
                    />
                  </div>
                  <span className="absolute right-0 text-[10px] font-mono text-muted-foreground ml-2">
                    {durationMs.toFixed(1)}ms
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Span Inspector Drawer */}
      {selectedSpan && (
        <div className="gh-bento space-y-3.5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10 text-primary">
                <Code2 className="w-3.5 h-3.5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-foreground font-mono">
                  {selectedSpan.name}
                </h4>
                <p className="text-[10px] font-mono text-muted-foreground">
                  ID: {selectedSpan.id} {selectedSpan.parent_span_id ? `| Parent: ${selectedSpan.parent_span_id}` : "(Root Span)"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-muted text-foreground border border-border">
                {selectedSpan.duration_ms?.toFixed(2) ?? "0.00"} ms
              </span>
              <span
                className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  selectedSpan.status_code === "OK" || selectedSpan.status_code === "1"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                    : "bg-destructive/10 text-destructive border border-destructive/20"
                }`}
              >
                {selectedSpan.status_code === "OK" || selectedSpan.status_code === "1" ? "Status: OK" : "Status: Error"}
              </span>
            </div>
          </div>

          {/* Attributes Grid */}
          <div>
            <h5 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Span Attributes
            </h5>
            {Object.keys(selectedSpan.attributes || {}).length > 0 ? (
              <div className="gh-box divide-y divide-border/40 font-mono text-xs">
                {Object.entries(selectedSpan.attributes).map(([key, val]) => (
                  <div key={key} className="grid grid-cols-12 px-3 py-1.5 bg-card hover:bg-muted/30">
                    <span className="col-span-5 md:col-span-4 font-semibold text-foreground truncate pr-2">
                      {key}
                    </span>
                    <span className="col-span-7 md:col-span-8 text-muted-foreground break-all text-[11px]">
                      {typeof val === "object" ? JSON.stringify(val) : String(val)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic">No custom attributes attached.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
