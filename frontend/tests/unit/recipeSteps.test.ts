import { describe, expect, it } from 'vitest'
import { buildStepSegments } from '../../src/utils/recipeSteps'
import type { RecipeIngredient } from '../../src/types/models'

const lentils = { ingredient: { id: 7, name: 'lentilles' } } as unknown as RecipeIngredient

describe('buildStepSegments', () => {
  it('links a mention of a recipe ingredient, shown by its readable name', () => {
    const segments = buildStepSegments('Cuire les @lentilles 20 minutes', [lentils])
    expect(segments).toEqual([{ text: 'Cuire les ' }, { text: 'lentilles', ingredientId: 7 }, { text: ' 20 minutes' }])
  })

  it('keeps an unknown mention as typed, "@" included, instead of silently dropping it', () => {
    const segments = buildStepSegments('Cuire les @len 20 minutes', [lentils])
    expect(segments.map((segment) => segment.text).join('')).toBe('Cuire les @len 20 minutes')
    expect(segments.some((segment) => segment.ingredientId)).toBe(false)
  })
})
