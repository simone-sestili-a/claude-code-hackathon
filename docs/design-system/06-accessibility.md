# Accessibility

**Target:** WCAG 2.1 Level AA minimum. Ops teams may rely on keyboard-only workflows during high-volume incidents.

## Contrast Requirements

All text must meet 4.5:1 ratio against its background. Large text (18px+ or 14px bold) minimum 3:1.

| Text | Background | Ratio | Pass |
|------|-----------|-------|------|
| `#F8FAFC` (primary) | `#0F172A` (raised) | 18.3:1 | AAA |
| `#CBD5E1` (secondary) | `#0F172A` | 11.9:1 | AAA |
| `#64748B` (muted) | `#0F172A` | 4.6:1 | AA |
| `#DC2626` (P1) | `#450A0A` (P1 bg) | 5.2:1 | AA |
| `#EA580C` (P2) | `#431407` (P2 bg) | 4.9:1 | AA |
| `#CA8A04` (P3) | `#422006` (P3 bg) | 4.7:1 | AA |
| `#16A34A` (P4) | `#052E16` (P4 bg) | 5.1:1 | AA |
| `#22C55E` (brand) | `#0F172A` | 8.4:1 | AAA |

**Never use `#475569` (slate-600) as readable text** — it fails at 3.2:1 on `bg-raised`.

## Keyboard Navigation

### Tab Order

1. Skip-to-content link (visually hidden until focused)
2. Header: logo → search → notifications → user menu
3. Sidebar: nav items (top to bottom)
4. Main content: filter bar → ticket list → detail panel

```tsx
// Skip link — always first focusable element
<a href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4
    focus:z-toast focus:px-4 focus:py-2 focus:bg-brand focus:text-white
    focus:rounded-md focus:font-sans focus:text-body-md">
  Skip to main content
</a>
```

### Keyboard Shortcuts (Ops Workflow)

| Key | Action |
|-----|--------|
| `j` / `k` | Next / previous ticket in list |
| `Enter` | Open selected ticket detail |
| `Esc` | Close detail panel / dismiss modal |
| `e` | Escalate selected ticket (with confirmation) |
| `r` | Draft reply for selected ticket |
| `/` | Focus search / filter bar |
| `1`–`4` | Filter by priority P1–P4 |

```tsx
// Keyboard shortcut handler — attach to document in layout
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.target instanceof HTMLInputElement) return // don't capture in inputs
    switch (e.key) {
      case 'j': selectNextTicket(); break
      case 'k': selectPrevTicket(); break
      case 'Escape': closeDetailPanel(); break
      case '/': e.preventDefault(); focusSearch(); break
    }
  }
  document.addEventListener('keydown', handler)
  return () => document.removeEventListener('keydown', handler)
}, [])
```

## Focus Management

### Focus Ring

All interactive elements must have visible focus rings. Never `outline-none` without replacement.

```css
/* Global focus style */
:focus-visible {
  outline: 2px solid #22C55E;
  outline-offset: 2px;
  border-radius: 4px;
}
```

Tailwind equivalent: `focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base`

### Focus Trapping

Modals and slide-over panels must trap focus:

```tsx
import { FocusTrap } from '@headlessui/react' // or React Aria

<FocusTrap>
  <div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
    {/* content */}
  </div>
</FocusTrap>
```

When a modal closes, focus must return to the element that triggered it.

### Detail Panel Focus

When a ticket detail panel opens, move focus to the panel heading:

```tsx
const panelHeadingRef = useRef<HTMLHeadingElement>(null)

useEffect(() => {
  if (isOpen) panelHeadingRef.current?.focus()
}, [isOpen])

<h2 ref={panelHeadingRef} tabIndex={-1} className="font-mono text-heading-md text-slate-50">
  {ticket.title}
</h2>
```

## ARIA Patterns

### Ticket List

```tsx
<ul role="list" aria-label="IT tickets">
  {tickets.map(ticket => (
    <li key={ticket.id} role="listitem">
      <TicketCard ticket={ticket} />
    </li>
  ))}
</ul>
```

### Live Feed (Agent Activity)

The agent feed updates in real-time. Use `aria-live` so screen readers announce new entries.

```tsx
<div
  role="log"
  aria-live="polite"
  aria-label="Agent activity feed"
  aria-atomic="false"
>
  {events.map(event => <AgentFeedItem key={event.id} event={event} />)}
</div>
```

Use `aria-live="assertive"` only for P1 alerts — it interrupts the reader immediately.

### Priority Alerts (P1)

```tsx
// P1 tickets entering the queue trigger an assertive announcement
<div role="alert" aria-live="assertive" className="sr-only">
  {newP1Ticket && `Critical P1 ticket ${newP1Ticket.id}: ${newP1Ticket.title}`}
</div>
```

### Audit Log Table

```tsx
<table role="grid" aria-label="Audit log">
  <thead>
    <tr>
      <th scope="col">Timestamp</th>
      <th scope="col">Actor</th>
      <th scope="col">Event</th>
      <th scope="col">Ticket</th>
      <th scope="col">Payload</th>
    </tr>
  </thead>
  <tbody>
    {entries.map(entry => <AuditLogRow key={entry.id} entry={entry} />)}
  </tbody>
</table>
```

### Icon Buttons

All icon-only buttons require `aria-label`:

```tsx
<button aria-label="Close detail panel" className="cursor-pointer ...">
  <X size={16} aria-hidden />
</button>
```

### Status Badges (not color-only)

Every status badge pairs color with text and an accessible label:

```tsx
<span role="img" aria-label="Status: In Progress" className="text-status-in-progress font-mono text-mono-sm">
  ● In Progress
</span>
```

## Motion & Animation

Respect `prefers-reduced-motion` for all animations:

```css
@media (prefers-reduced-motion: reduce) {
  .animate-pulse-critical,
  .animate-pulse,
  .animate-ping,
  .animate-live-dot {
    animation: none;
  }

  * {
    transition-duration: 0.01ms !important;
  }
}
```

```tsx
// React hook for motion preference
function useReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
```

The P1 critical pulse animation must have a **Pause** button in the settings panel for users with vestibular disorders.

## Form Accessibility (Filters / Search)

```tsx
<label htmlFor="ticket-search" className="font-sans text-label text-slate-400 uppercase tracking-wider">
  Search tickets
</label>
<input
  id="ticket-search"
  type="search"
  role="searchbox"
  aria-label="Search tickets by ID, user, or keyword"
  placeholder="TKT-00423, john.smith, VPN..."
  className="..."
/>
```

## Screen Reader Checklist

- [ ] All images have `alt` text (or `alt=""` for decorative)
- [ ] Icon buttons have `aria-label`
- [ ] Ticket cards have `role="button"` + `tabIndex={0}` + `onKeyDown`
- [ ] Live feed has `role="log"` + `aria-live="polite"`
- [ ] P1 alerts use `role="alert"` + `aria-live="assertive"`
- [ ] Modals trap focus and restore on close
- [ ] Skip link present and functional
- [ ] Color is never the sole differentiator (always + text/icon/shape)
- [ ] `prefers-reduced-motion` respected
- [ ] All form inputs have associated `<label>`
