import type { Config } from 'tailwindcss';

const v = (name: string) => `rgb(var(${name}) / <alpha-value>)`;

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        darkBg:      v('--bg-rgb'),
        cardBg:      v('--surface-rgb'),
        cardBg2:     v('--surface2-rgb'),
        bdr:         v('--bdr-rgb'),
        aqua:        v('--accent-rgb'),
        gold:        v('--gold-rgb'),
        'on-accent': v('--on-accent-rgb'),
        text:        v('--text-rgb'),
        teal:        v('--text2-rgb'),
        hint:        v('--hint-rgb'),
        win:         v('--win-rgb'),
        loss:        v('--loss-rgb'),
        green:       '#2FD996',
        orange:      '#FFB020',
        red:         '#FF5D6E',
        yellow:      '#FFC24B',
      },
      fontFamily: {
        arabic: ['Cairo', 'Noto Sans Arabic', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
