/** @type {import('tailwindcss').Config} */
const config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: {
        "2xl": "1200px",
      },
    },
    extend: {
      colors: {
        background: "#020817",
        foreground: "#E2E8F0",
        primary: {
          DEFAULT: "#38BDF8",
          foreground: "#0F172A",
        },
        muted: "#0B1220",
        border: "#1E293B",
        card: {
          DEFAULT: "#020617",
          foreground: "#E2E8F0",
        },
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.35rem",
      },
      boxShadow: {
        soft: "0 18px 45px rgba(15, 23, 42, 0.65)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
