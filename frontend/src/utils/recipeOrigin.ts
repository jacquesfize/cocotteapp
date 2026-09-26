import type { Recipe } from '../types/models'

/**
 * Une recette est considérée comme importée si elle vient d'une source externe. `source_type`
 * seul ne suffit pas : l'import par URL passe par le formulaire de création standard, qui laisse
 * `source_type` à "manual" — c'est la présence d'une URL source/vidéo qui trahit l'import.
 */
export function isImportedRecipe(recipe: Pick<Recipe, 'source_type' | 'source_url' | 'video_url'>): boolean {
  return (
    (Boolean(recipe.source_type) && recipe.source_type !== 'manual') ||
    Boolean(recipe.source_url) ||
    Boolean(recipe.video_url)
  )
}
