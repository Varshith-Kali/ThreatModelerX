/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1A1A1A', // Dark charcoal (background)
          light: '#2A2A2A',   // Slightly lighter charcoal
        },
        secondary: {
          DEFAULT: '#282828', // Dark grey (card backgrounds)
          light: '#3A3A3A',   // Medium grey (hover states)
        },
        accent: {
          DEFAULT: '#FFFFFF', // White (for accent elements)
          light: '#F5F5F5',   // Off-white
        },
        text: {
          primary: '#FFFFFF', // White text
          secondary: '#E0E0E0', // Light grey text
          muted: '#999999',   // Muted grey text
        },
        brand: {
          DEFAULT: '#FFFFFF', // White for brand elements
        },
        highlight: {
          DEFAULT: '#444444', // Highlight color for hover states
        },
        // Override all blue-related colors
        blue: '#444444',
        cyan: '#444444',
        sky: '#444444',
        indigo: '#444444',
        // Override severity colors
        critical: '#444444',
        high: '#444444',
        medium: '#444444',
        low: '#444444'
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
