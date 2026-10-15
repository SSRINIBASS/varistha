"use client";

/**
 * GitHub Primer-styled JSON payload diff viewer for human-in-the-loop approvals.
 */

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

interface PayloadDiffViewerProps {
  proposedPayload: Record<string, unknown> | unknown;
  approvedPayload?: Record<string, unknown> | unknown | null;
  className?: string;
}

export function PayloadDiffViewer({
  proposedPayload,
  approvedPayload,
  className = "",
}: PayloadDiffViewerProps) {
  const [copied, setCopied] = useState<"proposed" | "approved" | null>(null);

  const proposedStr = JSON.stringify(proposedPayload, null, 2);
  const approvedStr = approvedPayload
    ? JSON.stringify(approvedPayload, null, 2)
    : proposedStr;

  const handleCopy = (type: "proposed" | "approved", text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  const hasModifications =
    approvedPayload !== undefined &&
    approvedPayload !== null &&
    JSON.stringify(proposedPayload) !== JSON.stringify(approvedPayload);

  return (
    <div className={`space-y-3 ${className}`}>
      {hasModifications ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Proposed Payload (Original) */}
          <div className="rounded-lg border border-border bg-card overflow-hidden shadow-xs">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/40 text-xs font-mono">
              <span className="font-semibold text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                Original (Proposed by Agent)
              </span>
              <button
                type="button"
                onClick={() => handleCopy("proposed", proposedStr)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Copy JSON"
              >
                {copied === "proposed" ? (
                  <Check className="w-3 h-3 text-emerald-500" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
                <span>{copied === "proposed" ? "Copied" : "Copy"}</span>
              </button>
            </div>
            <pre className="p-3 text-xs font-mono text-foreground/90 overflow-x-auto max-h-72 bg-muted/10 leading-relaxed">
              <code>{proposedStr}</code>
            </pre>
          </div>

          {/* Approved / Modified Payload */}
          <div className="rounded-lg border border-border bg-card overflow-hidden shadow-xs">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/40 text-xs font-mono">
              <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Approved / Edited Payload
              </span>
              <button
                type="button"
                onClick={() => handleCopy("approved", approvedStr)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Copy JSON"
              >
                {copied === "approved" ? (
                  <Check className="w-3 h-3 text-emerald-500" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
                <span>{copied === "approved" ? "Copied" : "Copy"}</span>
              </button>
            </div>
            <pre className="p-3 text-xs font-mono text-foreground/90 overflow-x-auto max-h-72 bg-emerald-500/5 dark:bg-emerald-950/10 leading-relaxed">
              <code>{approvedStr}</code>
            </pre>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-card overflow-hidden shadow-xs">
          <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/40 text-xs font-mono">
            <span className="font-semibold text-muted-foreground">Proposed Payload</span>
            <button
              type="button"
              onClick={() => handleCopy("proposed", proposedStr)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Copy JSON"
            >
              {copied === "proposed" ? (
                <Check className="w-3 h-3 text-emerald-500" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
              <span>{copied === "proposed" ? "Copied" : "Copy"}</span>
            </button>
          </div>
          <pre className="p-3 text-xs font-mono text-foreground/90 overflow-x-auto max-h-72 bg-muted/10 leading-relaxed">
            <code>{proposedStr}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
