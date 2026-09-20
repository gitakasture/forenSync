const THEME_KEY = "forensync_theme";

export function getTheme() {
  return localStorage.getItem(THEME_KEY) || "dark";
}

export function applyTheme(theme) {
  const root = document.documentElement;
  if (theme === "light") {
    root.classList.add("light");
  } else {
    root.classList.remove("light");
  }
  localStorage.setItem(THEME_KEY, theme);
}

export function initTheme() {
  applyTheme(getTheme());
}