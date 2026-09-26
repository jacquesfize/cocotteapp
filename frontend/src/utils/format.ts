import { i18n } from '../i18n'

export function formatDuration(minutes: number | null | undefined): string {
  if (!minutes) return i18n.global.t('duration.minutes', { n: 0 })
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours === 0) return i18n.global.t('duration.minutes', { n: rest })
  if (rest === 0) return i18n.global.t('duration.hours', { n: hours })
  return i18n.global.t('duration.hoursMinutes', { h: hours, m: rest })
}

/** Libellé traduit d'une unité (valeur stockée inchangée) ; retombe sur la valeur brute si inconnue. */
export function formatUnit(unit: string | null | undefined): string {
  if (!unit) return ''
  const key = `units.${unit}`
  return i18n.global.te(key) ? i18n.global.t(key) : unit
}

/** Unités qui ne se comptent qu'en entier (pas de "1.5 pièce" ni de "0.5 pincée"). */
const INTEGER_UNITS = new Set(['piece', 'pinch'])

/**
 * Quantité d'ingrédient lisible : entier (arrondi au supérieur) pour les unités entières,
 * sinon au plus 2 décimales sans zéros inutiles ("2.00" → "2", "1.50" → "1.5").
 */
export function formatQuantity(quantity: number | string | null | undefined, unit?: string | null): string {
  if (quantity === null || quantity === undefined || quantity === '') return ''
  const numeric = Number(quantity)
  if (!Number.isFinite(numeric)) return String(quantity)
  if (unit && INTEGER_UNITS.has(unit)) return String(Math.ceil(numeric))
  return String(Math.round(numeric * 100) / 100)
}
