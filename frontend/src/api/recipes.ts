import client from './client'
import type { Paginated, RecipeListParams } from '../types/api'
import type {
  CooklangPreview,
  PersonalTag,
  Recipe,
  RecipeComment,
  RecipeCommentInput,
  RecipeInput,
  RecipeNutrition,
  RecipeStep,
  Tag,
} from '../types/models'

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

export interface CooklangPreviewInput {
  title?: string
  raw_cooklang: string
  servings?: number
}

/** Parse du Cooklang sans rien créer, pour pré-remplir le formulaire de recette. */
export function previewRecipeFromCooklang(payload: CooklangPreviewInput): Promise<CooklangPreview> {
  return client.post('recipes/preview-cooklang/', payload).then((r) => r.data)
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

/** Remplace l'ensemble des étiquettes personnelles du visiteur sur cette recette. */
export function setRecipeTags(id: number | string, tagIds: number[]): Promise<PersonalTag[]> {
  return client.put(`recipes/${id}/my-tags/`, { tag_ids: tagIds }).then((r) => r.data)
}

export interface ImageCreditInput {
  image_license: string
  image_credit_author?: string
  image_credit_source_url?: string
  image_credit_license_url?: string
  image_credit_note?: string
}

function appendCredit(formData: FormData, credit: ImageCreditInput) {
  formData.append('image_license', credit.image_license)
  if (credit.image_credit_author) formData.append('image_credit_author', credit.image_credit_author)
  if (credit.image_credit_source_url) formData.append('image_credit_source_url', credit.image_credit_source_url)
  if (credit.image_credit_license_url) formData.append('image_credit_license_url', credit.image_credit_license_url)
  if (credit.image_credit_note) formData.append('image_credit_note', credit.image_credit_note)
}

export function uploadRecipeImage(id: number | string, file: File, credit: ImageCreditInput): Promise<Recipe> {
  const formData = new FormData()
  formData.append('image', file)
  appendCredit(formData, credit)
  return client.patch(`recipes/${id}/image/`, formData).then((r) => r.data)
}

export function uploadStepImage(
  recipeId: number | string,
  stepId: number | string,
  file: File,
  credit: ImageCreditInput,
): Promise<RecipeStep> {
  const formData = new FormData()
  formData.append('image', file)
  appendCredit(formData, credit)
  return client.patch(`recipes/${recipeId}/steps/${stepId}/image/`, formData).then((r) => r.data)
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

export interface RecipeRatingResult {
  average_rating: number | null
  ratings_count: number
  my_rating: number
}

export function rateRecipe(recipeId: number | string, value: number): Promise<RecipeRatingResult> {
  return client.post(`recipes/${recipeId}/rate/`, { value }).then((r) => r.data)
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
