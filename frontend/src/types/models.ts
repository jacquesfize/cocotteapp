export type DietType = 'omnivore' | 'vegetarian' | 'vegan'
export type ActivityLevel = 'sedentary' | 'moderate' | 'athlete'
export type Unit = 'g' | 'kg' | 'ml' | 'l' | 'piece' | 'tbsp' | 'tsp' | 'pinch'
export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack'
export type PlanningPermission = 'read' | 'write'
export type IngredientCategory =
  | 'vegetable'
  | 'fruit'
  | 'legume'
  | 'grain'
  | 'nut_seed'
  | 'dairy'
  | 'meat_fish'
  | 'egg'
  | 'fat'
  | 'condiment'
  | 'other'
export type RecipeSourceType = 'manual' | 'url' | 'cooklang' | 'youtube'
export type TagKind = 'meal_type' | 'cuisine' | 'other'

export interface Allergen {
  slug: string
  name: string
}

export interface User {
  id: number
  username: string
  email: string
  diet_type: DietType
  activity_level: ActivityLevel
  allergies: string[]
  intolerances: string[]
  is_staff: boolean
  date_joined: string
  health_data_consent_at: string | null
}

export interface LegalInfo {
  policy_version: string
  publisher_name: string
  publisher_address: string
  contact_email: string
  host_name: string
  host_address: string
  privacy_contact_email: string
  inactive_retention_days: number
  planning_snack_enabled: boolean
  nutrition_alerts_enabled: boolean
}

export interface AdminUser {
  id: number
  username: string
  email: string
  is_active: boolean
  is_staff: boolean
  date_joined: string
  recipe_count: number
}

export interface Ingredient {
  id: number
  name: string
  slug: string
  category: IngredientCategory
  default_unit: Unit
  available_months: number[]
  translations?: Record<string, string>
  allergens?: string[]
  allergens_reviewed?: boolean
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
  fiber_g: number
  iron_mg: number
  vitamin_b12_ug: number
  calcium_mg: number
  omega3_g: number
  zinc_mg: number
  carbon_kg_co2e_per_kg: number
}

export interface Cookware {
  id: number
  name: string
  slug: string
  // Un emoji représentant l'objet, s'il en existe un (vide sinon).
  emoji?: string
  // Photo relative (`/media/cookware/...`), ou null, et son crédit (mêmes règles que les recettes).
  image?: string | null
  image_license?: string
  image_credit_author?: string
  image_credit_source_url?: string
  image_credit_license_url?: string
  translations?: Record<string, string>
}

export interface Tag {
  id: number
  name: string
  kind: TagKind
}

export type TagColor = 'gray' | 'red' | 'orange' | 'yellow' | 'green' | 'teal' | 'blue' | 'purple' | 'pink'

// Étiquette personnelle : visible et modifiable par son seul propriétaire, posée sur n'importe
// quelle recette (`Recipe.my_tags`). `recipes_count` n'est renvoyé que par /api/personal-tags/.
export interface PersonalTag {
  id: number
  name: string
  emoji: string
  color: TagColor
  recipes_count?: number
}

export interface ThematicPage {
  id: number
  title: string
  slug: string
  description: string
  icon: string
  image: string | null
  filters: Record<string, string>
  order: number
}

export interface AdminThematicPage extends ThematicPage {
  is_active: boolean
  created_at: string
}

export interface RecipeIngredient {
  id: number
  ingredient: Ingredient
  quantity: number
  unit: Unit
  group_name: string
  order: number
}

export interface RecipeStep {
  id: number
  order: number
  instruction: string
  image: string | null
  image_url: string
  image_license: string
  image_credit_author: string
  image_credit_source_url: string
  image_credit_license_url: string
  image_credit_note: string
}

export interface RecipeVersion {
  id: number
  slug: string
  title: string
  version_label: string
  author: string
}

export interface Comment {
  id: number
  author_name: string
  username: string | null
  body: string
  is_hidden?: boolean
  created_at: string
}

export interface CommentInput {
  author_name?: string
  body: string
}

export interface RecipeComment extends Comment {
  recipe: number
}

export type RecipeCommentInput = CommentInput

export interface BlogPostComment extends Comment {
  post: number
}

/** A blog post as listed by `GET /api/blog/posts/`: no HTML content, an excerpt instead. */
export interface BlogPostSummary {
  id: number
  title: string
  author: string
  author_id: number
  excerpt: string
  cover_image: string | null
  comments_enabled: boolean
  created_at: string
  updated_at: string
}

export interface BlogPost {
  id: number
  title: string
  author: string
  author_id: number
  /** HTML, sanitized server-side. */
  content: string
  cover_image: string | null
  comments_enabled: boolean
  created_at: string
  updated_at: string
}

export interface BlogAuthor {
  id: number
  username: string
}

export interface BlogPostInput {
  title: string
  content: string
  comments_enabled: boolean
}

export interface BlogImage {
  id: number
  image: string
  created_at: string
}

export interface Recipe {
  id: number
  title: string
  slug: string
  description: string
  author: string
  author_id: number
  servings: number
  prep_time_minutes: number
  cook_time_minutes: number
  total_time_minutes: number
  diet_type: DietType
  source_type: RecipeSourceType
  source_url: string
  video_url: string
  youtube_id: string | null
  image: string | null
  image_url: string
  image_license: string
  image_credit_author: string
  image_credit_source_url: string
  image_credit_license_url: string
  image_credit_note: string
  is_public: boolean
  content_publicly_licensed: boolean
  content_restricted: boolean
  carbon_footprint_kg_co2e: number
  average_rating: number | null
  ratings_count: number
  my_rating: number | null
  // Étiquettes personnelles du visiteur connecté sur cette recette (vide si anonyme).
  my_tags: PersonalTag[]
  tags: Tag[]
  cookware: Cookware[]
  ingredients: RecipeIngredient[]
  allergens: string[]
  allergens_unverified: boolean
  steps: RecipeStep[]
  root_recipe: number | null
  version_label: string
  versions: RecipeVersion[]
  created_at: string
  updated_at: string
}

export interface RecipeIngredientInput {
  ingredient_id: number
  quantity: number | string
  unit: Unit
  group_name: string
  order: number
}

export interface RecipeStepInput {
  id?: number
  instruction: string
  order: number
  image_url?: string
  image_license?: string
  image_credit_author?: string
  image_credit_source_url?: string
  image_credit_license_url?: string
  image_credit_note?: string
}

export interface RecipeInput {
  title: string
  description: string
  servings: number
  prep_time_minutes: number
  cook_time_minutes: number
  diet_type: DietType
  is_public: boolean
  content_publicly_licensed: boolean
  source_url: string
  video_url: string
  image_url: string
  image_license?: string
  image_credit_author?: string
  image_credit_source_url?: string
  image_credit_license_url?: string
  image_credit_note?: string
  // Seulement à la création d'une recette pré-remplie depuis du Cooklang collé.
  source_type?: RecipeSourceType
  cookware_ids: number[]
  ingredients: RecipeIngredientInput[]
  steps: RecipeStepInput[]
}

export interface ImportPreviewIngredient {
  raw_line: string
  quantity: string
  unit: Unit
  name: string
  ingredient: Ingredient | null
}

export interface ImportPreviewStep {
  order: number
  instruction: string
}

export interface ImportPreview {
  title: string
  servings: number
  cook_time_minutes: number
  source_url: string
  steps: ImportPreviewStep[]
  ingredients: ImportPreviewIngredient[]
}

// `POST /api/recipes/preview-cooklang/` : même forme que l'aperçu d'un import d'URL, plus ce que
// les métadonnées Cooklang peuvent porter. Les champs absents du texte (et non saisis) sont `null`.
export interface CooklangPreview {
  title: string
  description: string
  servings: number | null
  prep_time_minutes: number | null
  cook_time_minutes: number | null
  source_url: string
  steps: ImportPreviewStep[]
  ingredients: (ImportPreviewIngredient & { group_name: string })[]
  // `#matériel` du texte : rapproché de la bibliothèque, ou `null` (à créer dans le formulaire).
  cookware: { name: string; cookware: Cookware | null }[]
}

// Image libre de droits proposée par `GET /api/import/image-suggestions/` (Openverse), avec ses
// champs de crédit déjà au format attendu par le formulaire de recette.
export interface FreeImageSuggestion {
  url: string
  thumbnail: string
  title: string
  image_license: 'cc_by' | 'cc_by_sa' | 'public_domain'
  image_credit_author: string
  image_credit_source_url: string
  image_credit_license_url: string
}

export interface NutrientTotals {
  calories_kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
  fiber_g: number
  iron_mg: number
  vitamin_b12_ug: number
  calcium_mg: number
  omega3_g: number
  zinc_mg: number
}

export interface RecipeNutrition {
  totals: NutrientTotals
  per_serving: NutrientTotals
  carbon_footprint_kg_co2e: number
  carbon_footprint_per_serving_kg_co2e: number
}

export interface NutrientDeficiency {
  nutrient: keyof NutrientTotals
  amount: number
  minimum: number
  unit: string
}

export interface NutritionSummary {
  totals: NutrientTotals
  daily_average: NutrientTotals
  deficiencies: NutrientDeficiency[]
  carbon_footprint_kg_co2e: number
  carbon_footprint_daily_average_kg_co2e: number
}

export interface MealPlanEntry {
  id: number
  recipe: number
  recipe_title: string
  recipe_allergens?: string[]
  recipe_image: string | null
  recipe_image_url: string
  date: string
  meal_type: MealType
  servings: number
}

export interface PlanningShare {
  id: number
  shared_with_username: string
  shared_with_email: string
  permission: PlanningPermission
  created_at: string
}

export interface PlanningShareReceived {
  id: number
  owner: number
  owner_username: string
  owner_email: string
  permission: PlanningPermission
  created_at: string
}

export interface ShoppingListItem {
  id: number
  ingredient: Ingredient
  quantity: number
  unit: Unit
  is_owned: boolean
  is_checked: boolean
}

export interface ShoppingList {
  id: number
  name: string
  items: ShoppingListItem[]
  created_at: string
}
