import client from './client'

export function listIngredients(params = {}) {
  return client.get('ingredients/', { params }).then((r) => r.data)
}

export function createIngredient(payload) {
  return client.post('ingredients/', payload).then((r) => r.data)
}
