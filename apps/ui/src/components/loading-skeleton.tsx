/**
 * Reusable Loading Skeleton Components.
 * Follows SPEC.md § 4.4 design rule: "Every screen has empty, loading, and error states."
 */

import React from "react";

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export function TableSkeleton({
  rows = 5,
  columns = 5,
  className = "",
}: TableSkeletonProps) {
  return (
    <div
      data-testid="table-skeleton"
      className={`w-full divide-y divide-border/60 border border-border/60 rounded-xl bg-card overflow-hidden ${className}`}
    >
      <div className="bg-muted/40 px-4 py-3 flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <div
            key={`th-${i}`}
            className="h-4 bg-muted animate-pulse rounded flex-1"
          />
        ))}
      </div>
      <div className="divide-y divide-border/40">
        {Array.from({ length: rows }).map((_, r) => (
          <div
            key={`tr-${r}`}
            className="px-4 py-3.5 flex items-center gap-4 bg-card"
          >
            {Array.from({ length: columns }).map((_, c) => (
              <div
                key={`td-${r}-${c}`}
                className="h-4 bg-muted/70 animate-pulse rounded flex-1"
                style={{ width: `${Math.max(40, (c + 1) * 20)}%` }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

interface WaterfallSkeletonProps {
  bars?: number;
  className?: string;
}

export function WaterfallSkeleton({
  bars = 4,
  className = "",
}: WaterfallSkeletonProps) {
  return (
    <div
      data-testid="waterfall-skeleton"
      className={`w-full p-6 space-y-4 border border-border/60 rounded-xl bg-card ${className}`}
    >
      <div className="h-5 w-48 bg-muted animate-pulse rounded mb-6" />
      {Array.from({ length: bars }).map((_, i) => (
        <div key={`wf-bar-${i}`} className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground">
            <div className="h-3 w-28 bg-muted animate-pulse rounded" />
            <div className="h-3 w-16 bg-muted animate-pulse rounded" />
          </div>
          <div className="w-full bg-muted/40 h-6 rounded-md overflow-hidden p-0.5">
            <div
              className="bg-muted animate-pulse h-full rounded"
              style={{
                marginLeft: `${i * 15}%`,
                width: `${Math.max(20, 70 - i * 15)}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
