/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        hud: { bg: "#0a0a0f", card: "#1a1a2e", accent: "#00d4ff", text: "#e0e0e0", muted: "#8888aa", success: "#00ff88", warning: "#ffaa00", danger: "#ff4444" },
      },
      fontFamily: { mono: ["JetBrains Mono", "monospace"] },
      animation: { "fade-in": "fadeIn 0.3s ease-out", "slide-up": "slideUp 0.3s ease-out", pulse: "pulse 2s infinite" },
      keyframes: { fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } }, slideUp: { "0%": { opacity: "0", transform: "translateY(10px)" }, "100%": { opacity: "1", transform: "translateY(0)" } } },
    },
  },
  plugins: [],
};
