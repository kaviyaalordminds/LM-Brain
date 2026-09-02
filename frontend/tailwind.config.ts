import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"IBM Plex Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        space: {
          950: '#080B10', // Deepest background
          900: '#0D1118', // Surface base
          850: '#131923', // Elevated card / container
          800: '#1B2433', // Active borders / hover
          750: '#232E40', // Muted borders / separators
          700: '#2D3A50',
          600: '#475569',
        },
        status: {
          running: '#10B981',
          queued: '#06B6D4',
          verifying: '#8B5CF6',
          warning: '#F59E0B',
          blocked: '#F97316',
          failed: '#EF4444',
          memory: '#6366F1',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'flow': 'flow 2s linear infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        flow: {
          '0%': { strokeDashoffset: '24' },
          '100%': { strokeDashoffset: '0' },
        },
      },
    },
  },
  plugins: [],
};
export default config;

