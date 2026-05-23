/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0A0B0C',
          secondary: '#121316',
          tertiary: '#1A1B1F',
          card: '#1E2028',
          hover: '#252730',
        },
        border: {
          primary: '#2A2D35',
          secondary: '#353842',
        },
        accent: {
          primary: '#8B5CF6',
          hover: '#7C3AED',
          light: '#A78BFA',
        },
        text: {
          primary: '#F5F5F7',
          secondary: '#A0A0A8',
          muted: '#6B6B75',
        },
        status: {
          active: '#10B981',
          paused: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    }
  },
  plugins: []
}
