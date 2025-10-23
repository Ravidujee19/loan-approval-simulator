/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      container: { center: true, padding: '1rem' },
      borderRadius: { '2xl': '1rem' },
    },
  },
  plugins: [],
};
