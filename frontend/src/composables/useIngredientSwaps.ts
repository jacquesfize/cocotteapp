import { ref } from 'vue'
import type { IngredientAlternative, RecipeIngredient, Unit } from '../types/models'

// Remplacement d'un ingrédient par l'une de ses alternatives, le temps de la consultation d'une
// recette (page + mode cuisine). Ce choix n'est pas enregistré : planning, courses et nutrition
// restent calculés sur les ingrédients de la recette.
export interface DisplayedIngredient {
  name: string
  quantity: number | string
  unit: Unit
  // Alternative choisie pour cette ligne, null tant que l'ingrédient d'origine est affiché.
  swapped: IngredientAlternative | null
}

export function useIngredientSwaps() {
  // id de la ligne de recette -> id de l'alternative choisie
  const chosen = ref<Record<number, number>>({})

  function alternativesOf(item: RecipeIngredient): IngredientAlternative[] {
    return item.alternatives ?? []
  }

  function chosenAlternative(item: RecipeIngredient): IngredientAlternative | null {
    const id = chosen.value[item.id]
    return id ? (alternativesOf(item).find((alternative) => alternative.id === id) ?? null) : null
  }

  function choose(item: RecipeIngredient, alternative: IngredientAlternative | null) {
    if (alternative) {
      chosen.value = { ...chosen.value, [item.id]: alternative.id }
    } else {
      const { [item.id]: _removed, ...rest } = chosen.value
      chosen.value = rest
    }
  }

  function display(item: RecipeIngredient): DisplayedIngredient {
    const swapped = chosenAlternative(item)
    if (!swapped) return { name: item.ingredient.name, quantity: item.quantity, unit: item.unit, swapped: null }
    // Tag `less` : pas d'autre ingrédient, c'est celui de la ligne en plus petite quantité.
    return {
      name: swapped.ingredient?.name ?? item.ingredient.name,
      quantity: swapped.quantity,
      unit: swapped.unit,
      swapped,
    }
  }

  return { alternativesOf, chosenAlternative, choose, display }
}

export type IngredientSwaps = ReturnType<typeof useIngredientSwaps>
