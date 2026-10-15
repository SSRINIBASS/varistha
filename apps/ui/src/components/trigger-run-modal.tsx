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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="relative w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl text-card-foreground animate-in fade-in zoom-in-95 duration-150">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2.5 mb-1">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
            <Play className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-semibold leading-tight">Trigger Agent Run</h3>
            <p className="text-xs text-muted-foreground">
              Agent: <span className="font-mono font-medium text-foreground">{agent.name}</span> (v{agent.current_version})
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-destructive text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="flex-1">{error}</span>
          </div>
        )}

        <form onSubmit={handleExecute} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Trigger Type
            </label>
            <select
              value={triggerType}
              onChange={(e) => setTriggerType(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring"
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
              className="w-full px-3 py-2 rounded-lg border border-input bg-background font-mono text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/60">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-lg text-xs font-medium border border-border text-foreground hover:bg-muted transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 cursor-pointer shadow-xs"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing Run...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Run Now</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
