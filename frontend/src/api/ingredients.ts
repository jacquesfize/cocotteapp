import client from './client'
import type { IngredientListParams, Paginated } from '../types/api'
import type { Ingredient } from '../types/models'

export function listIngredients(params: IngredientListParams = {}): Promise<Paginated<Ingredient>> {
  return client.get('ingredients/', { params }).then((r) => r.data)
}

export function createIngredient(payload: Partial<Ingredient>): Promise<Ingredient> {
  return client.post('ingredients/', payload).then((r) => r.data)
}
