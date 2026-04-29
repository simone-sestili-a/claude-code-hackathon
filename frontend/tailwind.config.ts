import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      colors: {
        accent: {
          DEFAULT: "var(--color-accent)",
          hover: "var(--color-accent-hover)",
          fg: "var(--color-accent-fg)",
          subtle: "var(--color-accent-subtle)",
          muted: "var(--color-accent-muted)",
        },
        surface: {
          DEFAULT: "var(--color-surface)",
          sidebar: "var(--color-sidebar)",
          "sidebar-active": "var(--color-sidebar-active)",
        },
        border: {
          DEFAULT: "var(--color-border)",
          subtle: "var(--color-border-subtle)",
        },
        text: {
          DEFAULT: "var(--color-text)",
          secondary: "var(--color-text-secondary)",
          tertiary: "var(--color-text-tertiary)",
        },
        status: {
          success: "var(--color-success)",
          "success-bg": "var(--color-success-bg)",
          warning: "var(--color-warning)",
          "warning-bg": "var(--color-warning-bg)",
          error: "var(--color-error)",
          "error-bg": "var(--color-error-bg)",
        },
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "10px",
      },
      transitionTimingFunction: {
        "out-quart": "cubic-bezier(0.25, 1, 0.5, 1)",
      },
      transitionDuration: {
        DEFAULT: "150ms",
      },
      animation: {
        "fade-in": "fadeIn 150ms cubic-bezier(0.25, 1, 0.5, 1)",
        "slide-in": "slideIn 200ms cubic-bezier(0.25, 1, 0.5, 1)",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
