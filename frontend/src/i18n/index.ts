import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import fr from './locales/fr.json'

export type Locale = 'fr' | 'en'

export const SUPPORTED_LOCALES: Array<{ code: Locale; label: string }> = [
  { code: 'fr', label: 'Français' },
  { code: 'en', label: 'English' },
]

const STORAGE_KEY = 'locale'

function initialLocale(): Locale {
  const stored = localStorage.getItem(STORAGE_KEY)
  const match = SUPPORTED_LOCALES.find((l) => l.code === stored)
  return match?.code ?? 'fr'
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: initialLocale(),
  fallbackLocale: 'fr',
  messages: { fr, en },
})

export function setLocale(code: Locale) {
  i18n.global.locale.value = code
  localStorage.setItem(STORAGE_KEY, code)
  document.documentElement.setAttribute('lang', code)
}
