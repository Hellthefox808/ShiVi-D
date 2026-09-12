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
          dark: "#08090C",
          card: "#111318",
          border: "#222634",
          accent: "#F59E0B",
          warning: "#F97316",
          danger: "#EF4444",
          success: "#10B981",
        }
      },
    },
  },
  plugins: [],
};
