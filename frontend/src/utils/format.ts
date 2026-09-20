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
