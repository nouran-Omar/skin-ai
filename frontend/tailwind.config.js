/** SkinAI palette: deep navy, medical teal, quiet sage, and a cool off-white canvas. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      screens: { xs: "420px" },
      fontFamily: { sans: ['"Manrope Variable"', "system-ui", "sans-serif"], display: ['"Fraunces Variable"', "Georgia", "serif"] },
      colors: {
        brand: { 50: "#f3f7f8", 100: "#e4eef0", 200: "#c8dcdf", 300: "#9ebfc4", 400: "#6d9fa7", 500: "#397e88", 600: "#176c75", 700: "#125c66", 800: "#174454", 900: "#102a43" },
        mint: { 50: "#eff8f4", 100: "#dcefe6", 300: "#a3d4bc", 400: "#6eb99b", 500: "#349a82", 600: "#247d70", 700: "#1d655c" },
        teal: { 50: "#effafa", 100: "#d3f0ee", 300: "#74d2ca", 400: "#37b8ae", 500: "#159b96", 600: "#117b7a", 700: "#126264" },
        sage: { 50: "#f2f6f1", 100: "#e4ede1", 300: "#b7cbb1", 500: "#799575", 700: "#4d6854" },
        amber: { 500: "#c98a0b", 100: "#fbf0d4" },
        coral: { 500: "#c0392b", 100: "#fbe3df" },
        canvas: { DEFAULT: "#f7f8fb", dark: "#0b1620" },
        panel: { DEFAULT: "#ffffff", dark: "#111f2b" },
        line: { DEFAULT: "#dfe7e9", dark: "#263b48" },
      },
    },
  },
  plugins: [],
};
