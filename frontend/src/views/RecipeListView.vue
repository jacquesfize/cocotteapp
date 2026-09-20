<script setup lang="ts">
import { Link2, Plus, X } from '@lucide/vue'
import { nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, type LocationQuery, type LocationQueryRaw } from 'vue-router'
import Pagination from '../components/Pagination.vue'
import RecipeCard from '../components/RecipeCard.vue'
import RecipeFilters, { type RecipeFilterValues } from '../components/RecipeFilters.vue'
import { previewImportFromUrl } from '../api/importer'
import { listRecipes } from '../api/recipes'
import { useAuthStore } from '../stores/auth'
import { setPendingImportDraft } from '../utils/pendingImportDraft'
import type { RecipeListParams } from '../types/api'
import type { Recipe } from '../types/models'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const recipes = ref<Recipe[]>([])
const count = ref(0)
const isLoading = ref(false)

function filtersFromQuery(query: LocationQuery): RecipeFilterValues {
  return {
    search: (query.search as string) || '',
    diet_type: (query.diet_type as string) || '',
    max_prep_time: (query.max_prep_time as string) || '',
    max_cook_time: (query.max_cook_time as string) || '',
    ingredients: (query.ingredients as string) || '',
    in_season: query.in_season === 'true',
    carbon_level: (query.carbon_level as string) || '',
  }
}

function pageFromQuery(query: LocationQuery) {
  return Number(query.page) || 1
}

// Le routeur déclenche ses hooks afterEach (ex. la fermeture du menu compte dans NavBar.vue)
// pour toute navigation, même un router.replace() vers une query string strictement
// identique. Sans cette comparaison, chaque chargement de la liste — y compris le cas le
// plus courant, sans filtre — émettait une navigation "pour rien" quelques centaines de ms
// après le montage, qui pouvait entrer en collision avec ce que l'utilisateur faisait entre
// temps (ouvrir le menu compte, cliquer sur un lien) et annuler cette action silencieusement.
function queryMatches(current: LocationQuery, next: Record<string, unknown>) {
  const currentKeys = Object.keys(current).filter((key) => current[key] !== undefined && current[key] !== '')
  const nextKeys = Object.keys(next).filter((key) => next[key] !== undefined && next[key] !== '')
  if (currentKeys.length !== nextKeys.length) return false
  return currentKeys.every((key) => String(current[key]) === String(next[key]))
}

// Les filtres vivent dans l'URL (query string) : /recipes?ingredients=Tomate ou
// /recipes?in_season=true deviennent ainsi de vraies pages thématiques, partageables.
const filters = ref<RecipeFilterValues>(filtersFromQuery(route.query))
const page = ref(pageFromQuery(route.query))

async function load() {
  isLoading.value = true
  try {
    const params: RecipeListParams = {}
    for (const [key, value] of Object.entries(filters.value)) {
      if (value !== '' && value !== false) (params as Record<string, unknown>)[key] = value
    }
    if (page.value > 1) params.page = page.value
    const data = await listRecipes(params)
    recipes.value = data.results
    count.value = data.count
    if (!queryMatches(route.query, params as Record<string, unknown>)) {
      router.replace({ query: params as unknown as LocationQueryRaw })
    }
  } finally {
    isLoading.value = false
  }
}

function goToPage(newPage: number) {
  page.value = newPage
  load()
}

let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(
  filters,
  () => {
    page.value = 1
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(load, 300)
  },
  { deep: true },
)

// Permet à un lien interne (ex. "Produits de saison", ou un ingrédient cliqué
// depuis une recette) de mettre à jour les filtres même si l'on est déjà sur
// cette page — seule la query string change alors, le composant n'est pas remonté.
watch(
  () => route.query,
  (query) => {
    const next = filtersFromQuery(query)
    const changed = (Object.keys(next) as Array<keyof typeof next>).some(
      (key) => next[key] !== filters.value[key],
    )
    if (changed) filters.value = next
    const nextPage = pageFromQuery(query)
    if (nextPage !== page.value) page.value = nextPage
  },
)

onMounted(load)

const importUrl = ref('')
const importError = ref('')
const isImporting = ref(false)
const showImportForm = ref(false)
const importUrlInput = ref<HTMLInputElement | null>(null)

function toggleImportForm() {
  showImportForm.value = !showImportForm.value
  if (showImportForm.value) {
    nextTick(() => importUrlInput.value?.focus())
  }
}

// Le scraping est rapproché du catalogue d'ingrédients (voir apps/importer/services.py) mais
// ne crée rien en base : le brouillon part directement vers le formulaire de création de
// recette, qui a déjà tout le nécessaire pour vérifier/corriger chaque ingrédient (IngredientPicker
// par ligne + soumission bloquée tant qu'une ligne n'a pas d'ingrédient choisi) — pas besoin
// d'un écran intermédiaire dédié.
async function handleImport() {
  importError.value = ''
  isImporting.value = true
  try {
    const preview = await previewImportFromUrl(importUrl.value)
    setPendingImportDraft({
      title: preview.title,
      servings: preview.servings,
      cook_time_minutes: preview.cook_time_minutes,
      image_url: preview.image_url,
      source_url: preview.source_url,
      steps: preview.steps,
      ingredients: preview.ingredients.map((item) => ({
        ingredient: item.ingredient,
        quantity: item.quantity,
        unit: item.unit,
        raw_line: item.raw_line,
      })),
    })
    router.push({ name: 'recipe-new' })
  } catch {
    importError.value = t('recipes.importError')
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <div>
    <div class="row page-header">
      <h1>{{ $t('recipes.title') }}</h1>
      <div class="row">
        <RouterLink v-if="authStore.isAuthenticated" :to="{ name: 'recipe-new' }">
          <button><Plus :size="16" />{{ $t('recipes.newRecipe') }}</button>
        </RouterLink>
        <button
          v-if="authStore.isAuthenticated"
          class="secondary"
          type="button"
          :aria-expanded="showImportForm"
          aria-controls="import-form"
          @click="toggleImportForm"
        >
          <component :is="showImportForm ? X : Link2" :size="16" />{{ $t('recipes.importButton') }}
        </button>
      </div>
    </div>

    <div v-if="authStore.isAuthenticated && showImportForm" id="import-form" class="card" style="margin-bottom: 1rem">
      <form class="row" style="align-items: flex-end" @submit.prevent="handleImport">
        <div class="field" style="flex: 1; min-width: 220px">
          <label for="import-url">{{ $t('recipes.importFromUrl') }}</label>
          <input
            id="import-url"
            ref="importUrlInput"
            v-model="importUrl"
            type="url"
            placeholder="https://..."
            required
          />
        </div>
        <button type="submit" :disabled="isImporting">
          <Link2 :size="16" />{{ isImporting ? $t('common.loading') : $t('recipes.importButton') }}
        </button>
      </form>
      <p v-if="importError" class="muted">{{ importError }}</p>
    </div>

    <RecipeFilters v-model="filters" />

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
    <p v-else-if="!recipes.length" class="muted">{{ $t('recipes.noResults') }}</p>
    <div v-else class="card recipe-list">
      <RecipeCard v-for="recipe in recipes" :key="recipe.id" :recipe="recipe" />
    </div>

    <Pagination :page="page" :count="count" @update:page="goToPage" />
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.recipe-list {
  padding: 0;
  overflow: hidden;
}
</style>
