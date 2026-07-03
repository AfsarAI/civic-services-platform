/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,jsx}",
  ],

  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },

        civic: {
          green: "#16a34a",
          amber: "#d97706",
          red: "#dc2626",
          blue: "#2563eb",
          gray: "#6b7280",
        },
      },

      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
      },

      boxShadow: {
        card: "0 4px 20px rgba(15,23,42,.05)",
        hover: "0 10px 35px rgba(15,23,42,.08)",
      },

      borderRadius: {
        xl: "16px",
        "2xl": "24px",
      },
    },
  },

  plugins: [],
}