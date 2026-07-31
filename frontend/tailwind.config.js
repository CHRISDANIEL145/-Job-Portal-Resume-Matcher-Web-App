/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f4fbf7",
          500: "#1f8f66",
          700: "#0f5f43"
        }
      }
    }
  },
  plugins: [],
};
