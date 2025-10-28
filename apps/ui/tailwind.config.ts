import type { Config } from 'tailwindcss'

export default {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        local: {
          DEFAULT: '#2563eb' // blue-600
        },
        cloud: {
          DEFAULT: '#7c3aed' // violet-600
        }
      }
    }
  },
  plugins: [require('@tailwindcss/typography'), require('@tailwindcss/line-clamp')]
} satisfies Config
