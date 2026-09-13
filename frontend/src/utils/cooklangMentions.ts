// Sous-ensemble Cooklang pour référencer un ingrédient depuis le texte d'une étape,
// ex. "Faire revenir l'@oignon puis ajouter l'@huile_olive{2%cs}." Même regex que le
// parseur backend (backend/apps/recipes/cooklang.py) : les mots multiples s'écrivent
// avec un underscore (ex. "huile_olive" -> "huile olive").
const MENTION_RE = /@(?<name>[^\s@#~{}]+)(?:\{(?<meta>[^}]*)\})?/g

export interface IngredientMention {
  /** Tel que tapé, ex. "huile_olive" */
  name: string
  /** Underscores remplacés par des espaces, ex. "huile olive" */
  displayName: string
  /** Position du "@" dans le texte */
  start: number
  /** Position juste après la mention complète (nom + éventuel {meta}) */
  end: number
}

export function parseIngredientMentions(text: string): IngredientMention[] {
  const mentions: IngredientMention[] = []
  for (const match of text.matchAll(MENTION_RE)) {
    const name = match.groups?.name ?? ''
    const start = match.index ?? 0
    mentions.push({
      name,
      displayName: name.replace(/_/g, ' '),
      start,
      end: start + match[0].length,
    })
  }
  return mentions
}

export function findOrphanMentions(text: string, knownNames: string[]): IngredientMention[] {
  const known = new Set(knownNames.map((name) => name.trim().toLowerCase()))
  return parseIngredientMentions(text).filter((mention) => !known.has(mention.displayName.toLowerCase()))
}

/** Convertit un nom d'ingrédient réel en mention Cooklang, ex. "huile olive" -> "@huile_olive". */
export function toMentionToken(ingredientName: string): string {
  return `@${ingredientName.trim().replace(/\s+/g, '_')}`
}
