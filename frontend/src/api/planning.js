import client from './client'

export function listMealPlanEntries(params = {}) {
  return client.get('meal-plan-entries/', { params }).then((r) => r.data)
}

export function createMealPlanEntry(payload) {
  return client.post('meal-plan-entries/', payload).then((r) => r.data)
}

export function deleteMealPlanEntry(id) {
  return client.delete(`meal-plan-entries/${id}/`)
}

export function getNutritionSummary(params = {}) {
  return client.get('meal-plan-entries/nutrition_summary/', { params }).then((r) => r.data)
}
