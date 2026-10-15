/**
 * Reusable Empty State Component.
 * Follows SPEC.md § 4.4 design rule: "Every screen has empty, loading, and error states."
 */

import React from "react";
import { LucideIcon, Inbox } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick?: () => void;
    href?: string;
  };
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`gh-box flex flex-col items-center justify-center text-center p-8 sm:p-12 border-dashed ${className}`}
    >
      <div className="flex items-center justify-center w-12 h-12 rounded-md bg-muted text-muted-foreground mb-3 border border-border">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-bold text-foreground mb-1">{title}</h3>
      <p className="text-xs text-muted-foreground max-w-sm mb-5 leading-relaxed">
        {description}
      </p>
      {action && (
        action.href ? (
          <a
            href={action.href}
            className="gh-btn-primary"
          >
            {action.label}
          </a>
        ) : (
          <button
            type="button"
            onClick={action.onClick}
            className="gh-btn-primary"
          >
            {action.label}
          </button>
        )
      )}
    </div>
  );
}
