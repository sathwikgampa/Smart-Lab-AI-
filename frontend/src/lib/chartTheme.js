// Chart colours. Categorical slots are assigned in fixed order (never cycled). Slot 1 is the
// brand accent purple (see src/theme.css); slots 2-4 (orange, green, amber) stay well separated
// from it and from each other under colour-vision deficiency. Light-mode slots 3-4 sit below 3:1
// contrast on white, so every chart also ships a legend, tooltips and a table view.
export const SERIES = {
  light: ["#6B4FD8", "#eb6834", "#1baf7a", "#eda100"],
  dark: ["#8F78E8", "#d95926", "#199e70", "#c98500"],
};

export function chartTheme(theme) {
  const dark = theme === "dark";
  return {
    series: SERIES[dark ? "dark" : "light"],
    grid: dark ? "#2A2A2E" : "#ECECEF",
    axis: dark ? "#A1A1A8" : "#6E6E76",
    surface: dark ? "#111111" : "#FFFFFF",
    tooltip: {
      contentStyle: {
        background: dark ? "#111111" : "#FFFFFF",
        border: `1px solid ${dark ? "#2A2A2E" : "#ECECEF"}`,
        borderRadius: 10,
        boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
        fontSize: 12,
        color: dark ? "#F4F4F7" : "#111111",
      },
      labelStyle: { color: dark ? "#C9C9CF" : "#6E6E76" },
      itemStyle: { color: dark ? "#F4F4F7" : "#111111" },
    },
  };
}
