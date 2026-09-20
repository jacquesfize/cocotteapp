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
export type RecipeSourceType = 'manual' | 'url' | 'cooklang'
export type TagKind = 'meal_type' | 'cuisine' | 'other'

export interface User {
  id: number
  username: string
  email: string
  diet_type: DietType
  activity_level: ActivityLevel
  is_staff: boolean
  date_joined: string
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

export interface Tag {
  id: number
  name: string
  kind: TagKind
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
}

export interface RecipeVersion {
  id: number
  slug: string
  title: string
  version_label: string
  author: string
}

export interface RecipeComment {
  id: number
  recipe: number
  author_name: string
  username: string | null
  body: string
  is_hidden?: boolean
  created_at: string
}

export interface RecipeCommentInput {
  author_name?: string
  body: string
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
  is_public: boolean
  tags: Tag[]
  ingredients: RecipeIngredient[]
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
  instruction: string
  order: number
}

export interface RecipeInput {
  title: string
  description: string
  servings: number
  prep_time_minutes: number
  cook_time_minutes: number
  diet_type: DietType
  is_public: boolean
  source_url: string
  video_url: string
  image_url: string
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
  image_url: string
  source_url: string
  steps: ImportPreviewStep[]
  ingredients: ImportPreviewIngredient[]
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
