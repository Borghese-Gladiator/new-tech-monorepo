import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        felt: "#0f3a2c",
        feltDeep: "#0a2a20",
      },
    },
  },
  plugins: [],
};

export default config;
