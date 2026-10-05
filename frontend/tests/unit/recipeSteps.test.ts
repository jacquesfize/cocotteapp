import { describe, expect, it } from 'vitest'
import { buildStepSegments, ingredientRowsFor } from '../../src/utils/recipeSteps'
import type { RecipeIngredient } from '../../src/types/models'

const lentils = { ingredient: { id: 7, name: 'lentilles' } } as unknown as RecipeIngredient

describe('buildStepSegments', () => {
  it('links a mention of a recipe ingredient, shown by its readable name', () => {
    const segments = buildStepSegments('Cuire les @lentilles 20 minutes', [lentils])
    expect(segments).toEqual([{ text: 'Cuire les ' }, { text: 'lentilles', ingredientId: 7, ingredientIndex: 0 }, { text: ' 20 minutes' }])
  })

  it('keeps an unknown mention as typed, "@" included, instead of silently dropping it', () => {
    const segments = buildStepSegments('Cuire les @len 20 minutes', [lentils])
    expect(segments.map((segment) => segment.text).join('')).toBe('Cuire les @len 20 minutes')
    expect(segments.some((segment) => segment.ingredientId)).toBe(false)
  })

  it('points a mention at the first row when the ingredient is used in several parts', () => {
    const butterDough = { id: 1, ingredient: { id: 3, name: 'beurre' }, group_name: 'Pâte' } as unknown as RecipeIngredient
    const salt = { id: 2, ingredient: { id: 4, name: 'sel' }, group_name: 'Pâte' } as unknown as RecipeIngredient
    const butterFilling = { id: 3, ingredient: { id: 3, name: 'beurre' }, group_name: 'Garniture' } as unknown as RecipeIngredient
    const rows = [butterDough, salt, butterFilling]

    const segments = buildStepSegments('Ajouter le @beurre', rows)
    expect(segments[1]).toMatchObject({ ingredientId: 3, ingredientIndex: 0 })
    expect(ingredientRowsFor(rows, 3)).toEqual([butterDough, butterFilling])
  })
})
