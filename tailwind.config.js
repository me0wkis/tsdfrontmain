/** @type {import('tailwindcss').Config} */
import PrimeUI from "tailwindcss-primeui";

export default {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Lato", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [PrimeUI],
};
