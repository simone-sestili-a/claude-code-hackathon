# Spacing & Layout

## Base Unit

All spacing is multiples of **4px** (Tailwind's default `1` = 0.25rem = 4px).

```
4px  = spacing-1
8px  = spacing-2
12px = spacing-3
16px = spacing-4
20px = spacing-5
24px = spacing-6
32px = spacing-8
40px = spacing-10
48px = spacing-12
64px = spacing-16
```

## Spacing Scale Application

| Context | Value | Tailwind |
|---------|-------|---------|
| Icon–label gap | 8px | `gap-2` |
| Inner card padding | 16px | `p-4` |
| Card–card gap (bento) | 12px | `gap-3` |
| Section vertical gap | 24px | `gap-6` |
| Page horizontal padding | 24px | `px-6` |
| Page top padding (below header) | 80px | `pt-20` |
| Modal padding | 24px | `p-6` |
| Tooltip padding | `6px 10px` | `px-2.5 py-1.5` |
| Badge padding | `2px 8px` | `px-2 py-0.5` |

## Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Header (fixed, h-14, bg-bg-raised, border-b border-border-subtle)│
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                   │
│  Sidebar     │           Main Content Area                      │
│  w-64        │           flex-1, overflow-y-auto                │
│  fixed       │           pt-14 (below header)                   │
│  top-14      │           px-6 py-6                              │
│  bottom-0    │                                                   │
│              │                                                   │
└──────────────┴──────────────────────────────────────────────────┘
```

### Header

```tsx
<header className="fixed top-0 inset-x-0 h-14 z-sticky
  bg-bg-raised border-b border-border-subtle
  flex items-center justify-between px-6">
```

### Sidebar

```tsx
<aside className="fixed left-0 top-14 bottom-0 w-64 z-raised
  bg-bg-raised border-r border-border-subtle
  overflow-y-auto">
```

### Main

```tsx
<main className="ml-64 pt-14 min-h-screen bg-bg-base">
  <div className="px-6 py-6">
    {/* bento grid or list content */}
  </div>
</main>
```

## Bento Grid System

The dashboard uses a **12-column bento grid** with responsive collapsing. Each widget declares its column span; the grid fills gaps automatically.

```tsx
// Base grid container
<div className="grid grid-cols-12 gap-3 auto-rows-auto">
```

### Widget Span Reference

| Widget | Desktop (xl) | Tablet (md) | Mobile |
|--------|-------------|-------------|--------|
| Metrics bar | 12 | 12 | 12 |
| Ticket volume chart | 8 | 12 | 12 |
| Priority breakdown donut | 4 | 6 | 12 |
| Category heatmap | 4 | 6 | 12 |
| Agent activity feed | 8 | 12 | 12 |
| Ticket list panel | 12 | 12 | 12 |
| Audit log | 6 | 12 | 12 |
| SLA tracker | 6 | 12 | 12 |

```tsx
// Example bento cell
<div className="col-span-8 md:col-span-12 xl:col-span-8
  bg-bg-raised rounded-lg border border-border-subtle p-4">
```

### Bento Grid Visual

```
┌────────────────────────────────────────────────────────────┐
│  METRICS (12)                                              │
│  [Open] [P1] [P2] [Avg SLA] [Resolved] [Escalated]        │
├──────────────────────────────┬─────────────────────────────┤
│  VOLUME CHART (8)            │  PRIORITY DONUT (4)         │
│  Streaming area chart        │  P1/P2/P3/P4 breakdown      │
├──────────────┬───────────────┴─────────────────────────────┤
│  CATEGORY (4)│  AGENT ACTIVITY FEED (8)                    │
│  Heatmap     │  Live agent decisions + actions              │
├──────────────┴──────────────────────────────────────────── ┤
│  TICKET LIST (12)                                          │
│  Sortable, filterable, virtualized                         │
├──────────────────────────────┬─────────────────────────────┤
│  AUDIT LOG (6)               │  SLA TRACKER (6)            │
│  Full event trail            │  Breach risk indicators     │
└──────────────────────────────┴─────────────────────────────┘
```

## Responsive Breakpoints

| Breakpoint | Min-width | Target |
|-----------|-----------|--------|
| `sm` | 640px | Tall mobile |
| `md` | 768px | Tablet portrait |
| `lg` | 1024px | Laptop / tablet landscape |
| `xl` | 1280px | Desktop (primary target) |
| `2xl` | 1536px | Wide monitor |

**Primary design target: 1280px–1920px.** The sidebar collapses to icon-only below `lg`. Mobile is supported but de-prioritised (ops teams work at desks).

## Sidebar Collapse (lg breakpoint)

```tsx
// Collapsed: icon-only, w-16
// Expanded: full labels, w-64
<aside className={cn(
  'fixed left-0 top-14 bottom-0 z-raised transition-all duration-300',
  'bg-bg-raised border-r border-border-subtle overflow-hidden',
  collapsed ? 'w-16' : 'w-64',
)}>
```

## Min Heights

| Element | Min height |
|---------|-----------|
| Touch targets (all interactive) | 44px |
| Table rows | 52px |
| Ticket cards (collapsed) | 72px |
| Metric cards | 100px |
| Chart panels | 200px |
| Agent feed | 320px |
