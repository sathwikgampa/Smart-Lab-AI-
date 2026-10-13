/** @type {import('tailwindcss').Config} */
// Every colour below resolves to a CSS variable defined in src/theme.css (the single theme file).
const v = (name) => `rgb(var(--sl-${name}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        page: v("page"),
        canvas: v("canvas"),
        surface: v("surface"),
        subtle: v("subtle"),
        line: v("line"),
        ink: v("ink"),
        muted: v("muted"),
        faint: v("faint"),
        primary: { DEFAULT: v("primary"), hover: v("primary-hover") },
        accent: { DEFAULT: v("accent"), strong: v("accent-strong"), deeper: v("accent-deeper"), soft: v("accent-soft") },
        bubble: v("bubble"),
        success: { DEFAULT: v("success"), soft: v("success-soft") },
        warning: { DEFAULT: v("warning"), ink: v("warning-ink"), soft: v("warning-soft") },
        critical: { DEFAULT: v("critical"), soft: v("critical-soft") },
        // "info" shares the accent purple so notices stay in one palette.
        info: { DEFAULT: v("accent-strong"), soft: v("accent-soft") },
      },
      fontFamily: {
        sans: ["var(--sl-font-sans)"],
        serif: ["var(--sl-font-serif)"],
        mono: ["var(--sl-font-mono)"],
      },
      fontSize: { "2xs": ["0.6875rem", "1rem"] },
      maxWidth: { prose: "46rem" },
      borderRadius: { frame: "var(--sl-radius-frame)" },
      boxShadow: { panel: "var(--sl-shadow-panel)", pop: "var(--sl-shadow-pop)", prompt: "var(--sl-shadow-prompt)" },
    },
  },
  plugins: [],
};
