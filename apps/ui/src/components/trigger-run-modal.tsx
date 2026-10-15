"use client";

/**
 * Modal dialog to trigger an execution run for an agent.
 */

import React, { useState } from "react";
import { Play, Loader2, X, Terminal, AlertCircle } from "lucide-react";
import { triggerRun } from "@/lib/api";
import type { Agent } from "@/lib/types";

interface TriggerRunModalProps {
  agent: Agent;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (runId: string) => void;
}

export function TriggerRunModal({
  agent,
  isOpen,
  onClose,
  onSuccess,
}: TriggerRunModalProps) {
  const [inputText, setInputText] = useState<string>("{\n  \"task\": \"Quick qualification task\"\n}");
  const [triggerType, setTriggerType] = useState<string>("manual");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleExecute(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    let parsedInput: Record<string, unknown> = {};
    if (inputText.trim()) {
      try {
        parsedInput = JSON.parse(inputText);
      } catch (err: unknown) {
        setError(
          `Invalid JSON input: ${err instanceof Error ? err.message : "Parse error"}`
        );
        return;
      }
    }

    setLoading(true);
    try {
      const run = await triggerRun(agent.name || agent.id, parsedInput, triggerType);
      onSuccess(run.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to trigger run");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs">
      <div className="gh-modal max-w-lg">
        {/* Header */}
        <div className="gh-box-header px-6 py-3.5">
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 text-primary fill-primary" />
            <div>
              <h3 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
                <span>Run Agent Workflow</span>
                <span className="font-mono text-xs font-normal text-muted-foreground">
                  {agent.name} (v{agent.current_version})
                </span>
              </h3>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="gh-btn-subtle p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="m-4 mb-0 p-3 rounded-md border border-destructive/30 bg-destructive/10 text-destructive text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="flex-1">{error}</span>
          </div>
        )}

        <form onSubmit={handleExecute} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Trigger Type
            </label>
            <select
              value={triggerType}
              onChange={(e) => setTriggerType(e.target.value)}
              className="gh-input w-full"
            >
              <option value="manual">manual (Developer or UI trigger)</option>
              <option value="schedule">schedule (Scheduled Cron trigger)</option>
              <option value="webhook">webhook (External HTTP trigger)</option>
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Input Payload (JSON)
              </label>
              <span className="text-[11px] text-muted-foreground flex items-center gap-1 font-mono">
                <Terminal className="w-3 h-3" /> JSON object
              </span>
            </div>
            <textarea
              rows={5}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={'{\n  "task": "..."\n}'}
              className="gh-input w-full font-mono text-xs resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="gh-btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="gh-btn-primary"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing Run...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Workflow</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
