import client from './client'

export function listShoppingLists(params = {}) {
  return client.get('shopping-lists/', { params }).then((r) => r.data)
}

export function getShoppingList(id) {
  return client.get(`shopping-lists/${id}/`).then((r) => r.data)
}

export function createShoppingList(mealPlanEntryIds, name) {
  return client
    .post('shopping-lists/', { meal_plan_entry_ids: mealPlanEntryIds, name })
    .then((r) => r.data)
}

export function deleteShoppingList(id) {
  return client.delete(`shopping-lists/${id}/`)
}

export function markOwned(id, ingredientIds) {
  return client.post(`shopping-lists/${id}/mark_owned/`, { ingredient_ids: ingredientIds }).then((r) => r.data)
}

export function exportShoppingList(id) {
  return client.get(`shopping-lists/${id}/export/`).then((r) => r.data)
}
