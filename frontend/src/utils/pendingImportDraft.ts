import type { Cookware, Ingredient, Unit } from '../types/models'

// Passage de main en mémoire entre RecipeListView (lancement de l'import) et RecipeFormView
// (vérification/correction des ingrédients rapprochés + édition + soumission, qui a déjà tout
// le nécessaire : IngredientPicker par ligne, blocage de la soumission tant qu'une ligne n'a pas
// d'ingrédient) : ce n'est pas un état d'appli partagé mais un pur relais d'une navigation à
// l'autre dans la même session SPA, donc pas de store Pinia (le seul store du projet,
// stores/auth.js, ne porte que l'authentification).
export interface PendingImportIngredientRow {
  ingredient: Ingredient | null
  quantity: string | number
  unit: Unit
  // Ligne brute telle que scrapée (ex. "1 oignon moyen") : affichée en aide dans
  // RecipeFormView tant que l'ingrédient n'a pas été rapproché, pour donner du contexte quand
  // le nom parsé seul ne suffit pas à retrouver/recréer le bon ingrédient.
  raw_line: string
  group_name?: string
}

export interface PendingImportDraft {
  title: string
  servings: number
  cook_time_minutes: number
  source_url: string
  // Seulement pour un aperçu Cooklang (RecipeFormView.vue::handleCooklangSubmit), qui ne passe
  // pas par ce relais mais pré-remplit le formulaire par la même fonction.
  description?: string
  prep_time_minutes?: number
  source_type?: 'cooklang'
  cookware?: { name: string; cookware: Cookware | null }[]
  steps: { instruction: string; order: number }[]
  ingredients: PendingImportIngredientRow[]
}

let pendingDraft: PendingImportDraft | null = null

export function setPendingImportDraft(draft: PendingImportDraft) {
  pendingDraft = draft
}

export function takePendingImportDraft(): PendingImportDraft | null {
  const draft = pendingDraft
  pendingDraft = null
  return draft
}
