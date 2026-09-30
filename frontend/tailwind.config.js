/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#070B14",
        panel: "#0D1424",
        raised: "#121B30",
        hairline: "#1F2B47",
        amber: {
          DEFAULT: "#FFB020",
          500: "#FFB020",
          400: "#FFC24D",
          600: "#E09815"
        },
        cyan: {
          DEFAULT: "#22D3EE",
          500: "#22D3EE",
          400: "#38BDF8",
          600: "#0284C7"
        },
        coral: {
          DEFAULT: "#FF5D5D",
          500: "#FF5D5D",
          400: "#FF7878",
          600: "#E04848"
        },
        mint: {
          DEFAULT: "#3DDC97",
          500: "#3DDC97",
          400: "#5EE7AB",
          600: "#2BBF80"
        },
        violet: {
          DEFAULT: "#8B7CFF",
          500: "#8B7CFF",
          400: "#A79AFF",
          600: "#6F5DEB"
        },
        chain: {
          tron: "#FF4D4D",
          ethereum: "#627EEA",
          bsc: "#F3BA2F",
          bitcoin: "#F7931A",
          polygon: "#8247E5",
          arbitrum: "#28A0F0"
        },
        text: {
          primary: "#E6ECFF",
          muted: "#8A97B8"
        }
      },
      fontFamily: {
        sans: ["'Space Grotesk'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
      }
    },
  },
  plugins: [],
}
