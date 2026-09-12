import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import fr from './locales/fr.json'

export const SUPPORTED_LOCALES = [
  { code: 'fr', label: 'Français' },
  { code: 'en', label: 'English' },
]

const STORAGE_KEY = 'locale'

function initialLocale() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (SUPPORTED_LOCALES.some((l) => l.code === stored)) return stored
  return 'fr'
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: initialLocale(),
  fallbackLocale: 'fr',
  messages: { fr, en },
})

export function setLocale(code) {
  i18n.global.locale.value = code
  localStorage.setItem(STORAGE_KEY, code)
  document.documentElement.setAttribute('lang', code)
}
