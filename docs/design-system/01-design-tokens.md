# Design Tokens

All tokens are defined as CSS custom properties and mirrored in `tailwind.config.ts`. **Never hard-code hex values in components** — always reference a token.

## Theme Strategy

- **Default:** follows `prefers-color-scheme` (OS setting)
- **Override:** `localStorage.getItem('theme')` → `'light' | 'dark' | 'system'`
- **Mechanism:** Tailwind `darkMode: 'class'` — `<html>` gets class `dark` or not
- Tokens are defined on `:root` (light) and overridden on `.dark` (dark)

## CSS Custom Properties

```css
/* src/styles/tokens.css */

/* ── LIGHT MODE (default) ────────────────────────────────── */
:root {
  /* Surfaces */
  --color-bg-base:      #F8FAFC;   /* slate-50  — body background */
  --color-bg-raised:    #FFFFFF;   /* white     — cards, panels */
  --color-bg-overlay:   #F1F5F9;   /* slate-100 — modals, popovers */
  --color-bg-muted:     #E2E8F0;   /* slate-200 — disabled, inactive */

  /* Borders */
  --color-border-subtle:  #E2E8F0; /* slate-200 — card edges */
  --color-border-default: #CBD5E1; /* slate-300 — inputs, dividers */
  --color-border-strong:  #94A3B8; /* slate-400 — focused inputs */

  /* Text */
  --color-text-primary:  #0F172A;  /* slate-900 — headings, labels */
  --color-text-secondary:#334155;  /* slate-700 — body, descriptions */
  --color-text-muted:    #64748B;  /* slate-500 — timestamps, meta */
  --color-text-disabled: #94A3B8;  /* slate-400 — disabled state */

  /* Brand / CTA */
  --color-brand-primary:  #16A34A; /* green-600 — primary actions */
  --color-brand-hover:    #15803D; /* green-700 — primary hover */
  --color-brand-subtle:   #DCFCE7; /* green-100 — brand tint bg */

  /* Priority — foreground */
  --color-p1:         #DC2626;     /* red-600 */
  --color-p1-bg:      #FEF2F2;     /* red-50  — light tint */
  --color-p1-glow:    rgba(220,38,38,0.20);

  --color-p2:         #EA580C;     /* orange-600 */
  --color-p2-bg:      #FFF7ED;     /* orange-50 */
  --color-p2-glow:    rgba(234,88,12,0.15);

  --color-p3:         #CA8A04;     /* yellow-600 */
  --color-p3-bg:      #FEFCE8;     /* yellow-50 */

  --color-p4:         #16A34A;     /* green-600 */
  --color-p4-bg:      #F0FDF4;     /* green-50 */

  /* Status */
  --color-status-open:        #2563EB; /* blue-600 */
  --color-status-in-progress: #9333EA; /* purple-600 */
  --color-status-resolved:    #16A34A; /* green-600 */
  --color-status-escalated:   #DC2626; /* red-600 */
  --color-status-frozen:      #64748B; /* slate-500 */

  /* Live */
  --color-live:     #16A34A;
  --color-live-dim: rgba(22,163,74,0.15);

  /* Shadows (lighter in light mode) */
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.08);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.10);
  --shadow-lg:    0 8px 24px rgba(0,0,0,0.12);
  --shadow-glow-p1: 0 0 12px var(--color-p1-glow);
  --shadow-glow-p2: 0 0 12px var(--color-p2-glow);
  --shadow-live:    0 0 8px rgba(22,163,74,0.30);
}

/* ── DARK MODE ───────────────────────────────────────────── */
.dark {
  /* Surfaces */
  --color-bg-base:      #020617;   /* slate-950 */
  --color-bg-raised:    #0F172A;   /* slate-900 */
  --color-bg-overlay:   #1E293B;   /* slate-800 */
  --color-bg-muted:     #334155;   /* slate-700 */

  /* Borders */
  --color-border-subtle:  #1E293B;
  --color-border-default: #334155;
  --color-border-strong:  #475569;

  /* Text */
  --color-text-primary:  #F8FAFC;
  --color-text-secondary:#CBD5E1;
  --color-text-muted:    #64748B;
  --color-text-disabled: #475569;

  /* Brand */
  --color-brand-primary:  #22C55E; /* green-500 — brighter on dark */
  --color-brand-hover:    #16A34A;
  --color-brand-subtle:   #14532D; /* green-900 */

  /* Priority */
  --color-p1:         #DC2626;
  --color-p1-bg:      #450A0A;     /* red-950 */
  --color-p1-glow:    rgba(220,38,38,0.35);

  --color-p2:         #EA580C;
  --color-p2-bg:      #431407;
  --color-p2-glow:    rgba(234,88,12,0.30);

  --color-p3:         #CA8A04;
  --color-p3-bg:      #422006;

  --color-p4:         #16A34A;
  --color-p4-bg:      #052E16;

  /* Status */
  --color-status-open:        #3B82F6;
  --color-status-in-progress: #A855F7;
  --color-status-resolved:    #22C55E;
  --color-status-escalated:   #EF4444;
  --color-status-frozen:      #94A3B8;

  /* Live */
  --color-live:     #22C55E;
  --color-live-dim: rgba(34,197,94,0.15);

  /* Shadows */
  --shadow-sm:    0 1px 2px rgba(0,0,0,0.5);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.6);
  --shadow-lg:    0 8px 24px rgba(0,0,0,0.7);
  --shadow-glow-p1: 0 0 12px var(--color-p1-glow);
  --shadow-glow-p2: 0 0 12px var(--color-p2-glow);
  --shadow-live:    0 0 8px rgba(34,197,94,0.4);
}

/* ── SHARED (both modes) ─────────────────────────────────── */
:root {
  /* Border Radius */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:  12px;
  --radius-xl:  16px;
  --radius-full: 9999px;

  /* Z-Index Scale */
  --z-base:    0;
  --z-raised:  10;
  --z-dropdown:20;
  --z-sticky:  30;
  --z-modal:   50;
  --z-toast:   60;
  --z-tooltip: 70;

  /* Transitions */
  --transition-fast:   150ms ease;
  --transition-base:   200ms ease;
  --transition-slow:   300ms ease;

  /* Typography */
  --font-mono:  'Fira Code', 'Cascadia Code', monospace;
  --font-sans:  'Fira Sans', 'Inter', system-ui, sans-serif;

  /* Animation */
  --pulse-critical: pulse-critical 2s cubic-bezier(0.4,0,0.6,1) infinite;
  --pulse-live:     pulse 2s cubic-bezier(0.4,0,0.6,1) infinite;
}

@keyframes pulse-critical {
  0%, 100% { box-shadow: 0 0 0 0 var(--color-p1-glow); }
  50%       { box-shadow: 0 0 0 6px transparent; }
}
```

## Theme Bootstrap (index.html / main.tsx)

Apply the correct class to `<html>` before first paint to prevent flash:

```html
<!-- index.html — inline script in <head>, before any CSS -->
<script>
  (function () {
    const stored = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const isDark = stored === 'dark' || (stored !== 'light' && prefersDark)
    document.documentElement.classList.toggle('dark', isDark)
  })()
</script>
```

## Theme Hook (React)

```tsx
// src/hooks/useTheme.ts
type Theme = 'light' | 'dark' | 'system'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem('theme') as Theme) ?? 'system'
  )

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      root.classList.toggle('dark', mq.matches)
      const handler = (e: MediaQueryListEvent) => root.classList.toggle('dark', e.matches)
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    } else {
      root.classList.toggle('dark', theme === 'dark')
    }
  }, [theme])

  const applyTheme = (next: Theme) => {
    setTheme(next)
    if (next === 'system') localStorage.removeItem('theme')
    else localStorage.setItem('theme', next)
  }

  return { theme, applyTheme }
}
```

## Tailwind Config

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',   // controlled by <html class="dark">
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Use CSS vars so both modes work automatically
        bg: {
          base:    'var(--color-bg-base)',
          raised:  'var(--color-bg-raised)',
          overlay: 'var(--color-bg-overlay)',
          muted:   'var(--color-bg-muted)',
        },
        border: {
          subtle:  'var(--color-border-subtle)',
          default: 'var(--color-border-default)',
          strong:  'var(--color-border-strong)',
        },
        text: {
          primary:   'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted:     'var(--color-text-muted)',
          disabled:  'var(--color-text-disabled)',
        },
        brand: {
          DEFAULT: 'var(--color-brand-primary)',
          hover:   'var(--color-brand-hover)',
          subtle:  'var(--color-brand-subtle)',
        },
        priority: {
          p1: 'var(--color-p1)',
          p2: 'var(--color-p2)',
          p3: 'var(--color-p3)',
          p4: 'var(--color-p4)',
        },
        status: {
          open:          'var(--color-status-open)',
          'in-progress': 'var(--color-status-in-progress)',
          resolved:      'var(--color-status-resolved)',
          escalated:     'var(--color-status-escalated)',
          frozen:        'var(--color-status-frozen)',
        },
      },
      fontFamily: {
        mono: ['Fira Code', 'Cascadia Code', 'monospace'],
        sans: ['Fira Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-p1':  'var(--shadow-glow-p1)',
        'glow-p2':  'var(--shadow-glow-p2)',
        'glow-live':'var(--shadow-live)',
      },
      borderRadius: {
        sm: '4px', md: '8px', lg: '12px', xl: '16px',
      },
      animation: {
        'pulse-critical': 'pulse-critical 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'live-dot':       'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      keyframes: {
        'pulse-critical': {
          '0%, 100%': { boxShadow: '0 0 0 0 var(--color-p1-glow)' },
          '50%':       { boxShadow: '0 0 0 6px transparent' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
```

## Token Usage Rules

| Rule | Correct | Wrong |
|------|---------|-------|
| Background surfaces | `bg-bg-raised` | `bg-slate-900` / `bg-white` |
| Priority foreground | `text-priority-p1` | `text-red-600` |
| Status colors | `text-status-open` | `text-blue-500` |
| Text hierarchy | `text-text-primary / secondary / muted` | `text-white` / `text-black` |
| Transitions | `transition-colors duration-200` | `transition-all duration-500` |
| Theme switching | CSS var tokens (auto-adapt) | Hard-coded dark/light hex pairs |
