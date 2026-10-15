/**
 * Reusable Error Alert Component with Retry.
 * Follows SPEC.md § 4.4 design rule: "Every screen has empty, loading, and error states."
 */

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorAlert({
  title = "An error occurred",
  message,
  onRetry,
  className = "",
}: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={`flex items-start gap-3 p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive dark:bg-destructive/15 ${className}`}
    >
      <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
      <div className="flex-1 text-sm">
        <h4 className="font-semibold text-destructive">{title}</h4>
        <p className="mt-1 text-destructive/90">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors cursor-pointer shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    </div>
  );
}
