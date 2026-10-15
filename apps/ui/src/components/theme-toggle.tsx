"use client";

import React, { useState, useRef, useEffect } from "react";
import { Sun, Moon, Laptop, Check } from "lucide-react";
import { useTheme } from "./theme-provider";

export function ThemeToggle() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <button
        type="button"
        onClick={() => setMenuOpen((prev) => !prev)}
        className="flex items-center justify-center w-7 h-7 rounded-md border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors cursor-pointer shadow-xs"
        title={`Theme: ${theme} (Current: ${resolvedTheme})`}
        aria-label="Toggle theme"
      >
        {resolvedTheme === "dark" ? (
          <Moon className="w-3.5 h-3.5 text-blue-400" />
        ) : (
          <Sun className="w-3.5 h-3.5 text-amber-500" />
        )}
      </button>

      {menuOpen && (
        <div className="absolute right-0 mt-1.5 w-36 rounded-md border border-border bg-popover text-popover-foreground shadow-lg py-1 z-50 text-xs animate-in fade-in-50 zoom-in-95">
          <div className="px-2 py-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border mb-1">
            Appearance
          </div>

          <button
            type="button"
            onClick={() => {
              setTheme("light");
              setMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 hover:bg-muted/70 transition-colors text-left cursor-pointer ${
              theme === "light" ? "text-primary font-semibold" : "text-foreground"
            }`}
          >
            <span className="flex items-center gap-2">
              <Sun className="w-3.5 h-3.5 text-amber-500" />
              <span>Light</span>
            </span>
            {theme === "light" && <Check className="w-3.5 h-3.5 text-primary" />}
          </button>

          <button
            type="button"
            onClick={() => {
              setTheme("dark");
              setMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 hover:bg-muted/70 transition-colors text-left cursor-pointer ${
              theme === "dark" ? "text-primary font-semibold" : "text-foreground"
            }`}
          >
            <span className="flex items-center gap-2">
              <Moon className="w-3.5 h-3.5 text-blue-400" />
              <span>Dark</span>
            </span>
            {theme === "dark" && <Check className="w-3.5 h-3.5 text-primary" />}
          </button>

          <button
            type="button"
            onClick={() => {
              setTheme("system");
              setMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 hover:bg-muted/70 transition-colors text-left cursor-pointer ${
              theme === "system" ? "text-primary font-semibold" : "text-foreground"
            }`}
          >
            <span className="flex items-center gap-2">
              <Laptop className="w-3.5 h-3.5 text-muted-foreground" />
              <span>System</span>
            </span>
            {theme === "system" && <Check className="w-3.5 h-3.5 text-primary" />}
          </button>
        </div>
      )}
    </div>
  );
}
