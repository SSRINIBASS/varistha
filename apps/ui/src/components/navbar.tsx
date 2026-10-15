"use client";

/**
 * Global Navigation Header.
 * Follows GitHub Primer UI/UX design:
 * - Top header bar with breadcrumb, search/command bar, status indicators, theme toggle.
 * - UnderlineNav with classic GitHub tab icons, counter pills, and coral active indicator.
 */

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Layers,
  Activity,
  ShieldAlert,
  Search,
  Plus,
} from "lucide-react";
import { checkHealth, getAgents, getApprovals } from "@/lib/api";
import { ThemeToggle } from "./theme-toggle";

export function Navbar() {
  const pathname = usePathname();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [agentCount, setAgentCount] = useState<number | null>(null);
  const [pendingCount, setPendingCount] = useState<number | null>(null);

  useEffect(() => {
    let mounted = true;
    checkHealth()
      .then((res) => {
        if (mounted) setApiOnline(res.status === "healthy");
      })
      .catch(() => {
        if (mounted) setApiOnline(false);
      });

    getAgents()
      .then((res) => {
        if (mounted && res?.total !== undefined) {
          setAgentCount(res.total);
        }
      })
      .catch(() => {
        // Fallback silently if agents can't be counted yet
      });

    getApprovals({ status: "pending" })
      .then((res) => {
        if (mounted && res?.total !== undefined) {
          setPendingCount(res.total);
        }
      })
      .catch(() => {
        // Fallback silently
      });

    return () => {
      mounted = false;
    };
  }, []);

  const navItems = [
    {
      label: "Agents",
      href: "/agents",
      icon: Bot,
      counter: agentCount !== null ? String(agentCount) : undefined,
      match: (p: string) => p === "/" || p.startsWith("/agents"),
    },
    {
      label: "Lifecycle",
      href: "/lifecycle",
      icon: Layers,
      counter: "6",
      match: (p: string) => p.startsWith("/lifecycle"),
    },
    {
      label: "Runs",
      href: "/runs",
      icon: Activity,
      match: (p: string) => p.startsWith("/runs"),
    },
    {
      label: "Governance",
      href: "/governance",
      icon: ShieldAlert,
      counter: pendingCount !== null && pendingCount > 0 ? String(pendingCount) : undefined,
      isAlertCounter: pendingCount !== null && pendingCount > 0,
      match: (p: string) => p.startsWith("/governance"),
    },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/95 backdrop-blur-md">
      {/* Primary Top Bar (GitHub Global Header) */}
      <div className="w-full px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
        {/* Left: Octicon logo + Repository breadcrumb */}
        <div className="flex items-center gap-3">
          <Link
            href="/agents"
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs"
            title="Varistha Control Plane"
          >
            <Bot className="w-5 h-5" />
          </Link>

          <div className="flex items-center gap-1.5 text-xs sm:text-sm">
            <Link
              href="/agents"
              className="text-muted-foreground hover:text-foreground font-normal transition-colors"
            >
              varistha
            </Link>
            <span className="text-muted-foreground/60">/</span>
            <Link
              href="/agents"
              className="font-bold text-foreground hover:underline flex items-center gap-1.5"
            >
              <span>control-plane</span>
            </Link>
            <span className="hidden sm:inline-block ml-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border border-border bg-muted/60 text-muted-foreground">
              Public
            </span>
          </div>
        </div>

        {/* Center: GitHub-styled Global Command / Search bar */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-4">
          <div className="w-full relative flex items-center">
            <Search className="w-3.5 h-3.5 absolute left-3 text-muted-foreground" />
            <input
              type="text"
              readOnly
              placeholder="Type / to search agents, runs, traces..."
              onClick={() => {
                const searchEl = document.querySelector<HTMLInputElement>(
                  'input[placeholder*="Search"]'
                );
                if (searchEl) searchEl.focus();
              }}
              className="w-full pl-8 pr-8 py-1.5 rounded-md border border-border bg-muted/40 hover:bg-muted/70 text-xs text-foreground placeholder:text-muted-foreground transition-colors cursor-pointer focus:outline-hidden"
            />
            <kbd className="absolute right-2.5 px-1.5 py-0.5 rounded text-[10px] font-mono border border-border bg-card text-muted-foreground shadow-2xs">
              /
            </kbd>
          </div>
        </div>

        {/* Right: API Health + New Agent + Theme Toggle + GitHub link */}
        <div className="flex items-center gap-2.5">
          {/* API Health Indicator */}
          <div
            title={
              apiOnline === true
                ? "Varistha API connected"
                : apiOnline === false
                ? "Varistha API offline"
                : "Checking API connection..."
            }
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono border border-border bg-muted/30"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                apiOnline === true
                  ? "bg-emerald-500 shadow-xs shadow-emerald-500/50 animate-pulse"
                  : apiOnline === false
                  ? "bg-rose-500"
                  : "bg-amber-400"
              }`}
            />
            <span className="hidden sm:inline text-muted-foreground text-[11px]">
              {apiOnline === true
                ? "API Online"
                : apiOnline === false
                ? "API Offline"
                : "Connecting..."}
            </span>
          </div>

          {/* Primer Theme Toggle */}
          <ThemeToggle />

          {/* GitHub Repo Link */}
          <a
            href="https://github.com/SSRINIBASS/varistha"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center w-7 h-7 rounded-md border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors shadow-xs"
            title="View on GitHub"
          >
            <svg
              className="w-3.5 h-3.5 fill-current"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
          </a>

          {/* GitHub Primer Green Action Button */}
          <Link
            href="/lifecycle"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:brightness-110 font-medium text-xs transition-all shadow-xs"
            title="Manage Agent Lifecycle"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="font-semibold">New</span>
          </Link>
        </div>
      </div>

      {/* GitHub UnderlineNav (Sub-navigation tabs) */}
      <div className="w-full px-4 sm:px-6 lg:px-8 border-t border-border/60 bg-muted/20">
        <nav
          className="flex items-center gap-1 overflow-x-auto -mb-px text-xs font-medium"
          aria-label="Varistha navigation tabs"
        >
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.match(pathname || "");

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3.5 py-2.5 border-b-2 transition-all whitespace-nowrap ${
                  isActive
                    ? "border-[#fd8c73] dark:border-[#f78166] text-foreground font-semibold"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? "text-foreground" : "text-muted-foreground"
                  }`}
                />
                <span>{item.label}</span>
                {item.counter && (
                  <span
                    className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-mono font-medium ${
                      item.isAlertCounter
                        ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 font-semibold"
                        : isActive
                        ? "bg-secondary text-secondary-foreground border border-border"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {item.counter}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
