import { i18n } from '../i18n'

export function formatDuration(minutes: number | null | undefined): string {
  if (!minutes) return i18n.global.t('duration.minutes', { n: 0 })
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours === 0) return i18n.global.t('duration.minutes', { n: rest })
  if (rest === 0) return i18n.global.t('duration.hours', { n: hours })
  return i18n.global.t('duration.hoursMinutes', { h: hours, m: rest })
}
