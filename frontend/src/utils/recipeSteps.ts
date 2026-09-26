// Logique partagée entre l'affichage classique d'une recette (RecipeSummary.vue) et le mode
// cuisine plein écran (RecipeCookMode.vue) : découpage d'une étape en segments (@mentions
// d'ingrédients, minuteurs "~{...}") et regroupement des ingrédients par group_name.
import { parseIngredientMentions } from './cooklangMentions'
import { parseTimerMentions } from './cooklangTimers'
import type { RecipeIngredient } from '../types/models'

export interface StepSegment {
  text: string
  ingredientId?: number
  timerSeconds?: number
  timerLabel?: string
}

export function buildStepSegments(instruction: string, ingredients: RecipeIngredient[]): StepSegment[] {
  const mentions = parseIngredientMentions(instruction).map((mention) => ({ kind: 'mention' as const, ...mention }))
  const timers = parseTimerMentions(instruction)
    .filter((timer) => timer.totalSeconds !== null)
    .map((timer) => ({ kind: 'timer' as const, ...timer }))
  const ranges = [...mentions, ...timers].sort((a, b) => a.start - b.start)
  if (!ranges.length) return [{ text: instruction }]

  const segments: StepSegment[] = []
  let cursor = 0
  for (const range of ranges) {
    if (range.start > cursor) {
      segments.push({ text: instruction.slice(cursor, range.start) })
    }
    if (range.kind === 'mention') {
      const match = ingredients.find(
        (item) => item.ingredient.name.toLowerCase() === range.displayName.toLowerCase(),
      )
      segments.push({ text: range.displayName, ingredientId: match?.ingredient.id })
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
