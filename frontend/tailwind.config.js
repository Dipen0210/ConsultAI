/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f9ff",
          500: "#2563eb",
          600: "#1d4ed8",
        },
      },
    },
  },
  plugins: [],
};
