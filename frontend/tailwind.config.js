/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: "#040405",
          900: "#08080A",
          850: "#0E0E12",
          800: "#14141A",
          700: "#1E1E26",
          600: "#2A2A36",
        },
        accent: {
          cyan: "#00E5FF",
          emerald: "#10B981",
          violet: "#8B5CF6",
          amber: "#F59E0B",
          rose: "#F43F5E",
        }
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        serif: ["Instrument Serif", "Georgia", "serif"],
      },
      backgroundImage: {
        'glow-radial': 'radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.12) 0%, transparent 60%)',
        'glass-card': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      }
    },
  },
  plugins: [],
}
