import type { ActivityLevel, DietType, MealType, PlanningPermission } from './models'

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface RecipeListParams {
  search?: string
  diet_type?: DietType | ''
  max_prep_time?: number | string
  max_cook_time?: number | string
  ingredients?: string
  in_season?: boolean
  carbon_level?: 'low' | 'medium' | 'high' | ''
  max_carbon?: number | string
  exclude_allergens?: string
  // Slugs de matériel séparés par des virgules : recettes qui en utilisent au moins un.
  cookware?: string
  // Identifiants d'étiquettes personnelles séparés par des virgules : recettes qui en portent au moins une.
  personal_tags?: string
  page?: number
  page_size?: number
}

export interface BlogPostListParams {
  author?: number
  search?: string
  page?: number
}

export interface IngredientListParams {
  category?: string
  in_season?: boolean
  search?: string
  page?: number
  // `false` : file de revue des administrateurs (ingrédients créés par des utilisateurs).
  is_verified?: boolean
}

export interface MealPlanEntryListParams {
  date_after?: string
  date_before?: string
  meal_type?: MealType
  owner?: number | string
}

export interface PlanningSharePayload {
  email: string
  permission: PlanningPermission
}

export interface AdminUserListParams {
  search?: string
  page?: number
}

export interface AdminThematicPageInput {
  title: string
  description: string
  icon: string
  filters: Record<string, string>
  order: number
  is_active: boolean
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  diet_type?: DietType
  activity_level?: ActivityLevel
  health_data_consent?: boolean
}

export interface ChangePasswordPayload {
  old_password: string
  new_password: string
}

export interface PasswordResetConfirmPayload {
  uid: string
  token: string
  new_password: string
}

export interface TokenPair {
  access: string
  refresh: string
}
