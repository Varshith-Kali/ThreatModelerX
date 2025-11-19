/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#050505', // Very dark almost black
          light: '#0a0a0a',   // Slightly lighter
        },
        secondary: {
          DEFAULT: '#121212', // Material Design Dark Surface
          light: '#1e1e1e',   // Lighter surface
        },
        accent: {
          DEFAULT: '#00E5FF', // Cyan Neon
          light: '#E0F7FA',   // Very light cyan
          hover: '#00B8D4',   // Darker cyan
        },
        text: {
          primary: '#FFFFFF', // White
          secondary: '#B0BEC5', // Blue Grey
          muted: '#78909C',   // Muted Blue Grey
        },
        brand: {
          DEFAULT: '#00E5FF', // Cyan Neon
        },
        highlight: {
          DEFAULT: '#263238', // Dark Blue Grey
        },
        // Override all blue-related colors to match theme
        blue: {
          50: '#E0F7FA',
          100: '#B2EBF2',
          500: '#00BCD4',
          600: '#00ACC1',
          700: '#0097A7',
        },
        // Override severity colors for dark mode
        critical: '#FF5252', // Red A200
        high: '#FFAB40',     // Orange A200
        medium: '#FFD740',   // Amber A200
        low: '#69F0AE'       // Green A200
      },
    },
  },
  safelist: [
    'bg-highlight',
    'text-accent',
    'border-highlight',
    'bg-secondary',
    'bg-primary-light',
    'text-text-secondary'
  ],
  plugins: [],
};
