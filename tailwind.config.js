/** @type {import('tailwindcss').Config} */
module.exports = {
  // TAMBAHKAN prefix ini untuk migrasi yang aman dari Bootstrap
  prefix: 'tw-', 

  // Arahkan Tailwind ke template Flask Anda
  content: [
    "./nemukerja/templates/**/*.html",
    "./nemukerja/static/script.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}