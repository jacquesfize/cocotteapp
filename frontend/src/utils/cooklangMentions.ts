// Sous-ensemble Cooklang pour référencer un ingrédient (ou un matériel) depuis le texte d'une
// étape, ex. "Faire revenir l'@oignon dans la #poêle puis ajouter l'@huile_olive{2%cs}." Même
// syntaxe que le parseur backend (backend/apps/recipes/cooklang.py) : les mots multiples
// s'écrivent avec un underscore (ex. "huile_olive" -> "huile olive").
const MENTION_RE = /@(?<name>[^\s@#~{}]+)(?:\{(?<meta>[^}]*)\})?/g
// Le nom d'un matériel ne commence pas par un chiffre ("étape #2" reste du texte) et s'arrête à
// la ponctuation ("le #four." désigne le four).
const COOKWARE_RE = /#(?<name>[^\s\d@#~{}.,;:!?()][^\s@#~{}.,;:!?()]*)(?:\{(?<meta>[^}]*)\})?/g

export interface IngredientMention {
  /** Tel que tapé, ex. "huile_olive" */
  name: string
  /** Underscores remplacés par des espaces, ex. "huile olive" */
  displayName: string
  /** Position du "@" (ou du "#") dans le texte */
  start: number
  /** Position juste après la mention complète (nom + éventuel {meta}) */
  end: number
}

export type CookwareMention = IngredientMention

function parseMentions(text: string, pattern: RegExp): IngredientMention[] {
  const mentions: IngredientMention[] = []
  for (const match of text.matchAll(pattern)) {
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

function withoutKnown(mentions: IngredientMention[], knownNames: string[]) {
  const known = new Set(knownNames.map((name) => name.trim().toLowerCase()))
  return mentions.filter((mention) => !known.has(mention.displayName.toLowerCase()))
}

export function parseIngredientMentions(text: string): IngredientMention[] {
  return parseMentions(text, MENTION_RE)
}

export function parseCookwareMentions(text: string): CookwareMention[] {
  return parseMentions(text, COOKWARE_RE)
}

export function findOrphanMentions(text: string, knownNames: string[]): IngredientMention[] {
  return withoutKnown(parseIngredientMentions(text), knownNames)
}

export function findOrphanCookwareMentions(text: string, knownNames: string[]): CookwareMention[] {
  return withoutKnown(parseCookwareMentions(text), knownNames)
}

/** Convertit un nom d'ingrédient réel en mention Cooklang, ex. "huile olive" -> "@huile_olive". */
export function toMentionToken(ingredientName: string): string {
  return `@${ingredientName.trim().replace(/\s+/g, '_')}`
}

/** Convertit un nom de matériel en mention Cooklang, ex. "Friteuse à air" -> "#Friteuse_à_air". */
export function toCookwareToken(cookwareName: string): string {
  return `#${cookwareName.trim().replace(/\s+/g, '_')}`
}
