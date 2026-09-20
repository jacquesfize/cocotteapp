// Emoji par slug d'allergène (cf. backend `seed_allergens`). Les emojis n'existent pas
// pour tous les allergènes (sésame, moutarde, sulfites, lupin) : ce sont des approximations.
const ALLERGEN_EMOJIS: Record<string, string> = {
  gluten: '🌾',
  milk: '🥛',
  lactose: '🧀',
  egg: '🥚',
  peanut: '🥜',
  tree_nuts: '🌰',
  soy: '🫘',
  fish: '🐟',
  crustaceans: '🦐',
  molluscs: '🦪',
  celery: '🥬',
  mustard: '🟡',
  sesame: '🥯',
  sulphites: '🍷',
  lupin: '🌸',
}

export function allergenEmoji(slug: string): string {
  return ALLERGEN_EMOJIS[slug] ?? '⚠️'
}

export interface AllergenMatches {
  allergies: string[]
  intolerances: string[]
}

// Allergènes d'une recette qui concernent l'utilisateur, séparés par sévérité.
export function matchUserAllergens(
  recipeAllergens: string[] | undefined,
  user: { allergies?: string[]; intolerances?: string[] } | null | undefined,
): AllergenMatches {
  const slugs = recipeAllergens ?? []
  return {
    allergies: slugs.filter((s) => user?.allergies?.includes(s)),
    intolerances: slugs.filter((s) => user?.intolerances?.includes(s)),
  }
}
