# Typography

## Font System

IntakeAI uses the **Fira** family — technical, monospaced feel for data surfaces, humanist sans for readable prose.

| Role | Font | Rationale |
|------|------|-----------|
| Headings / Labels / IDs | **Fira Code** | Monospaced; ticket IDs, timestamps, and code snippets feel native |
| Body / Descriptions / Prose | **Fira Sans** | Humanist; comfortable at paragraph density |

```html
<!-- index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
```

## Type Scale

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `text-display` | 32px / 2rem | 1.2 | 700 | Page titles, empty states |
| `text-heading-lg` | 24px / 1.5rem | 1.3 | 600 | Section headings |
| `text-heading-md` | 20px / 1.25rem | 1.35 | 600 | Card headings |
| `text-heading-sm` | 16px / 1rem | 1.4 | 600 | Sub-section labels |
| `text-body-lg` | 16px / 1rem | 1.6 | 400 | Primary body text |
| `text-body-md` | 14px / 0.875rem | 1.6 | 400 | Default body, ticket descriptions |
| `text-body-sm` | 13px / 0.8125rem | 1.5 | 400 | Secondary info, metadata |
| `text-caption` | 12px / 0.75rem | 1.4 | 400 | Timestamps, footnotes |
| `text-label` | 11px / 0.6875rem | 1.3 | 600 | Badges, chips (ALL CAPS) |
| `text-mono-md` | 14px / 0.875rem | 1.5 | 400 | Ticket IDs, user IDs, log lines |
| `text-mono-sm` | 12px / 0.75rem | 1.4 | 400 | Audit log entries, raw JSON |

## Tailwind Utilities (Custom)

Add to `tailwind.config.ts` under `theme.extend.fontSize`:

```typescript
fontSize: {
  'display':    ['2rem',    { lineHeight: '1.2',  fontWeight: '700' }],
  'heading-lg': ['1.5rem',  { lineHeight: '1.3',  fontWeight: '600' }],
  'heading-md': ['1.25rem', { lineHeight: '1.35', fontWeight: '600' }],
  'heading-sm': ['1rem',    { lineHeight: '1.4',  fontWeight: '600' }],
  'body-lg':    ['1rem',    { lineHeight: '1.6',  fontWeight: '400' }],
  'body-md':    ['0.875rem',{ lineHeight: '1.6',  fontWeight: '400' }],
  'body-sm':    ['0.8125rem',{lineHeight: '1.5',  fontWeight: '400' }],
  'caption':    ['0.75rem', { lineHeight: '1.4',  fontWeight: '400' }],
  'label':      ['0.6875rem',{lineHeight: '1.3',  fontWeight: '600' }],
  'mono-md':    ['0.875rem',{ lineHeight: '1.5',  fontWeight: '400' }],
  'mono-sm':    ['0.75rem', { lineHeight: '1.4',  fontWeight: '400' }],
},
```

## Usage Rules

### Headings → Fira Code
```tsx
<h1 className="font-mono text-display text-slate-50">IntakeAI</h1>
<h2 className="font-mono text-heading-lg text-slate-50">Open Tickets</h2>
<h3 className="font-mono text-heading-sm text-slate-300">Last 24 hours</h3>
```

### Body → Fira Sans
```tsx
<p className="font-sans text-body-md text-slate-300 leading-relaxed">
  VPN access for the Singapore office is intermittently dropping...
</p>
```

### IDs / Timestamps / Audit → Fira Code (mono)
```tsx
<span className="font-mono text-mono-sm text-slate-500">#TKT-00423</span>
<time className="font-mono text-caption text-slate-500">2026-04-28 09:14:33Z</time>
```

### Labels / Badges → uppercase, Fira Sans
```tsx
<span className="font-sans text-label uppercase tracking-widest text-slate-300">
  Category
</span>
```

## Line Length

- **Ticket descriptions:** max `max-w-prose` (65ch) inside expanded card view
- **Audit log lines:** unconstrained — monospace, full width
- **Dashboard summaries:** max 45–55ch per column cell

## Text Color Hierarchy

```
slate-50  (#F8FAFC) — primary headings, active labels
slate-300 (#CBD5E1) — body text, descriptions
slate-500 (#64748B) — metadata, timestamps, helper text
slate-600 (#475569) — disabled / placeholder
```

Never use `text-white` — it emits too much light on OLED and disrupts contrast calibration.

## Don't

- Don't mix Fira Code and Fira Sans in the same sentence
- Don't use font-weight 300 (Light) for anything smaller than 16px
- Don't set line-height below 1.4 for any reading text
- Don't uppercase body text — only badges and structural labels
