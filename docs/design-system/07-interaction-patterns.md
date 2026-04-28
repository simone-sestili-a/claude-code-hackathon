# Interaction Patterns

## Theme Toggle

The theme toggle lives in the header (top-right). It cycles through three states: **System → Light → Dark**.

```tsx
import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'

const icons = { system: Monitor, light: Sun, dark: Moon }
const labels = { system: 'System theme', light: 'Light mode', dark: 'Dark mode' }
const next = { system: 'light', light: 'dark', dark: 'system' } as const

export function ThemeToggle() {
  const { theme, applyTheme } = useTheme()
  const Icon = icons[theme]

  return (
    <button
      onClick={() => applyTheme(next[theme])}
      aria-label={`Current: ${labels[theme]}. Click to switch.`}
      className="p-2 rounded-md cursor-pointer
        text-text-muted hover:text-text-primary
        hover:bg-bg-overlay transition-colors duration-150
        focus-visible:ring-2 focus-visible:ring-brand"
    >
      <Icon size={16} aria-hidden />
    </button>
  )
}
```

**Placement:** header right side, before user avatar.  
**Transition:** the entire page switches theme in `150ms` (all surface tokens change via CSS vars simultaneously — no flash, no reflow).  
**Persistence:** `localStorage` key `'theme'`. Cleared (not set to `'system'`) when system mode is selected, so future OS changes are respected automatically.

---

## Animation Tokens

| Token | Duration | Easing | Use |
|-------|----------|--------|-----|
| `transition-fast` | 150ms | `ease` | Color changes, icon swaps |
| `transition-base` | 200ms | `ease` | Hover states, badge updates |
| `transition-slow` | 300ms | `ease` | Panel slides, modal fade |
| `transition-collapse`| 250ms | `ease-in-out` | Sidebar collapse |

**Rule:** Use `transform` and `opacity` only — never animate `width`, `height`, `top`, or `margin` (causes layout recalculation).

```css
/* Good */
.panel-enter { transform: translateX(100%); opacity: 0; }
.panel-enter-active { transform: translateX(0); opacity: 1; transition: all 300ms ease; }

/* Bad */
.panel-enter { width: 0; }
.panel-enter-active { width: 384px; transition: width 300ms; }
```

## Hover States

Every interactive element provides visual feedback within 150ms.

### Ticket Card

```tsx
// Resting → Hovered
border-border-subtle → border-border-strong
bg-bg-raised → bg-bg-overlay
// No scale transform — data cards must not shift layout
```

### Action Buttons

```tsx
// Primary (brand)
bg-brand → bg-brand-hover   (150ms)

// Secondary
bg-bg-overlay border-border-subtle → border-border-strong   (150ms)

// Danger
bg-[#450A0A] → bg-[#7F1D1D]   (150ms)

// Ghost
transparent → bg-bg-overlay   (150ms)
```

### Navigation Items (Sidebar)

```tsx
// Resting: text-slate-400
// Hovered: text-slate-50 + bg-bg-overlay (rounded-md)
// Active:  text-brand + bg-brand-subtle (rounded-md)
```

## Active / Selected States

When a ticket is selected (detail panel open):

```tsx
// Ticket card in list
ring-2 ring-brand ring-offset-2 ring-offset-bg-base bg-bg-overlay
```

When a sidebar item is active:

```tsx
text-brand bg-brand-subtle font-semibold
```

## Loading States

### Skeleton Screens

Use skeleton loading instead of spinners for list views. This prevents content jump.

```tsx
export function TicketCardSkeleton() {
  return (
    <div className="flex flex-col gap-2 p-4 rounded-lg bg-bg-raised border border-border-subtle animate-pulse">
      <div className="flex items-center gap-2">
        <div className="h-5 w-8 rounded-full bg-bg-muted" />     {/* badge */}
        <div className="h-4 w-24 rounded bg-bg-muted" />          {/* ID */}
        <div className="h-4 flex-1 rounded bg-bg-muted" />        {/* title */}
        <div className="h-5 w-20 rounded-md bg-bg-muted" />       {/* category */}
      </div>
      <div className="flex justify-between">
        <div className="h-3 w-40 rounded bg-bg-muted" />
        <div className="h-3 w-24 rounded bg-bg-muted" />
      </div>
    </div>
  )
}
```

### Button Loading

Disable during async; show spinner; preserve width to prevent layout shift:

```tsx
<button
  disabled={isPending}
  className={cn(
    'min-w-[120px] flex items-center justify-center gap-2',
    isPending && 'cursor-not-allowed opacity-70',
  )}
>
  {isPending ? <Loader2 size={14} className="animate-spin" aria-hidden /> : <AlertTriangle size={14} aria-hidden />}
  {isPending ? 'Escalating…' : 'Escalate'}
</button>
```

### Chart Loading

```tsx
<div className="h-48 flex items-center justify-center bg-bg-raised rounded-lg border border-border-subtle">
  <div className="flex flex-col items-center gap-2 text-slate-600">
    <Loader2 size={20} className="animate-spin" />
    <span className="font-mono text-caption">Loading metrics…</span>
  </div>
</div>
```

## Real-Time Updates

### Polling Strategy

```tsx
// React Query polling for ticket list
const { data } = useQuery({
  queryKey: ['tickets', filters],
  queryFn: fetchTickets,
  refetchInterval: 5_000,        // 5s for list
  refetchIntervalInBackground: true,
})

// Agent feed — shorter interval
const { data: feed } = useQuery({
  queryKey: ['agent-feed'],
  queryFn: fetchAgentFeed,
  refetchInterval: 2_000,        // 2s for activity
})
```

### New Ticket Flash

When a new ticket arrives, briefly highlight the new card:

```css
@keyframes ticket-enter {
  from { background-color: rgba(34,197,94,0.15); }
  to   { background-color: transparent; }
}

.ticket-new {
  animation: ticket-enter 1.5s ease-out forwards;
}
```

```tsx
// Apply 'ticket-new' class for 1.5s after ticket appears in list
const isNew = Date.now() - new Date(ticket.createdAt).getTime() < 5_000
```

### Live Indicator

```tsx
export function LiveIndicator() {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-caption text-brand">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand opacity-60" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-brand" />
      </span>
      LIVE
    </span>
  )
}
```

## Confirmation Dialogs

Required for destructive or irreversible actions: Escalate, Close (P1 is blocked entirely), Bulk operations.

```tsx
// Pattern: inline confirmation (no modal for speed)
// Step 1: click "Escalate" → button changes to confirm prompt
// Step 2: user clicks "Confirm escalation" within 5s, or action cancels

<div className="flex items-center gap-2">
  {confirming ? (
    <>
      <span className="font-sans text-body-sm text-slate-300">Escalate to human?</span>
      <button onClick={confirmEscalate} className="text-red-400 hover:text-red-300 cursor-pointer">
        Confirm
      </button>
      <button onClick={() => setConfirming(false)} className="text-slate-500 hover:text-slate-300 cursor-pointer">
        Cancel
      </button>
    </>
  ) : (
    <button onClick={() => setConfirming(true)} className="...">Escalate</button>
  )}
</div>
```

## Error Feedback

### Inline Errors (Forms)

```tsx
// Error appears immediately below the failing field
<div className="flex flex-col gap-1">
  <label htmlFor="user-id" className="font-sans text-label text-slate-400">User ID</label>
  <input id="user-id" className={cn('...', error && 'border-red-500 focus:ring-red-500')} />
  {error && (
    <p role="alert" className="font-sans text-caption text-red-400 flex items-center gap-1">
      <AlertCircle size={11} aria-hidden /> {error}
    </p>
  )}
</div>
```

### API Errors (Toast)

All API failures surface as a toast with:
- Error type (short)
- Ticket ID if relevant
- Retry action if applicable

```tsx
toast.error(`Failed to escalate ${ticket.id}`, {
  description: 'Network timeout — please retry',
  action: { label: 'Retry', onClick: retryEscalate },
  duration: 8_000,
})
```

## Empty States

Data-less views need contextual empty states, not blank space.

```tsx
export function EmptyTicketList({ filter }: { filter: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
      <CheckCircle size={40} className="text-slate-700" aria-hidden />
      <div>
        <p className="font-mono text-heading-sm text-slate-400">No tickets matching "{filter}"</p>
        <p className="font-sans text-body-sm text-slate-600 mt-1">Try adjusting your filters.</p>
      </div>
      <button onClick={clearFilters} className="font-sans text-body-sm text-brand hover:text-brand-hover cursor-pointer transition-colors">
        Clear filters
      </button>
    </div>
  )
}
```

## Drag & Drop (Ticket Triage Queue)

If implemented, use `@dnd-kit/core`. Keyboard drag must be supported:
- `Space` to pick up
- Arrow keys to reorder
- `Space` to drop
- `Escape` to cancel

Drag ghost: semi-transparent card (`opacity-80`) with `shadow-glow-p1` if P1.
