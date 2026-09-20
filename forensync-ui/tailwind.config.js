/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        panel: "rgb(var(--color-panel) / <alpha-value>)",
        raised: "rgb(var(--color-raised) / <alpha-value>)",
        hairline: "rgb(var(--color-hairline) / <alpha-value>)",
        ash: "rgb(var(--color-ash) / <alpha-value>)",
        paper: "rgb(var(--color-paper) / <alpha-value>)",
        amber: {
          DEFAULT: "#E8A33D",
          hover: "#F0B458",
          dim: "#8A6626",
        },
        teal: {
          DEFAULT: "#4FB6B0",
          dim: "#2E4E4C",
        },
        danger: "#D6524B",
        success: "#5FAE7A",
      },
      fontFamily: {
        display: ["IBM Plex Serif", "Georgia", "serif"],
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
}