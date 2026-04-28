# Data Visualization

## Library: Recharts

All charts use [Recharts](https://recharts.org/) (built on D3, React-first, accessible).

```bash
npm install recharts
```

Recharts renders SVG — all chart elements support ARIA attributes. Provide a `<title>` inside each SVG and a `<table>` fallback for screen readers.

---

## Chart Inventory

### 1. Ticket Volume (Streaming Area Chart)

Real-time ticket inflow over the last 60 minutes. Updates every 5s.

```tsx
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export function TicketVolumeChart({ data }: { data: VolumePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="volumeGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#22C55E" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22C55E" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="time"
          tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'Fira Code' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'Fira Code' }}
          tickLine={false}
          axisLine={false}
          width={28}
        />
        <Tooltip content={<VolumeTooltip />} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#22C55E"
          strokeWidth={1.5}
          fill="url(#volumeGrad)"
          dot={false}
          animationDuration={300}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
```

**Color:** `#22C55E` (brand green) — represents healthy throughput.  
**Accessibility:** `role="img"` + `aria-label="Ticket volume over the last 60 minutes"` on container.

---

### 2. Priority Distribution (Donut Chart)

Breakdown of open tickets by priority. Static snapshot, refreshes every 10s.

```tsx
import { PieChart, Pie, Cell, Legend, ResponsiveContainer } from 'recharts'

const PRIORITY_COLORS = {
  P1: '#DC2626',
  P2: '#EA580C',
  P3: '#CA8A04',
  P4: '#16A34A',
}

export function PriorityDonut({ data }: { data: PriorityCount[] }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={75}
          dataKey="count"
          nameKey="priority"
          paddingAngle={2}
        >
          {data.map(entry => (
            <Cell key={entry.priority} fill={PRIORITY_COLORS[entry.priority]} />
          ))}
        </Pie>
        <Legend
          formatter={(value) => (
            <span className="font-mono text-mono-sm text-slate-300">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
```

**Center label:** Total open ticket count (positioned absolutely over the donut hole).

---

### 3. Category Heatmap (Bar Chart)

Horizontal bar chart: tickets per category, colored by category accent.

```tsx
import { BarChart, Bar, XAxis, YAxis, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const CATEGORY_COLORS: Record<string, string> = {
  VPN:      '#0891B2',
  SECURITY: '#D97706',
  HARDWARE: '#7C3AED',
  SOFTWARE: '#0284C7',
  ACCESS:   '#0D9488',
  OTHER:    '#64748B',
}

export function CategoryBreakdown({ data }: { data: CategoryCount[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="category"
          tick={{ fill: '#CBD5E1', fontSize: 12, fontFamily: 'Fira Code' }}
          width={72}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CategoryTooltip />} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={20}>
          {data.map(entry => (
            <Cell key={entry.category} fill={CATEGORY_COLORS[entry.category] ?? '#64748B'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
```

---

### 4. SLA Breach Risk (Gauge / Progress Bars)

Per-ticket SLA countdown. Visual urgency increases as deadline approaches.

```tsx
interface SLATrackerProps {
  elapsed: number      // minutes
  limit: number        // minutes (from priority SLA)
  priority: Priority
}

export function SLABar({ elapsed, limit, priority }: SLATrackerProps) {
  const pct = Math.min((elapsed / limit) * 100, 100)
  const color =
    pct >= 90 ? '#DC2626' :
    pct >= 70 ? '#EA580C' :
    pct >= 50 ? '#CA8A04' :
               '#16A34A'

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between font-mono text-caption text-slate-500">
        <span>{elapsed}m elapsed</span>
        <span className={cn(pct >= 90 && 'text-red-400 font-semibold')}>
          {limit - elapsed}m remaining
        </span>
      </div>
      <div className="h-1.5 bg-bg-muted rounded-full overflow-hidden">
        <div
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`SLA ${pct.toFixed(0)}% elapsed`}
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}
```

---

### 5. Resolution Rate (Line Chart)

24-hour resolved vs escalated trend. Dual-line with distinct patterns.

```tsx
<LineChart data={data}>
  <Line
    type="monotone"
    dataKey="resolved"
    stroke="#22C55E"
    strokeWidth={1.5}
    dot={false}
    name="Resolved"
  />
  <Line
    type="monotone"
    dataKey="escalated"
    stroke="#EF4444"
    strokeWidth={1.5}
    strokeDasharray="4 2"   // dashed for colorblind users
    dot={false}
    name="Escalated"
  />
</LineChart>
```

Dashed line for escalated ensures colorblind users can distinguish the two series.

---

## Custom Tooltip Pattern

All charts share a consistent tooltip style:

```tsx
export function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-bg-overlay border border-border-default rounded-md px-3 py-2 shadow-lg">
      <p className="font-mono text-caption text-slate-500 mb-1">{label}</p>
      {payload.map(entry => (
        <p key={entry.name} className="font-mono text-mono-sm" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  )
}
```

---

## Chart Grid Styling

```tsx
import { CartesianGrid } from 'recharts'

// Consistent grid across all charts
<CartesianGrid
  strokeDasharray="3 3"
  stroke="#1E293B"          // border-subtle
  vertical={false}          // horizontal lines only for bar/area charts
/>
```

---

## Accessibility for Charts

1. **Container:** `role="img"` + `aria-label="[descriptive chart name]"`
2. **Table fallback:** Provide a visually-hidden `<table>` with the same data
3. **Colors:** Never rely on color alone — use stroke patterns + legend text
4. **Live charts:** Include a **Pause** button; announce updates via `aria-live="polite"`

```tsx
// Table fallback for screen readers
<table className="sr-only">
  <caption>Ticket volume over the last 60 minutes</caption>
  <thead>
    <tr><th>Time</th><th>Count</th></tr>
  </thead>
  <tbody>
    {data.map(row => (
      <tr key={row.time}><td>{row.time}</td><td>{row.count}</td></tr>
    ))}
  </tbody>
</table>
```

---

## Real-Time Data Management

```tsx
// Keep last 60 data points for area chart (1h at 1-min resolution)
function useStreamingData<T>(maxPoints = 60) {
  const [data, setData] = useState<T[]>([])

  const push = useCallback((point: T) => {
    setData(prev => [...prev.slice(-(maxPoints - 1)), point])
  }, [maxPoints])

  return { data, push }
}
```

**Performance note:** Recharts re-renders the full SVG on each data update. For >60 points at 2s intervals, consider `animationDuration={0}` or switch to Canvas-based rendering via `react-chartjs-2`.

---

## Chart SLA Reference

| Chart | Refresh | Max points | Animation |
|-------|---------|------------|-----------|
| Volume area | 5s | 60 | 300ms |
| Priority donut | 10s | — | 200ms |
| Category bars | 10s | — | 200ms |
| SLA bars | 1s | — | 1000ms |
| Resolution line | 60s | 288 (24h×12) | 0ms |
