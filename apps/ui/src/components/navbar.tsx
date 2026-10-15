"use client";

/**
 * Global Navigation Header.
 * Displays brand, navigation links, and real-time API connection status.
 */

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, Activity } from "lucide-react";
import { checkHealth } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    checkHealth()
      .then((res) => {
        if (mounted) setApiOnline(res.status === "healthy");
      })
      .catch(() => {
        if (mounted) setApiOnline(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const navItems = [
    { label: "Agents", href: "/agents", icon: Bot },
    { label: "Runs", href: "/runs", icon: Activity },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/80 bg-background/95 backdrop-blur-sm">
      <div className="container mx-auto max-w-7xl px-4 sm:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/agents" className="flex items-center gap-2.5 font-bold tracking-tight text-foreground hover:opacity-90">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground shadow-xs">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-base font-extrabold tracking-wider">VARISTHA</span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground px-1.5 py-0.5 rounded bg-muted">
                Control Plane
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href ||
                (item.href === "/agents" && (pathname === "/" || pathname?.startsWith("/agents")));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-secondary text-secondary-foreground font-semibold"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {/* API Health Pill */}
          <div
            title={
              apiOnline === true
                ? "Varistha API connected"
                : apiOnline === false
                ? "Varistha API offline"
                : "Checking API connection..."
            }
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border border-border bg-card shadow-xs"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                apiOnline === true
                  ? "bg-emerald-500 shadow-sm shadow-emerald-500/50 animate-pulse"
                  : apiOnline === false
                  ? "bg-rose-500"
                  : "bg-amber-400"
              }`}
            />
            <span className="text-muted-foreground text-[11px]">
              {apiOnline === true
                ? "API Online"
                : apiOnline === false
                ? "API Offline"
                : "Connecting..."}
            </span>
          </div>

          <a
            href="https://github.com/amydgylla/varistha"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            title="GitHub Repository"
          >
            <svg
              className="w-4 h-4 fill-current"
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
        </div>
      </div>
    </header>
  );
}
