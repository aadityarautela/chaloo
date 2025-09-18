/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}", "./src/**/*.html", "./src/**/*.ts"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#deeefe',
          200: '#c0e0fd',
          300: '#96cafa',
          400: '#67adf6',
          500: '#3a8df0',
          600: '#1f6fdd',
          700: '#1858b6',
          800: '#174a93',
          900: '#173f78',
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica", "Arial", "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"],
      },
      boxShadow: {
        'soft': '0 8px 30px rgba(31, 111, 221, 0.12)'
      }
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
