import { describe, expect, it } from 'vitest'
import { useIngredientSwaps } from '../../src/composables/useIngredientSwaps'
import type { IngredientAlternative, RecipeIngredient } from '../../src/types/models'
import type { Ingredient } from '../../src/types/models'

const milk = { id: 1, name: 'Lait' } as Ingredient
const oatMilk = { id: 2, name: "Lait d'avoine" } as Ingredient

const vegan = { id: 11, ingredient: oatMilk, quantity: 300, unit: 'ml', tag: 'vegan', note: '', order: 0 } as IngredientAlternative
const less = { id: 12, ingredient: null, quantity: 100, unit: 'ml', tag: 'less', note: '', order: 1 } as IngredientAlternative
const line = {
  id: 5,
  ingredient: milk,
  quantity: 250,
  unit: 'ml',
  group_name: '',
  order: 0,
  alternatives: [vegan, less],
} as RecipeIngredient

describe('useIngredientSwaps', () => {
  it('shows the recipe ingredient until an alternative is chosen', () => {
    const swaps = useIngredientSwaps()

    expect(swaps.display(line)).toEqual({ name: 'Lait', quantity: 250, unit: 'ml', swapped: null })
  })

  it("shows the chosen alternative's ingredient and quantity, and goes back to the original", () => {
    const swaps = useIngredientSwaps()

    swaps.choose(line, vegan)
    expect(swaps.display(line)).toMatchObject({ name: "Lait d'avoine", quantity: 300, unit: 'ml', swapped: vegan })

    swaps.choose(line, null)
    expect(swaps.display(line).swapped).toBeNull()
  })

  it('keeps the line ingredient for a reduced quantity', () => {
    const swaps = useIngredientSwaps()

    swaps.choose(line, less)

    expect(swaps.display(line)).toMatchObject({ name: 'Lait', quantity: 100, swapped: less })
  })

  it('handles lines without alternatives, and swaps each line independently', () => {
    const swaps = useIngredientSwaps()
    const plain = { ...line, id: 6, alternatives: undefined } as RecipeIngredient

    swaps.choose(line, vegan)

    expect(swaps.alternativesOf(plain)).toEqual([])
    expect(swaps.display(plain).swapped).toBeNull()
  })
})
