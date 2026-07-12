/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "hud-bg": "#0a0a0f",
        "hud-card": "#1a1a2e",
        "hud-accent": "#00d4ff",
        "hud-text": "#e0e0e0",
        "hud-muted": "#8888aa",
        "hud-success": "#00ff88",
        "hud-warning": "#ffaa00",
        "hud-danger": "#ff4444",
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};