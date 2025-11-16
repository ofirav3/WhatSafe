import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(222.2 47.4% 11.2%)",
        foreground: "hsl(210 40% 98%)",
        primary: {
          DEFAULT: "hsl(217.2 91.2% 59.8%)",
          foreground: "hsl(210 40% 98%)",
        },
        muted: {
          DEFAULT: "hsl(215 20.2% 65.1%)",
          foreground: "hsl(215.4 16.3% 56.9%)",
        }
      },
      borderRadius: {
        lg: "12px",
        md: "10px",
        sm: "8px"
      },
    },
  },
  plugins: [],
} satisfies Config;

