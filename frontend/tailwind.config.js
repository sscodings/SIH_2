/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Stitch ChainNetra System Design Tokens
        surface: "#f8f9ff",
        "surface-dim": "#cadcf4",
        "surface-bright": "#f8f9ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#eef4ff",
        "surface-container": "#e4efff",
        "surface-container-high": "#dae9ff",
        "surface-container-highest": "#d2e4fd",
        "surface-variant": "#d2e4fd",
        "surface-tint": "#1b5fa7",
        background: "#f8f9ff",
        
        "on-surface": "#0a1d2e",
        "on-surface-variant": "#424751",
        "on-background": "#0a1d2e",
        
        "inverse-surface": "#213244",
        "inverse-on-surface": "#e9f1ff",
        
        outline: "#727782",
        "outline-variant": "#c2c6d2",
        
        primary: "#01549b",
        "on-primary": "#ffffff",
        "primary-container": "#2f6db5",
        "on-primary-container": "#e7eeff",
        "inverse-primary": "#a5c8ff",
        "primary-fixed": "#d4e3ff",
        "primary-fixed-dim": "#a5c8ff",
        "on-primary-fixed": "#001c3a",
        "on-primary-fixed-variant": "#004785",
        
        secondary: "#006b5f",
        "on-secondary": "#ffffff",
        "secondary-container": "#84f3e0",
        "on-secondary-container": "#006f63",
        "secondary-fixed": "#87f5e3",
        "secondary-fixed-dim": "#6ad9c7",
        "on-secondary-fixed": "#00201c",
        "on-secondary-fixed-variant": "#005047",
        
        tertiary: "#33567f",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#4c6e99",
        "on-tertiary-container": "#e7efff",
        "tertiary-fixed": "#d3e4ff",
        "tertiary-fixed-dim": "#a7c9f9",
        "on-tertiary-fixed": "#001c38",
        "on-tertiary-fixed-variant": "#244871",
        
        error: "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",

        // Backward compatibility / UI accent aliases
        ink: "#0a1d2e",
        panel: "#ffffff",
        raised: "#eef4ff",
        hairline: "#dae9ff",
        amber: {
          DEFAULT: "#D9901A",
          500: "#D9901A",
          400: "#F0A732",
          600: "#B87510"
        },
        cyan: {
          DEFAULT: "#2F6DB5",
          500: "#2F6DB5",
          400: "#4D8CD6",
          600: "#1B5294"
        },
        coral: {
          DEFAULT: "#C8504B",
          500: "#C8504B",
          400: "#E26B66",
          600: "#A93A36"
        },
        mint: {
          DEFAULT: "#1C9C8C",
          500: "#1C9C8C",
          400: "#36B7A6",
          600: "#137B6E"
        },
        violet: {
          DEFAULT: "#33567F",
          500: "#33567F",
          400: "#4C6E99",
          600: "#244063"
        },
        chain: {
          tron: "#ba1a1a",
          ethereum: "#2f6db5",
          bsc: "#d9901a",
          bitcoin: "#d9901a",
          polygon: "#33567f",
          arbitrum: "#01549b"
        },
        text: {
          primary: "#0a1d2e",
          muted: "#5A6B80"
        }
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        md: "0.5rem",
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
        full: "9999px"
      },
      spacing: {
        "space-xs": "0.25rem",
        "space-sm": "0.5rem",
        "space-md": "1rem",
        "space-lg": "1.5rem",
        "space-xl": "2rem",
        gutter: "1rem",
        "gutter-lg": "1.5rem",
        margin: "1.5rem",
        "margin-sm": "1rem"
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "Inter", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
        "body-sm": ["'IBM Plex Sans'", "sans-serif"],
        "body-md": ["'IBM Plex Sans'", "sans-serif"],
        "body-lg": ["'IBM Plex Sans'", "sans-serif"],
        "label-sm": ["'IBM Plex Sans'", "sans-serif"],
        "label-md": ["'IBM Plex Sans'", "sans-serif"],
        "headline-sm": ["'IBM Plex Sans'", "sans-serif"],
        "headline-md": ["'IBM Plex Sans'", "sans-serif"],
        "headline-lg": ["'IBM Plex Sans'", "sans-serif"],
        "display-lg": ["'IBM Plex Sans'", "sans-serif"],
        "code-sm": ["'IBM Plex Mono'", "monospace"],
        "code-md": ["'IBM Plex Mono'", "monospace"],
      },
      fontSize: {
        "body-sm": ["11px", { lineHeight: "16px", letterSpacing: "0.01em", fontWeight: "400" }],
        "label-sm": ["10px", { lineHeight: "14px", letterSpacing: "0.05em", fontWeight: "600" }],
        "body-md": ["13px", { lineHeight: "18px", letterSpacing: "0em", fontWeight: "400" }],
        "label-md": ["12px", { lineHeight: "16px", letterSpacing: "0.02em", fontWeight: "600" }],
        "code-sm": ["11px", { lineHeight: "16px", letterSpacing: "0em", fontWeight: "400" }],
        "code-md": ["13px", { lineHeight: "18px", letterSpacing: "0em", fontWeight: "400" }],
        "body-lg": ["15px", { lineHeight: "22px", letterSpacing: "0em", fontWeight: "400" }],
        "headline-sm": ["15px", { lineHeight: "22px", letterSpacing: "0em", fontWeight: "600" }],
        "headline-md": ["18px", { lineHeight: "26px", letterSpacing: "-0.005em", fontWeight: "600" }],
        "headline-lg": ["22px", { lineHeight: "30px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "display-lg": ["30px", { lineHeight: "38px", letterSpacing: "-0.015em", fontWeight: "600" }],
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
      }
    },
  },
  plugins: [],
}
