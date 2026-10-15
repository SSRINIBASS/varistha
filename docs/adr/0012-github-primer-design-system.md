# ADR 0012: GitHub Primer UI/UX Design System & Theme Engine

## Status
Accepted

## Context
Varistha is designed as an open-source, self-hostable control plane for AI agents (AI employees) targeted at engineering teams and startups (`docs/SPEC.md § 4.4`). The initial MVP UI was functional but lacked visual depth, constrained widescreen monitors to artificial `max-w-7xl` containers, lacked dark/light theme switching, and did not leverage established conventions familiar to developers.

Engineering and DevOps teams spend significant time in GitHub and GitHub Actions. Adopting GitHub's Primer design language and Bento architecture establishes immediate visual fluency, ergonomic navigation, and high information density.

## Decisions

### 1. Full-Span Fluid Layout
- Eliminated artificial max-width constraints (`max-w-7xl`) across `layout.tsx` and all top-level views.
- Adopted fluid full-width responsive gutters (`w-full px-4 sm:px-6 lg:px-8 py-5`) allowing widescreen monitors (1920x1080 and larger) to span the 6-stage lifecycle Kanban columns without horizontal compression or unnecessary scrolling.

### 2. GitHub Primer Design Tokens & Theme Engine
Implemented official GitHub Primer color variables and semantic design tokens:
- **Light Theme**: Canvas (`#ffffff`), Canvas Subtle (`#f6f8fa`), Border Default (`#d0d7de`), Text Primary (`#1f2328`), Text Muted (`#656d76`), Primer Green (`#1f883d`), Primer Blue Link (`#0969da`), Danger Red (`#cf222e`).
- **Dark Theme**: Canvas (`#0d1117`), Dark Box Canvas (`#161b22`), Header Inset (`#010409`), Border Default (`#30363d`), Text Primary (`#f0f6fc`), Text Muted (`#8b949e`), Dark Primer Green (`#238636`), Dark Primer Blue (`#58a6ff`), Dark Danger (`#f85149`).
- **Typography**: Native GitHub font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif`) with `ui-monospace` for identifiers, versions, tokens, and payloads.
- **Atmospheric Gradient**: Radial background glow (`radial-gradient(ellipse at 50% -20%, ...)`).
- **Shadows**: Primer multi-layer elevation system (`--shadow-resting`, `--shadow-card`, `--shadow-bento`, `--shadow-floating`).

### 3. Theme Toggle & FOUC Prevention
- Implemented a unified `ThemeProvider` supporting `light`, `dark`, and `system` preferences.
- Utilized React 19's `useSyncExternalStore` for flicker-free OS media query synchronization and persistent `localStorage` (`varistha-theme`).
- Added an inline anti-FOUC (Flash of Unstyled Content) script in `<head>` that parses `localStorage` or `window.matchMedia` prior to DOM rendering.
- Built `ThemeToggle` with GitHub `ActionMenu` dropdown styling, active checkmarks, and outside-click dismissal.

### 4. Bento & Component Architecture
Created reusable GitHub Primer component utilities in `globals.css`:
- `.gh-box`: Classic GitHub container with header (`.gh-box-header`) and bordered rows (`.gh-box-row`).
- `.gh-bento` & `.gh-bento-hero`: Elevated card with hover border illumination.
- `.gh-counter`: Counter pill for tabs, filters, and stage statistics.
- `.gh-btn-primary`, `.gh-btn-secondary`, `.gh-btn-danger`, `.gh-btn-subtle`: Authentic GitHub button hierarchy with active scale micro-interactions.
- `.gh-tab`, `.gh-tab-active`: GitHub UnderlineNav with signature coral active indicator (`#fd8c73` dark / `#f78166` light).
- `.gh-diff-add`, `.gh-diff-delete`: GitHub Pull Request diff row highlighting.

### 5. Verification & Safety
- Maintained 100% backward compatibility and interaction stability across all views (Lifecycle Kanban, Agents Table, Spec Diff Viewer, Stage Promotion Modal, Trace Waterfall).
- Vitest suite (23 tests) and ESLint strict passing with zero errors.

## Consequences
- Standardized UI pattern language across all existing and upcoming modules.
- Developers familiar with GitHub navigate agent lifecycles, diffs, and telemetry with zero learning curve.
