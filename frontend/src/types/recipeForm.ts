import type { AlternativeTag, Ingredient, Unit } from './models'

// Alternative en cours d'édition d'une ligne (voir IngredientSections.vue).
export interface AlternativeFormRow {
  ingredient: Ingredient | null
  quantity: string | number
  unit: Unit
  tag: AlternativeTag
  note: string
}

// Une ligne d'ingrédient du formulaire de recette. `group_name` est le nom de la section où elle
// se trouve ('' = section sans nom, toujours affichée en premier).
export interface IngredientFormRow {
  ingredient: Ingredient | null
  quantity: string | number
  unit: Unit
  group_name: string
  order: number
  // Ligne importée depuis une recette scrapée dont l'ingrédient n'a pas pu être rapproché
  // automatiquement du catalogue (voir apps/importer/services.py::find_matching_ingredient) :
  // affiche un badge (+ le texte d'origine pour aider) tant qu'aucun ingrédient n'a été
  // choisi/créé ici.
  unmatched?: boolean
  raw_line?: string
  alternatives?: AlternativeFormRow[]
}

export const INGREDIENT_UNITS: Unit[] = ['g', 'kg', 'ml', 'l', 'piece', 'tbsp', 'tsp', 'pinch']

export const ALTERNATIVE_TAGS: AlternativeTag[] = ['vegan', 'vegetarian', 'gluten_free', 'lactose_free', 'missing', 'less']
