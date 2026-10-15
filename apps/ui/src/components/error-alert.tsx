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
      className={`flex items-start gap-3 p-3.5 rounded-md border border-destructive/40 bg-destructive/10 text-destructive ${className}`}
    >
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
      <div className="flex-1 text-xs">
        <h4 className="font-bold text-destructive">{title}</h4>
        <p className="mt-1 text-destructive/90 leading-relaxed">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2.5 gh-btn-danger text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    </div>
  );
}
