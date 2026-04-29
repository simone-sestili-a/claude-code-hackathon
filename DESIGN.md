# Design

## Theme

Light mode. Physical scene: an operations clerk at a Milan pension fund office, processing adhesion forms at a well-lit desk during morning hours. She reads dense data all day. The interface must be easy on the eyes, high-contrast, and feel like well-designed office stationery — quality paper, not a glossy tech app.

## Color Strategy

Restrained. One accent color, tinted neutrals throughout.

Accent: deep amber-ochre (oklch 42% 0.145 65). This breaks the financial-blue reflex. The warm amber evokes Italian archival documents, pension forms on cream paper, quality institutional stationery. It is specific to this project — not generic "warm = friendly".

### Palette

```
--color-bg:              oklch(97.5% 0.008 70)   /* warm parchment white */
--color-surface:         oklch(99.5% 0.005 70)   /* near-white for chat/result areas */
--color-sidebar:         oklch(95.0% 0.012 70)   /* slightly warmer for sidebar */
--color-sidebar-active:  oklch(91.0% 0.025 70)   /* active session — background tint only, no border-left */
--color-border:          oklch(88.0% 0.014 70)   /* warm border */
--color-border-subtle:   oklch(92.0% 0.010 70)   /* very subtle separator */

--color-text:            oklch(16.0% 0.018 70)   /* near-black warm */
--color-text-secondary:  oklch(44.0% 0.018 70)   /* warm mid-gray */
--color-text-tertiary:   oklch(62.0% 0.014 70)   /* light warm gray */

--color-accent:          oklch(42.0% 0.145 65)   /* deep amber — primary action, links */
--color-accent-hover:    oklch(35.0% 0.145 65)   /* darker on hover */
--color-accent-fg:       oklch(97.5% 0.008 70)   /* parchment white on accent */
--color-accent-subtle:   oklch(94.0% 0.035 68)   /* light amber — user bubbles, highlights */
--color-accent-muted:    oklch(97.0% 0.018 68)   /* very light amber tint */

--color-success:         oklch(44.0% 0.150 145)  /* forest green */
--color-success-bg:      oklch(95.0% 0.040 145)
--color-warning:         oklch(52.0% 0.160 70)   /* amber — same hue as accent */
--color-warning-bg:      oklch(95.0% 0.045 70)
--color-error:           oklch(48.0% 0.200 25)   /* terracotta red */
--color-error-bg:        oklch(96.0% 0.040 25)
```

## Typography

Single family: Geist Sans (built into Next.js 14 via next/font/google, or system fallback). Clean, modern, technically precise. Not on the reflex-reject list. Weight 400 for body, 500 for labels, 600 for headings.

Scale (rem, fixed — product UI, not fluid):
```
--text-xs:  0.75rem  / 1.1rem
--text-sm:  0.875rem / 1.25rem
--text-base: 1rem    / 1.5rem
--text-lg:  1.125rem / 1.5rem
--text-xl:  1.25rem  / 1.4rem
--text-2xl: 1.5rem   / 1.3rem
```

Ratio: 1.125 between steps (product UI density, not brand display).

Body max-width: 65ch in prose sections. Data areas can be denser.

## Layout

Standard product shell: fixed left sidebar (260px) + main content area. Sidebar collapses on mobile (<768px) via toggle.

Spacing rhythm: sidebar padding 16px, main area 24px, content sections separated by 32-48px vertical space. Tight within data groups (8px), generous between sections.

No container wrappers around chat messages. Messages stretch to the available width minus padding.

## Components

### Button
Primary: accent bg + parchment text. No gradient, no shadow. Hover: darker accent.
Secondary: border + transparent bg. Hover: subtle accent-muted bg.
Destructive: error color.
Height: 36px. Border-radius: 6px. Padding: 0 16px.
Icon buttons: h-10 w-10 (40px) standard, h-9 w-9 (36px) small. Minimum touch target 36px, prefer 40px for primary actions.

### Badge / Confidence indicator
Module confidence: colored number only — no pill badge.
- ≥ 85%: success green text
- 70-84%: warning amber text
- < 70%: error terracotta text

### Separator
1px border-subtle. No decorative lines.

### Skeleton
Animate-pulse. Warm background matching the surface it sits on.

### Chat message bubbles
User: accent-subtle background, left-padded, right-aligned.
Assistant text: transparent background, left-aligned.
Document result: full-width panel with surface bg and border, not a bubble.

### Session sidebar items
Selected: sidebar-active background (background tint). Never a border-left accent stripe.
Text truncated at one line. Date label in tertiary text.

## Motion

150ms ease-out on all state transitions. No page-load choreography. Skeleton states during loading. Fade-in for new messages (opacity 0→1, 150ms).

## Elevation

No box shadows on content surfaces. Use border + background difference for depth. Shadow only on floating dropdowns or popovers (if any).
