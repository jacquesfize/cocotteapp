// Logique partagée entre l'affichage classique d'une recette (RecipeSummary.vue) et le mode
// cuisine plein écran (RecipeCookMode.vue) : découpage d'une étape en segments (@mentions
// d'ingrédients, #matériel, minuteurs "~{...}") et regroupement des ingrédients par group_name.
import { parseCookwareMentions, parseIngredientMentions } from './cooklangMentions'
import { parseTimerMentions } from './cooklangTimers'
import type { Cookware, RecipeIngredient } from '../types/models'

export interface StepSegment {
  text: string
  ingredientId?: number
  // Position de la ligne d'ingrédient visée dans `ingredients` : un même ingrédient pouvant figurer
  // dans plusieurs parties, l'id seul ne désigne pas une ligne (ancre `ingredient-row-<index>`).
  ingredientIndex?: number
  // Présent (éventuellement `undefined` si le matériel n'est pas dans la recette) pour un #matériel.
  cookware?: { id?: number }
  timerSeconds?: number
  timerLabel?: string
}

export function buildStepSegments(
  instruction: string,
  ingredients: RecipeIngredient[],
  cookware: Cookware[] = [],
): StepSegment[] {
  const mentions = parseIngredientMentions(instruction).map((mention) => ({ kind: 'mention' as const, ...mention }))
  const cookwareMentions = parseCookwareMentions(instruction).map((mention) => ({
    kind: 'cookware' as const,
    ...mention,
  }))
  const timers = parseTimerMentions(instruction)
    .filter((timer) => timer.totalSeconds !== null)
    .map((timer) => ({ kind: 'timer' as const, ...timer }))
  const ranges = [...mentions, ...cookwareMentions, ...timers].sort((a, b) => a.start - b.start)
  if (!ranges.length) return [{ text: instruction }]

  const segments: StepSegment[] = []
  let cursor = 0
  for (const range of ranges) {
    if (range.start > cursor) {
      segments.push({ text: instruction.slice(cursor, range.start) })
    }
    if (range.kind === 'mention') {
      // Plusieurs lignes pour le même ingrédient (une par partie) : la mention pointe vers la
      // première ; le détail de toutes les quantités est affiché par `ingredientRowsFor`.
      const matchIndex = ingredients.findIndex(
        (item) => item.ingredient.name.toLowerCase() === range.displayName.toLowerCase(),
      )
      const match = matchIndex >= 0 ? ingredients[matchIndex] : undefined
      // Mention qui ne correspond à aucun ingrédient de la recette (ex. "@len" laissé tel quel) :
      // on garde le texte tapé, "@" compris, plutôt que de le réduire silencieusement à "len" —
      // l'éditeur l'avertit déjà, l'affichage ne doit pas masquer la mention.
      segments.push(
        match
          ? { text: range.displayName, ingredientId: match.ingredient.id, ingredientIndex: matchIndex }
          : { text: instruction.slice(range.start, range.end) },
      )
    } else if (range.kind === 'cookware') {
      const match = cookware.find((item) => item.name.toLowerCase() === range.displayName.toLowerCase())
      segments.push({ text: range.displayName, cookware: { id: match?.id } })
    } else {
      segments.push({
        text: instruction.slice(range.start, range.end),
        timerSeconds: range.totalSeconds ?? undefined,
        timerLabel: range.displayName || undefined,
      })
    }
    cursor = range.end
  }
  if (cursor < instruction.length) {
    segments.push({ text: instruction.slice(cursor) })
  }
  return segments
}

// Toutes les lignes d'un même ingrédient (une par partie où il sert), dans l'ordre de la recette.
export function ingredientRowsFor(ingredients: RecipeIngredient[], ingredientId: number): RecipeIngredient[] {
  return ingredients.filter((item) => item.ingredient.id === ingredientId)
}

export interface IngredientGroup {
  name: string | null
  items: RecipeIngredient[]
}

// Les ingrédients sont ordonnés côté backend (RecipeIngredient.order) : on regroupe donc les
// group_name identiques et consécutifs sous un même intertitre plutôt que de le répéter en
// texte entre parenthèses sur chaque ligne.
export function groupIngredients(ingredients: RecipeIngredient[]): IngredientGroup[] {
  const groups: IngredientGroup[] = []
  for (const item of ingredients) {
    const name = item.group_name || null
    const last = groups[groups.length - 1]
    if (last && last.name === name) {
      last.items.push(item)
    } else {
      groups.push({ name, items: [item] })
    }
  }
  return groups
}
