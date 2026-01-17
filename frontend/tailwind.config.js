/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Background colors - deep navy/charcoal
        background: {
          primary: '#0a0e1a',
          secondary: '#0f172a',
          tertiary: '#1e293b',
        },
        // Surface colors for glassmorphism
        surface: {
          glass: 'rgba(255, 255, 255, 0.03)',
          'glass-hover': 'rgba(255, 255, 255, 0.06)',
          'glass-active': 'rgba(255, 255, 255, 0.08)',
        },
        // Status colors
        status: {
          normal: '#22c55e',
          'normal-muted': '#16a34a',
          warning: '#f59e0b',
          'warning-muted': '#d97706',
          critical: '#ef4444',
          'critical-muted': '#dc2626',
          info: '#3b82f6',
        },
        // Text colors
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#64748b',
        },
        // Accent colors
        accent: {
          cyan: '#06b6d4',
          purple: '#8b5cf6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['SF Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'title': ['1.75rem', { lineHeight: '2.25rem', fontWeight: '600' }],
        'section': ['1.25rem', { lineHeight: '1.75rem', fontWeight: '500' }],
        'body': ['0.9375rem', { lineHeight: '1.5rem', fontWeight: '400' }],
        'caption': ['0.75rem', { lineHeight: '1rem', fontWeight: '400' }],
      },
      borderRadius: {
        'glass': '12px',
        'panel': '16px',
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.3)',
        'glass-lg': '0 8px 40px rgba(0, 0, 0, 0.4)',
        'glow-green': '0 0 20px rgba(34, 197, 94, 0.3)',
        'glow-amber': '0 0 20px rgba(245, 158, 11, 0.3)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.3)',
      },
      backdropBlur: {
        'glass': '16px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
