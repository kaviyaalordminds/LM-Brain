import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080B11",
        carbon: "#0E131F",
        "carbon-raised": "#141B2D",
        "carbon-hover": "#1A233A",
        "carbon-border": "#1F293D",
        brand: {
          blue: "#38BDF8",
          purple: "#818CF8",
          cyan: "#22D3EE",
          emerald: "#34D399",
          amber: "#FBBF24",
          rose: "#FB7185",
        }
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      }
    },
  },
  plugins: [],
};
export default config;
