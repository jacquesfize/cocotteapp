import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark'

export const DEFAULT_ACCENT = '#ff6a3d'
export const ACCENT_PRESETS = ['#ff6a3d', '#e5484d', '#d6409f', '#7c5cff', '#2f80ed', '#12a594', '#3e9b4f', '#c98a00']

const MODE_KEY = 'theme-mode'
const ACCENT_KEY = 'theme-accent'
const HEX_RE = /^#[0-9a-f]{6}$/i

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // stockage indisponible (navigation privée...) : le choix vaut pour la session seulement
  }
}

function initialMode(): ThemeMode {
  const stored = read(MODE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

function initialAccent(): string {
  const stored = read(ACCENT_KEY)
  return stored && HEX_RE.test(stored) ? stored.toLowerCase() : DEFAULT_ACCENT
}

export const themeMode = ref<ThemeMode>(initialMode())
export const accentColor = ref<string>(initialAccent())

/** Noir ou blanc selon la luminance du fond, pour garder le texte lisible sur l'accent choisi. */
export function readableTextOn(hex: string): string {
  const channel = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  const luminance = 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5)
  return luminance > 0.5 ? '#241f1d' : '#ffffff'
}

export function applyTheme() {
  const root = document.documentElement
  root.setAttribute('data-theme', themeMode.value)
  root.style.setProperty('--color-primary', accentColor.value)
  root.style.setProperty('--color-on-primary', readableTextOn(accentColor.value))
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', accentColor.value)
}

export function setThemeMode(mode: ThemeMode) {
  themeMode.value = mode
  write(MODE_KEY, mode)
  applyTheme()
}

export function toggleThemeMode() {
  setThemeMode(themeMode.value === 'dark' ? 'light' : 'dark')
}

export function setAccentColor(hex: string) {
  if (!HEX_RE.test(hex)) return
  accentColor.value = hex.toLowerCase()
  write(ACCENT_KEY, accentColor.value)
  applyTheme()
}

export function resetAccentColor() {
  accentColor.value = DEFAULT_ACCENT
  write(ACCENT_KEY, null)
  applyTheme()
}
