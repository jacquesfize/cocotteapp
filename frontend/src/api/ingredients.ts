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

// Réservé au staff : fusionne l'ingrédient `id` dans `into` (recettes et listes de courses
// basculent sur la cible, puis `id` est supprimé). Renvoie l'ingrédient cible.
export function mergeIngredient(id: number, into: number): Promise<Ingredient> {
  return client.post(`ingredients/${id}/merge/`, { into }).then((r) => r.data)
}

export interface NutritionSuggestionResponse {
  found: boolean
  suggestion?: Partial<NutrientTotals> & { carbon_kg_co2e_per_kg?: number }
}

export function suggestIngredientNutrition(name: string): Promise<NutritionSuggestionResponse> {
  return client.get('ingredients/nutrition-suggestion/', { params: { name } }).then((r) => r.data)
}
