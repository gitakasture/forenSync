/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12161B",
        panel: "#1A1F26",
        raised: "#20262E",
        hairline: "#2B333C",
        ash: "#8B93A0",
        paper: "#E9E7E2",
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
