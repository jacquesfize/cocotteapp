import client from './client'
import type { IngredientListParams, Paginated } from '../types/api'
import type { Ingredient, NutrientTotals } from '../types/models'

export function listIngredients(params: IngredientListParams = {}): Promise<Paginated<Ingredient>> {
  return client.get('ingredients/', { params }).then((r) => r.data)
}

export function createIngredient(payload: Partial<Ingredient>): Promise<Ingredient> {
  return client.post('ingredients/', payload).then((r) => r.data)
}

export function updateIngredient(id: number, payload: Partial<Ingredient>): Promise<Ingredient> {
  return client.patch(`ingredients/${id}/`, payload).then((r) => r.data)
}

export function deleteIngredient(id: number) {
  return client.delete(`ingredients/${id}/`)
}

export interface NutritionSuggestionResponse {
  found: boolean
  suggestion?: Partial<NutrientTotals> & { carbon_kg_co2e_per_kg?: number }
}

export function suggestIngredientNutrition(name: string): Promise<NutritionSuggestionResponse> {
  return client.get('ingredients/nutrition-suggestion/', { params: { name } }).then((r) => r.data)
}
