export function recipeImageUrl(entity: { image: string | null; image_url: string }): string | null {
  return entity.image || entity.image_url || null
}
