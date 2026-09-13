import client from './client'

export function listRecipes(params = {}) {
  return client.get('recipes/', { params }).then((r) => r.data)
}

export function getRecipe(id) {
  return client.get(`recipes/${id}/`).then((r) => r.data)
}

export function getRandomRecipe(params = {}) {
  return client.get('recipes/random/', { params }).then((r) => r.data)
}

export function getRecipeNutrition(id) {
  return client.get(`recipes/${id}/nutrition/`).then((r) => r.data)
}

export function createRecipe(payload) {
  return client.post('recipes/', payload).then((r) => r.data)
}

export function updateRecipe(id, payload) {
  return client.patch(`recipes/${id}/`, payload).then((r) => r.data)
}

export function deleteRecipe(id) {
  return client.delete(`recipes/${id}/`)
}

export function listTags() {
  return client.get('tags/').then((r) => r.data)
}

export function uploadRecipeImage(id, file) {
  const formData = new FormData()
  formData.append('image', file)
  return client.patch(`recipes/${id}/image/`, formData).then((r) => r.data)
}

export function downloadRecipePdf(id) {
  return client.get(`recipes/${id}/pdf/`, { responseType: 'blob' }).then((r) => r.data)
}
