import client from './client'
import type { MealPlanEntryListParams } from '../types/api'
import type { MealPlanEntry, NutritionSummary } from '../types/models'

export function listMealPlanEntries(params: MealPlanEntryListParams = {}): Promise<MealPlanEntry[]> {
  return client.get('meal-plan-entries/', { params }).then((r) => r.data)
}

export function createMealPlanEntry(
  payload: Pick<MealPlanEntry, 'recipe' | 'date' | 'meal_type' | 'servings'>,
): Promise<MealPlanEntry> {
  return client.post('meal-plan-entries/', payload).then((r) => r.data)
}

export function deleteMealPlanEntry(id: number | string) {
  return client.delete(`meal-plan-entries/${id}/`)
}

export function getNutritionSummary(params: MealPlanEntryListParams = {}): Promise<NutritionSummary> {
  return client.get('meal-plan-entries/nutrition_summary/', { params }).then((r) => r.data)
}

export function downloadWeekPdf(params: MealPlanEntryListParams = {}): Promise<Blob> {
  return client.get('meal-plan-entries/week-pdf/', { params, responseType: 'blob' }).then((r) => r.data)
}
