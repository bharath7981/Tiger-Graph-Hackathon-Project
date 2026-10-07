/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0d14',
          800: '#111726',
          700: '#1b2338',
          600: '#26314d',
        },
        brand: {
          cyan: '#00f2fe',
          blue: '#4facfe',
          purple: '#7f53ac',
          amber: '#f6d365',
          emerald: '#10b981',
        }
      }
    },
  },
  plugins: [],
}
