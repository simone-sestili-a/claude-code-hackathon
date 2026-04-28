# Component Library

All components are React + TypeScript. Import icons from `lucide-react`. Never use emojis as icons.

---

## 1. Priority Badge

Displays P1–P4 with color-coded pill. Always paired with text label for accessibility.

```tsx
import { cn } from '@/lib/utils'

type Priority = 'P1' | 'P2' | 'P3' | 'P4'

const priorityConfig: Record<Priority, { bg: string; text: string; label: string }> = {
  P1: { bg: 'bg-[#450A0A]', text: 'text-[#DC2626]', label: 'Critical' },
  P2: { bg: 'bg-[#431407]', text: 'text-[#EA580C]', label: 'High' },
  P3: { bg: 'bg-[#422006]', text: 'text-[#CA8A04]', label: 'Medium' },
  P4: { bg: 'bg-[#052E16]', text: 'text-[#16A34A]', label: 'Low' },
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  const cfg = priorityConfig[priority]
  return (
    <span
      role="img"
      aria-label={`Priority ${priority} — ${cfg.label}`}
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full',
        'font-sans text-label uppercase tracking-widest',
        cfg.bg, cfg.text,
      )}
    >
      {priority}
    </span>
  )
}
```

**Variants:** badge only (list view) · badge + label (expanded view) · icon only (mobile)

---

## 2. Category Chip

```tsx
import { Network, ShieldAlert, HardDrive, Code2, KeyRound, HelpCircle } from 'lucide-react'

type Category = 'VPN' | 'SECURITY' | 'HARDWARE' | 'SOFTWARE' | 'ACCESS' | 'OTHER'

const categoryConfig: Record<Category, { icon: React.ElementType; color: string }> = {
  VPN:      { icon: Network,     color: 'text-cyan-500' },
  SECURITY: { icon: ShieldAlert, color: 'text-amber-500' },
  HARDWARE: { icon: HardDrive,   color: 'text-violet-500' },
  SOFTWARE: { icon: Code2,       color: 'text-sky-500' },
  ACCESS:   { icon: KeyRound,    color: 'text-teal-500' },
  OTHER:    { icon: HelpCircle,  color: 'text-slate-400' },
}

export function CategoryChip({ category }: { category: Category }) {
  const { icon: Icon, color } = categoryConfig[category]
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1
      rounded-md bg-bg-overlay text-body-sm font-sans text-slate-300
      border border-border-subtle">
      <Icon size={12} className={color} aria-hidden />
      {category}
    </span>
  )
}
```

---

## 3. Ticket Card

The primary list item. Collapsed by default; expands inline on click.

### Anatomy

```
┌─────────────────────────────────────────────────────────────────────┐
│ [P1 badge] [#TKT-00423]  VPN down — Singapore office    [SECURITY▼] │
│ ──────────────────────────────────────────────────────────────────── │
│ u001 · john.smith@corp   IN_PROGRESS · Agent: coordinator-01        │
│                                    Assigned: Network Team · 14m ago │
└─────────────────────────────────────────────────────────────────────┘
```

```tsx
interface Ticket {
  id: string
  priority: Priority
  category: Category
  title: string
  userId: string
  userEmail: string
  status: TicketStatus
  agentId?: string
  assignedTeam?: string
  createdAt: string
  frozen: boolean
}

export function TicketCard({ ticket, onClick }: { ticket: Ticket; onClick: () => void }) {
  return (
    <article
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      aria-label={`Ticket ${ticket.id}: ${ticket.title}`}
      className={cn(
        'group flex flex-col gap-2 p-4 rounded-lg cursor-pointer',
        'bg-bg-raised border border-border-subtle',
        'transition-all duration-200',
        'hover:border-border-strong hover:bg-bg-overlay',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
        ticket.priority === 'P1' && 'ring-1 ring-priority-p1 animate-pulse-critical',
        ticket.priority === 'P2' && 'ring-1 ring-priority-p2',
        ticket.frozen && 'opacity-60 grayscale-[40%] cursor-not-allowed',
      )}
    >
      {ticket.frozen && <FrozenBanner />}

      {/* Top row */}
      <div className="flex items-center gap-2 min-w-0">
        <PriorityBadge priority={ticket.priority} />
        <span className="font-mono text-mono-sm text-slate-500 shrink-0">{ticket.id}</span>
        <span className="font-sans text-body-md text-slate-50 truncate flex-1">{ticket.title}</span>
        <CategoryChip category={ticket.category} />
      </div>

      {/* Bottom row */}
      <div className="flex items-center justify-between gap-4 text-caption text-slate-500 font-mono">
        <span>{ticket.userId} · {ticket.userEmail}</span>
        <div className="flex items-center gap-3">
          <StatusBadge status={ticket.status} />
          <RelativeTime iso={ticket.createdAt} />
        </div>
      </div>
    </article>
  )
}
```

### Expanded State

When a ticket is selected, it expands in a side panel (not inline):

```
┌────────────────────────────────┐
│  Ticket Detail Panel (w-96)    │
│  Slides in from right          │
│  ──────────────────────────    │
│  Full description              │
│  Agent decision trail          │
│  Action buttons (if !FROZEN)   │
│  Related audit entries         │
└────────────────────────────────┘
```

---

## 4. Status Badge

```tsx
type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'ESCALATED' | 'FROZEN'

const statusConfig: Record<TicketStatus, { color: string; label: string }> = {
  OPEN:        { color: 'text-status-open',        label: 'Open' },
  IN_PROGRESS: { color: 'text-status-in-progress', label: 'In Progress' },
  RESOLVED:    { color: 'text-status-resolved',    label: 'Resolved' },
  ESCALATED:   { color: 'text-status-escalated',   label: 'Escalated' },
  FROZEN:      { color: 'text-status-frozen',      label: 'Frozen' },
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  const { color, label } = statusConfig[status]
  return (
    <span className={cn('font-mono text-mono-sm', color)}>
      ● {label}
    </span>
  )
}
```

---

## 5. Frozen Banner

Shown at top of any FROZEN account ticket. Blocks all CTA visibility.

```tsx
import { Lock } from 'lucide-react'

export function FrozenBanner() {
  return (
    <div role="alert" className="flex items-center gap-2 px-3 py-2 rounded-md
      bg-slate-800 border border-slate-600 text-slate-400 text-body-sm font-sans">
      <Lock size={14} aria-hidden />
      <span>Account frozen — actions disabled. Contact account management.</span>
    </div>
  )
}
```

---

## 6. Metric Card

For the top metrics bar (Open, P1 count, Avg SLA, etc.)

```tsx
interface MetricCardProps {
  label: string
  value: string | number
  delta?: string      // e.g. "+12%" or "-3 min"
  trend?: 'up' | 'down' | 'flat'
  accentColor?: string
}

export function MetricCard({ label, value, delta, trend, accentColor }: MetricCardProps) {
  return (
    <div className="bg-bg-raised border border-border-subtle rounded-lg p-4
      flex flex-col gap-1 min-h-[100px]">
      <span className="font-sans text-label uppercase tracking-widest text-slate-500">
        {label}
      </span>
      <span className={cn(
        'font-mono text-heading-lg text-slate-50',
        accentColor,
      )}>
        {value}
      </span>
      {delta && (
        <span className={cn(
          'font-mono text-caption',
          trend === 'up' ? 'text-red-400' : 'text-green-400',
        )}>
          {delta}
        </span>
      )}
    </div>
  )
}
```

**Metric cards for this dashboard:**

| Label | Value source | Accent | Alert when |
|-------|-------------|--------|-----------|
| Open Tickets | `tickets.filter(open)` | none | > 50 |
| P1 Active | `tickets.filter(p1,open)` | `text-priority-p1` | > 0 |
| P2 Active | `tickets.filter(p2,open)` | `text-priority-p2` | > 10 |
| Avg SLA (min) | rolling 1h average | none | > 120 |
| Resolved Today | count | `text-brand` | — |
| Escalated | count | `text-status-escalated` | > 5 |

---

## 7. Agent Activity Feed

Real-time stream of agent decisions. Newest entry at top. Max visible: 50 (virtual scroll).

```tsx
interface AgentEvent {
  id: string
  timestamp: string
  agentId: string
  action: 'CLASSIFY' | 'ROUTE' | 'ESCALATE' | 'DRAFT_REPLY' | 'CLOSE' | 'ENRICH'
  ticketId: string
  summary: string
  metadata?: Record<string, unknown>
}

const actionColors: Record<AgentEvent['action'], string> = {
  CLASSIFY:    'text-sky-400',
  ROUTE:       'text-violet-400',
  ESCALATE:    'text-red-400',
  DRAFT_REPLY: 'text-emerald-400',
  CLOSE:       'text-slate-400',
  ENRICH:      'text-cyan-400',
}

export function AgentFeedItem({ event }: { event: AgentEvent }) {
  return (
    <div className="flex gap-3 py-2.5 border-b border-border-subtle
      hover:bg-bg-overlay transition-colors duration-150 px-4">
      <time className="font-mono text-mono-sm text-slate-500 shrink-0 pt-0.5">
        {formatTime(event.timestamp)}
      </time>
      <div className="flex flex-col gap-0.5 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn('font-mono text-mono-sm font-semibold', actionColors[event.action])}>
            {event.action}
          </span>
          <span className="font-mono text-mono-sm text-slate-500">{event.ticketId}</span>
          <span className="font-mono text-caption text-slate-600">{event.agentId}</span>
        </div>
        <p className="font-sans text-body-sm text-slate-300 truncate">{event.summary}</p>
      </div>
    </div>
  )
}
```

---

## 8. Audit Log

Full immutable event trail. Monospace throughout; designed for forensic readability.

```tsx
interface AuditEntry {
  id: string
  timestamp: string
  actor: 'AGENT' | 'HUMAN' | 'SYSTEM' | 'HOOK'
  event: string
  ticketId?: string
  userId?: string
  payload?: Record<string, unknown>
}

export function AuditLogRow({ entry }: { entry: AuditEntry }) {
  return (
    <tr className="border-b border-border-subtle hover:bg-bg-overlay
      transition-colors duration-100 font-mono text-mono-sm">
      <td className="px-4 py-2 text-slate-500 whitespace-nowrap">{entry.timestamp}</td>
      <td className="px-4 py-2">
        <ActorBadge actor={entry.actor} />
      </td>
      <td className="px-4 py-2 text-slate-300">{entry.event}</td>
      <td className="px-4 py-2 text-slate-500">{entry.ticketId ?? '—'}</td>
      <td className="px-4 py-2">
        {entry.payload && (
          <button className="text-brand hover:text-brand-hover transition-colors cursor-pointer text-caption">
            view payload
          </button>
        )}
      </td>
    </tr>
  )
}
```

---

## 9. Routing View

Shows the coordinator decision: which team/subagent received the ticket.

```tsx
// Visual routing path
┌─────────────────────────────────────────────────────┐
│ Coordinator → [Classifier] → [Enricher] → Network   │
│                                          Team ✓     │
└─────────────────────────────────────────────────────┘
```

```tsx
interface RoutingStep {
  agent: string
  status: 'pending' | 'complete' | 'failed'
  durationMs?: number
}

export function RoutingPath({ steps, destination }: { steps: RoutingStep[]; destination: string }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {steps.map((step, i) => (
        <React.Fragment key={step.agent}>
          <RoutingNode step={step} />
          {i < steps.length - 1 && (
            <ChevronRight size={12} className="text-slate-600" aria-hidden />
          )}
        </React.Fragment>
      ))}
      <ChevronRight size={12} className="text-slate-600" aria-hidden />
      <span className="font-mono text-mono-sm text-brand">{destination}</span>
    </div>
  )
}
```

---

## 10. Action Buttons

Primary actions within a ticket detail panel. All disabled when `ticket.frozen === true`.

| Action | Icon | Variant | Condition |
|--------|------|---------|-----------|
| Escalate | `AlertTriangle` | Danger | status !== ESCALATED |
| Assign | `UserPlus` | Secondary | status === OPEN |
| Draft Reply | `Mail` | Secondary | always |
| Close | `CheckCircle` | Ghost | priority !== P1, category !== SECURITY |
| View Audit | `ScrollText` | Ghost | always |

```tsx
export function TicketActions({ ticket }: { ticket: Ticket }) {
  if (ticket.frozen) return null

  return (
    <div className="flex flex-wrap gap-2">
      <Button variant="danger" icon={AlertTriangle} disabled={ticket.status === 'ESCALATED'}>
        Escalate
      </Button>
      <Button variant="secondary" icon={Mail}>Draft Reply</Button>
      {ticket.priority !== 'P1' && ticket.category !== 'SECURITY' && (
        <Button variant="ghost" icon={CheckCircle}>Close</Button>
      )}
    </div>
  )
}
```

---

## 11. Toast Notifications

System feedback for agent actions. Auto-dismiss in 5s. Positioned top-right, stacked.

```tsx
type ToastVariant = 'success' | 'error' | 'warning' | 'info'

// Position: fixed top-4 right-4, z-toast (60)
// Max stack: 5 toasts
// Animation: slide in from right (200ms), fade out (150ms)
// Sound: optional (respect prefers-reduced-motion)
```

| Variant | bg | Icon |
|---------|-----|------|
| success | `#14532D` border `#16A34A` | `CheckCircle` green |
| error | `#450A0A` border `#DC2626` | `XCircle` red |
| warning | `#422006` border `#CA8A04` | `AlertTriangle` yellow |
| info | `#0C1A33` border `#3B82F6` | `Info` blue |
