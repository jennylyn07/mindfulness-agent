/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['DM Serif Display', 'serif'],
        sans: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        sage: {
          DEFAULT: '#7BA08A',
          light: '#A8C4B2',
          pale: '#D8EAE0',
          deep: '#4E7A62',
        },
        lavender: {
          DEFAULT: '#9B8EC4',
          light: '#C0B6E0',
          pale: '#E8E4F4',
        },
        accent: {
          DEFAULT: '#E8854A',
          pale: '#FAE8D8',
        },
        sky: {
          DEFAULT: '#5BA8CA',
          pale: '#DFF0FA',
        },
        cream: '#F5F2EC',
        'warm-white': '#FAFAF7',
      },
    },
  },
  plugins: [],
};
