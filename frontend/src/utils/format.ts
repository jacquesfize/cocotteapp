import { i18n } from '../i18n'

/** Affiché à la place d'une valeur absente (durée non renseignée d'une recette importée...). */
export const MISSING_VALUE = '—'

/** Durée lisible ; une durée nulle ou absente (non renseignée) s'affiche "—" plutôt que "0 min". */
export function formatDuration(minutes: number | null | undefined): string {
  if (!minutes) return MISSING_VALUE
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours === 0) return i18n.global.t('duration.minutes', { n: rest })
  if (rest === 0) return i18n.global.t('duration.hours', { n: hours })
  return i18n.global.t('duration.hoursMinutes', { h: hours, m: rest })
}

/** En français le pluriel commence à 2 ("1,5 pincée") ; en anglais tout sauf 1 est pluriel. */
function isPlural(count: number): boolean {
  return i18n.global.locale.value === 'fr' ? count >= 2 : count !== 1
}

/**
 * Libellé traduit d'une unité (valeur stockée inchangée) ; retombe sur la valeur brute si inconnue.
 * Avec une quantité, accorde le libellé au pluriel pour les unités qui en ont un (`unitsPlural`),
 * en se basant sur la quantité telle qu'affichée par `formatQuantity`.
 */
export function formatUnit(unit: string | null | undefined, quantity?: number | string | null): string {
  if (!unit) return ''
  const pluralKey = `unitsPlural.${unit}`
  if (quantity !== undefined && quantity !== null && i18n.global.te(pluralKey)) {
    const count = Number(formatQuantity(quantity, unit))
    if (Number.isFinite(count) && isPlural(count)) return i18n.global.t(pluralKey)
  }
  const key = `units.${unit}`
  return i18n.global.te(key) ? i18n.global.t(key) : unit
}

/** Unités qui ne se comptent qu'en entier (pas de "0.5 pincée") — "piece" accepte désormais les
 * décimales (ex. "0.5 pièce" pour un demi-camembert). */
const INTEGER_UNITS = new Set(['pinch'])

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

/**
 * Nombre formaté selon la langue de l'interface (virgule décimale en français : "1,5"), avec au
 * plus `maxFractionDigits` décimales — ou exactement ce nombre si `fixed` (équivalent localisé
 * de `toFixed`, ex. "9,2 / 65,0 g").
 */
export function formatNumber(
  value: number | string | null | undefined,
  maxFractionDigits = 1,
  { fixed = false }: { fixed?: boolean } = {},
): string {
  if (value === null || value === undefined || value === '') return MISSING_VALUE
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  return new Intl.NumberFormat(i18n.global.locale.value, {
    maximumFractionDigits: maxFractionDigits,
    minimumFractionDigits: fixed ? maxFractionDigits : 0,
  }).format(numeric)
}
