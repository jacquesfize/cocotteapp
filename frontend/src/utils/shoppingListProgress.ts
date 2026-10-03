import type { ShoppingList } from '../types/models'

export function shoppingListProgress(list: Pick<ShoppingList, 'items'> | null | undefined) {
  const items = list?.items ?? []
  const owned = items.filter((item) => item.is_owned).length
  const total = items.length
  const percent = total ? Math.round((owned / total) * 100) : 0
  return { owned, total, percent }
}
