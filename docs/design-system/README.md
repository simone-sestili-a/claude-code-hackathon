# IntakeAI — Design System

**Version:** 1.0 · **Stack:** React 18 + TypeScript + Tailwind CSS v3  
**Style:** Dual-mode (Light / Dark) · Enterprise Admin Dashboard · Bento Grid Layout  
**Default:** system preference (`prefers-color-scheme`) · user toggle persisted in `localStorage`

## Overview

IntakeAI is a data-dense IT helpdesk triage dashboard. The UI must communicate ticket state, agent actions, and routing decisions at a glance — without cognitive overload. Every design decision prioritises **information hierarchy**, **real-time legibility**, and **zero-friction keyboard workflows**.

Both light and dark modes are first-class citizens. The default follows the OS setting; the user can override it via a toggle in the header, persisted across sessions.

## Document Index

| File | Contents |
|------|----------|
| [01-design-tokens.md](./01-design-tokens.md) | CSS custom properties, Tailwind config extension, shadow scale, border radius, z-index |
| [02-typography.md](./02-typography.md) | Font system (Fira Code + Fira Sans), type scale, usage rules |
| [03-color-palette.md](./03-color-palette.md) | Full semantic color system — surfaces, priority, categories, status |
| [04-spacing-layout.md](./04-spacing-layout.md) | 4px base grid, spacing scale, bento grid layout, responsive breakpoints |
| [05-components.md](./05-components.md) | Component specs: ticket card, priority badge, category chip, routing view, agent feed, audit log, metrics |
| [06-accessibility.md](./06-accessibility.md) | WCAG AA requirements, keyboard navigation, ARIA patterns, focus management |
| [07-interaction-patterns.md](./07-interaction-patterns.md) | Animation tokens, loading states, hover/focus/active states, toast notifications |
| [08-data-visualization.md](./08-data-visualization.md) | Chart types, library (Recharts), real-time streaming, metrics cards |

## Design Principles

1. **Signal over noise** — Critical P1 tickets must be impossible to miss.
2. **Density with clarity** — Pack information; never sacrifice scannability.
3. **Deterministic feedback** — Every agent action produces visible, timestamped evidence.
4. **Keyboard-first** — Ops teams triage faster without lifting hands from keyboard.
5. **Frozen is frozen** — FROZEN account status is visually distinct and blocks all CTAs.

## Tech Stack

```
React 18 (TypeScript)
Tailwind CSS v3 — configured per design-tokens
Recharts — real-time streaming charts
Lucide React — SVG icon set
React Query — server state + polling
Zustand — client state (filter, selection)
React Aria / Headless UI — accessible primitives
```

## Quick-Start

```bash
# Install
npm install

# Tailwind config extends design tokens
# See tailwind.config.ts for full token mapping

# Dev server
npm run dev
```

## Priority Reference (at a glance)

| Priority | Color | Hex | Auto-close? | SLA |
|----------|-------|-----|-------------|-----|
| P1 | Critical Red | `#DC2626` | Never | 15 min |
| P2 | High Orange | `#EA580C` | No | 2 h |
| P3 | Medium Yellow | `#CA8A04` | Yes (non-SECURITY) | 8 h |
| P4 | Low Green | `#16A34A` | Yes | 48 h |

## Category Reference

| Category | Icon (Lucide) | Default Priority |
|----------|---------------|-----------------|
| VPN | `Network` | P2 |
| SECURITY | `ShieldAlert` | P1 |
| HARDWARE | `HardDrive` | P3 |
| SOFTWARE | `Code2` | P3 |
| ACCESS | `KeyRound` | P2 |
| OTHER | `HelpCircle` | P4 |
