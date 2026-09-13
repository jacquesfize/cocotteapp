import client from './client'
import type { Paginated } from '../types/api'
import type { ShoppingList } from '../types/models'

export function listShoppingLists(params: { page?: number } = {}): Promise<Paginated<ShoppingList>> {
  return client.get('shopping-lists/', { params }).then((r) => r.data)
}

export function getShoppingList(id: number | string): Promise<ShoppingList> {
  return client.get(`shopping-lists/${id}/`).then((r) => r.data)
}

export function createShoppingList(mealPlanEntryIds: number[], name?: string): Promise<ShoppingList> {
  return client
    .post('shopping-lists/', { meal_plan_entry_ids: mealPlanEntryIds, name })
    .then((r) => r.data)
}

export function deleteShoppingList(id: number | string) {
  return client.delete(`shopping-lists/${id}/`)
}

export function markOwned(id: number | string, ingredientIds: number[]): Promise<ShoppingList> {
  return client.post(`shopping-lists/${id}/mark_owned/`, { ingredient_ids: ingredientIds }).then((r) => r.data)
}

export function exportShoppingList(id: number | string): Promise<{ content: string }> {
  return client.get(`shopping-lists/${id}/export/`).then((r) => r.data)
}
