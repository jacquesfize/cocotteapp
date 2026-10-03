import client from './client'
import type { MealPlanEntryListParams, PlanningSharePayload } from '../types/api'
import type { MealPlanEntry, NutritionSummary, PlanningShare, PlanningShareReceived } from '../types/models'

export function listMealPlanEntries(params: MealPlanEntryListParams = {}): Promise<MealPlanEntry[]> {
  return client.get('meal-plan-entries/', { params }).then((r) => r.data)
}

export function createMealPlanEntry(
  payload: Pick<MealPlanEntry, 'recipe' | 'date' | 'meal_type' | 'servings'>,
  owner?: number | string,
): Promise<MealPlanEntry> {
  return client.post('meal-plan-entries/', payload, { params: owner ? { owner } : {} }).then((r) => r.data)
}

export function deleteMealPlanEntry(id: number | string, owner?: number | string) {
  return client.delete(`meal-plan-entries/${id}/`, { params: owner ? { owner } : {} })
}

export function updateMealPlanEntry(
  id: number | string,
  payload: Partial<Pick<MealPlanEntry, 'date' | 'meal_type' | 'servings'>>,
  owner?: number | string,
): Promise<MealPlanEntry> {
  return client.patch(`meal-plan-entries/${id}/`, payload, { params: owner ? { owner } : {} }).then((r) => r.data)
}

export function getNutritionSummary(params: MealPlanEntryListParams = {}): Promise<NutritionSummary> {
  return client.get('meal-plan-entries/nutrition_summary/', { params }).then((r) => r.data)
}

export function downloadWeekPdf(params: MealPlanEntryListParams = {}): Promise<Blob> {
  return client.get('meal-plan-entries/week-pdf/', { params, responseType: 'blob' }).then((r) => r.data)
}

export interface CalendarFeed {
  token: string
  url: string
  webcal_url: string
}

export function downloadWeekIcs(params: MealPlanEntryListParams = {}): Promise<Blob> {
  return client.get('meal-plan-entries/ics/', { params, responseType: 'blob' }).then((r) => r.data)
}

export function getCalendarFeed(): Promise<CalendarFeed> {
  return client.get('planning/calendar-feed/').then((r) => r.data)
}

export function regenerateCalendarFeed(): Promise<CalendarFeed> {
  return client.post('planning/calendar-feed/').then((r) => r.data)
}

export function listPlanningShares(): Promise<PlanningShare[]> {
  return client.get('planning-shares/').then((r) => r.data)
}

export function listSharedWithMe(): Promise<PlanningShareReceived[]> {
  return client.get('planning-shares/shared-with-me/').then((r) => r.data)
}

export function createOrUpdatePlanningShare(payload: PlanningSharePayload): Promise<PlanningShare> {
  return client.post('planning-shares/', payload).then((r) => r.data)
}

export function deletePlanningShare(id: number | string) {
  return client.delete(`planning-shares/${id}/`)
}
