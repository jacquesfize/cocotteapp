// Sous-ensemble Cooklang pour les minuteurs d'étape, ex. "Laisser reposer ~{10%minutes}."
// ou "Laisser ~repos{1%heure} au frigo." Même regex que le parseur backend (dormant, voir
// backend/apps/recipes/cooklang.py TIMER_RE) : un nom est optionnel avant les {}, la meta
// s'écrit "quantité%unité" (comme pour les mentions d'ingrédient, voir cooklangMentions.ts).
const TIMER_RE = /~(?<name>[^\s@#~{}]*)\{(?<meta>[^}]*)\}/g

const SECONDS_PER_UNIT: Record<string, number> = {
  s: 1,
  sec: 1,
  secs: 1,
  seconde: 1,
  secondes: 1,
  second: 1,
  seconds: 1,
  m: 60,
  min: 60,
  mins: 60,
  minute: 60,
  minutes: 60,
  h: 3600,
  hr: 3600,
  hrs: 3600,
  heure: 3600,
  heures: 3600,
  hour: 3600,
  hours: 3600,
}

export interface TimerMention {
  /** Nom optionnel avant les {}, tel que tapé (underscores compris), ex. "repos" */
  name: string
  /** Underscores remplacés par des espaces */
  displayName: string
  /** Quantité brute telle que tapée dans la meta, ex. "10" */
  quantity: string | null
  /** Unité brute telle que tapée dans la meta, ex. "minutes" */
  unit: string | null
  /** Durée totale en secondes, ou null si la quantité/unité n'est pas reconnue */
  totalSeconds: number | null
  /** Position du "~" dans le texte */
  start: number
  /** Position juste après la mention complète (nom + {meta}) */
  end: number
}

export function parseTimerMentions(text: string): TimerMention[] {
  const mentions: TimerMention[] = []
  for (const match of text.matchAll(TIMER_RE)) {
    const name = match.groups?.name ?? ''
    const meta = match.groups?.meta ?? ''
    const [quantityRaw, unitRaw] = meta.includes('%') ? meta.split('%', 2) : [meta, '']
    const quantity = quantityRaw.trim() || null
    const unit = unitRaw.trim() || null
    const quantityNumber = quantity !== null ? Number(quantity.replace(',', '.')) : NaN
    const secondsPerUnit = unit ? SECONDS_PER_UNIT[unit.toLowerCase()] : undefined
    const totalSeconds =
      secondsPerUnit !== undefined && !Number.isNaN(quantityNumber)
        ? Math.round(quantityNumber * secondsPerUnit)
        : null

    const start = match.index ?? 0
    mentions.push({
      name,
      displayName: name.replace(/_/g, ' '),
      quantity,
      unit,
      totalSeconds,
      start,
      end: start + match[0].length,
    })
  }
  return mentions
}
