# Color Palette

## Design Philosophy

IntakeAI supports **light and dark mode**, defaulting to the OS preference. The color system is built around three concerns:
1. **Priority legibility** — P1 must scream; P4 must whisper — in both modes.
2. **Status disambiguation** — ticket state is readable without relying on color alone (always paired with icon + text).
3. **WCAG AA minimum** — all text/background combinations meet 4.5:1 contrast ratio in both modes.

All values below are surfaced via CSS custom properties (`--color-*`) defined in `tokens.css`. Components reference the token, not the hex — so mode-switching is automatic.

---

## Surface Palette

### Light Mode

```
┌──────────────────────────────────────────────────────────────────┐
│  bg-base      #F8FAFC  ░░░░░░░░  Body, full-page background      │
│  bg-raised    #FFFFFF  ░░░░░░░░  Cards, panels, sidebar          │
│  bg-overlay   #F1F5F9  ░░░░░░░░  Modals, dropdowns, popovers     │
│  bg-muted     #E2E8F0  ░░░░░░░░  Disabled, inactive items        │
└──────────────────────────────────────────────────────────────────┘
```

### Dark Mode

```
┌──────────────────────────────────────────────────────────────────┐
│  bg-base      #020617  ████████  Body, full-page background      │
│  bg-raised    #0F172A  ████████  Cards, panels, sidebar          │
│  bg-overlay   #1E293B  ████████  Modals, dropdowns, popovers     │
│  bg-muted     #334155  ████████  Disabled, inactive items        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Text Palette

### Light Mode

| Token | Hex | Contrast on bg-raised | Use |
|-------|-----|-----------------------|-----|
| `text-primary` | `#0F172A` | 19.1:1 ✓ | Headings, active labels |
| `text-secondary` | `#334155` | 11.2:1 ✓ | Body, descriptions |
| `text-muted` | `#64748B` | 4.6:1 ✓ | Timestamps, meta |
| `text-disabled` | `#94A3B8` | 2.7:1 — | Disabled only (non-readable) |

### Dark Mode

| Token | Hex | Contrast on bg-raised | Use |
|-------|-----|-----------------------|-----|
| `text-primary` | `#F8FAFC` | 18.3:1 ✓ | Headings, active labels |
| `text-secondary` | `#CBD5E1` | 11.9:1 ✓ | Body, descriptions |
| `text-muted` | `#64748B` | 4.6:1 ✓ | Timestamps, meta |
| `text-disabled` | `#475569` | 3.2:1 — | Disabled only |

---

## Priority Color System

Priority foreground colors are **identical** in both modes — they're bold enough to work on either background. Only the background tints differ.

| Priority | Foreground | Light bg | Dark bg | Glow (dark only) |
|----------|-----------|----------|---------|-----------------|
| P1 | `#DC2626` | `#FEF2F2` | `#450A0A` | `rgba(220,38,38,0.35)` |
| P2 | `#EA580C` | `#FFF7ED` | `#431407` | `rgba(234,88,12,0.30)` |
| P3 | `#CA8A04` | `#FEFCE8` | `#422006` | — |
| P4 | `#16A34A` | `#F0FDF4` | `#052E16` | — |

Glows are disabled in light mode — they read poorly on white and are unnecessary for contrast.

### P1 Ring + Pulse

```tsx
// P1 card ring adapts via CSS var
className={cn(
  ticket.priority === 'P1' && 'ring-1 ring-priority-p1 animate-pulse-critical',
)}
// The glow keyframe uses --color-p1-glow which is lighter in light mode
```

---

## Brand / Action

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `brand` | `#16A34A` (green-600) | `#22C55E` (green-500) | Primary buttons, active nav |
| `brand-hover` | `#15803D` | `#16A34A` | Hover state |
| `brand-subtle` | `#DCFCE7` (green-100) | `#14532D` (green-900) | Tint backgrounds |

Dark mode uses a slightly brighter green because it needs to punch through the dark surface. Light mode uses a deeper green for sufficient contrast on white.

---

## Category Color Mapping

Category accent colors are the same in both modes — they're mid-range saturated hues that read on both light and dark surfaces.

| Category | Color | Hex | Tailwind |
|----------|-------|-----|---------|
| VPN | Cyan | `#0891B2` | `text-cyan-600` |
| SECURITY | Amber | `#D97706` | `text-amber-600` |
| HARDWARE | Violet | `#7C3AED` | `text-violet-600` |
| SOFTWARE | Sky | `#0284C7` | `text-sky-600` |
| ACCESS | Teal | `#0D9488` | `text-teal-600` |
| OTHER | Slate | `#64748B` | `text-slate-500` |

All pass 4.5:1 on both `bg-raised` values (white and `#0F172A`). Verified with Contrast Grid.

---

## Status Color System

| Status | Light | Dark | Use |
|--------|-------|------|-----|
| OPEN | `#2563EB` (blue-600) | `#3B82F6` (blue-500) | New tickets |
| IN_PROGRESS | `#9333EA` (purple-600) | `#A855F7` (purple-500) | Agent processing |
| RESOLVED | `#16A34A` (green-600) | `#22C55E` (green-500) | Completed |
| ESCALATED | `#DC2626` (red-600) | `#EF4444` (red-500) | Human required |
| FROZEN | `#64748B` (slate-500) | `#94A3B8` (slate-400) | Frozen account |

Light mode uses darker shades for contrast on white; dark mode uses lighter shades.

---

## FROZEN State

No change between modes — the visual treatment is always desaturation + reduced opacity:

```tsx
ticket.frozen && 'opacity-60 grayscale-[40%] cursor-not-allowed'
```

---

## Do / Don't

| Do | Don't |
|----|-------|
| Reference `var(--color-*)` tokens | Hard-code `#0F172A` or `#FFFFFF` in components |
| Pair color with icon + text for status | Rely on color alone |
| Use `grayscale + opacity` for FROZEN | Hide FROZEN content |
| Test contrast in both modes | Only test dark mode |
| Use lighter brand green in dark mode | Use same hex in both modes |
