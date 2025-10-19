const tokens = require("../../tokens/dist/tailwind.tokens.cjs");

module.exports = {
  content: ["./src/**/*.{html,js,ts,jsx,tsx}"],
  theme: {
    extend: tokens.theme.extend,
  },
  plugins: [],
};
