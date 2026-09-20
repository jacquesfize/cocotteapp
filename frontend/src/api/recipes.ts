import client from './client'
import type { Paginated, RecipeListParams } from '../types/api'
import type {
  DietType,
  Recipe,
  RecipeComment,
  RecipeCommentInput,
  RecipeInput,
  RecipeNutrition,
  Tag,
} from '../types/models'

export interface CooklangImportInput {
  title: string
  raw_cooklang: string
  servings?: number
  prep_time_minutes?: number
  cook_time_minutes?: number
  diet_type?: DietType
}

export function listRecipes(params: RecipeListParams = {}): Promise<Paginated<Recipe>> {
  return client.get('recipes/', { params }).then((r) => r.data)
}

export function getRecipe(id: number | string): Promise<Recipe> {
  return client.get(`recipes/${id}/`).then((r) => r.data)
}

export function getRandomRecipe(params: RecipeListParams = {}): Promise<Recipe> {
  return client.get('recipes/random/', { params }).then((r) => r.data)
}

export function getRecipeNutrition(id: number | string): Promise<RecipeNutrition> {
  return client.get(`recipes/${id}/nutrition/`).then((r) => r.data)
}

export function createRecipe(payload: RecipeInput): Promise<Recipe> {
  return client.post('recipes/', payload).then((r) => r.data)
}

export function importRecipeFromCooklang(payload: CooklangImportInput): Promise<Recipe> {
  return client.post('recipes/import-cooklang/', payload).then((r) => r.data)
}

export function updateRecipe(id: number | string, payload: RecipeInput): Promise<Recipe> {
  return client.patch(`recipes/${id}/`, payload).then((r) => r.data)
}

export function deleteRecipe(id: number | string) {
  return client.delete(`recipes/${id}/`)
}

export function listTags(): Promise<Paginated<Tag>> {
  return client.get('tags/').then((r) => r.data)
}

export function uploadRecipeImage(id: number | string, file: File): Promise<Recipe> {
  const formData = new FormData()
  formData.append('image', file)
  return client.patch(`recipes/${id}/image/`, formData).then((r) => r.data)
}

export function downloadRecipePdf(id: number | string): Promise<Blob> {
  return client.get(`recipes/${id}/pdf/`, { responseType: 'blob' }).then((r) => r.data)
}

export function forkRecipe(id: number | string, versionLabel: string): Promise<Recipe> {
  return client.post(`recipes/${id}/fork/`, { version_label: versionLabel }).then((r) => r.data)
}

export function listRecipeComments(recipeId: number | string): Promise<Paginated<RecipeComment>> {
  return client.get(`recipes/${recipeId}/comments/`).then((r) => r.data)
}

export function createRecipeComment(
  recipeId: number | string,
  payload: RecipeCommentInput,
): Promise<RecipeComment> {
  return client.post(`recipes/${recipeId}/comments/`, payload).then((r) => r.data)
}

export function hideRecipeComment(
  recipeId: number | string,
  commentId: number | string,
): Promise<RecipeComment> {
  return client.post(`recipes/${recipeId}/comments/${commentId}/hide/`).then((r) => r.data)
}

export interface RecipeArchiveImportResult {
  created: number
  skipped: number
  errors: { title: string; detail: string }[]
}

export function exportRecipeLibrary(scope: 'mine' | 'all' = 'mine'): Promise<Blob> {
  const params = scope === 'all' ? { scope } : {}
  return client.get('recipes/export/', { params, responseType: 'blob' }).then((r) => r.data)
}

export function importRecipeLibrary(file: File): Promise<RecipeArchiveImportResult> {
  const body = new FormData()
  body.append('file', file)
  return client.post('recipes/import-archive/', body).then((r) => r.data)
}
