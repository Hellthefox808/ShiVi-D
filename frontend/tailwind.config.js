/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        shivi: {
          dark: "#0F172A",
          card: "#FFFFFF",
          border: "#E2E8F0",
          accent: "#D97706",
          warning: "#EA580C",
          danger: "#DC2626",
          success: "#16A34A",
        }

      },
    },
  },
  plugins: [],
};
