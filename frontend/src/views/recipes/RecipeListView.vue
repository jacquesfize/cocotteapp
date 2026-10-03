<script setup lang="ts">
import { BookOpen, ChevronDown, Link2, Pencil, Plus, X } from '@lucide/vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, type LocationQuery, type LocationQueryRaw } from 'vue-router'
import Pagination from '../../components/shared/Pagination.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import RecipeCard from '../../components/recipes/RecipeCard.vue'
import RecipeFilters, { type RecipeFilterValues } from '../../components/recipes/RecipeFilters.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import { previewImportFromUrl } from '../../api/importer'
import { deleteRecipe, listRecipes } from '../../api/recipes'
import { useClickOutside } from '../../composables/useClickOutside'
import { useAuthStore } from '../../stores/auth'
import { setPendingImportDraft } from '../../utils/pendingImportDraft'
import type { RecipeListParams } from '../../types/api'
import type { Recipe } from '../../types/models'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const recipes = ref<Recipe[]>([])
const count = ref(0)
const isLoading = ref(false)

const myAllergens = computed(() => [
  ...(authStore.user?.allergies ?? []),
  ...(authStore.user?.intolerances ?? []),
])

function filtersFromQuery(query: LocationQuery): RecipeFilterValues {
  return {
    search: (query.search as string) || '',
    diet_type: (query.diet_type as string) || '',
    max_prep_time: (query.max_prep_time as string) || '',
    max_cook_time: (query.max_cook_time as string) || '',
    ingredients: (query.ingredients as string) || '',
    in_season: query.in_season === 'true',
    carbon_level: (query.carbon_level as string) || '',
    exclude_allergens: (query.exclude_allergens as string) || '',
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
// À l'arrivée sur la liste sans filtre explicite, on masque par défaut les recettes qui
// contiennent un allergène du profil (modifiable allergène par allergène dans les filtres).
if (!('exclude_allergens' in route.query) && myAllergens.value.length) {
  filters.value.exclude_allergens = myAllergens.value.join(',')
}
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

const deleteError = ref('')

async function handleDelete(recipe: Recipe) {
  if (!confirm(t('recipes.deleteNamedConfirm', { title: recipe.title }))) return
  deleteError.value = ''
  try {
    await deleteRecipe(recipe.id)
  } catch {
    deleteError.value = t('recipes.deleteError')
    return
  }
  // Si l'on vient de vider la dernière page, on recule d'une page plutôt que d'afficher une liste vide.
  if (recipes.value.length === 1 && page.value > 1) page.value -= 1
  await load()
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

const showCreateMenu = ref(false)
const createMenuEl = ref<HTMLElement | null>(null)
useClickOutside(createMenuEl, () => {
  showCreateMenu.value = false
})

function openImportForm() {
  showCreateMenu.value = false
  showImportForm.value = true
  nextTick(() => importUrlInput.value?.focus())
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
      <PageHeader :icon="BookOpen" :title="$t('recipes.title')" />
      <!-- Un seul point d'entrée : "Nouvelle recette" ouvre un petit menu (créer / importer),
           comme le bouton équivalent de l'accueil (HomeWeekStrip.vue). -->
      <div v-if="authStore.isAuthenticated" ref="createMenuEl" class="create-menu">
        <button
          type="button"
          class="create-toggle"
          :aria-expanded="showCreateMenu"
          aria-controls="recipe-create-panel"
          @click="showCreateMenu = !showCreateMenu"
        >
          <Plus :size="16" />{{ $t('recipes.newRecipe') }}<ChevronDown :size="16" class="chevron" />
        </button>
        <div v-show="showCreateMenu" id="recipe-create-panel" class="create-panel">
          <RouterLink :to="{ name: 'recipe-new' }" class="create-link" @click="showCreateMenu = false">
            <Pencil :size="16" /><span>{{ $t('recipes.createManually') }}</span>
          </RouterLink>
          <button
            type="button"
            class="create-link"
            :aria-expanded="showImportForm"
            aria-controls="import-form"
            @click="openImportForm"
          >
            <Link2 :size="16" /><span>{{ $t('recipes.importFromUrl') }}</span>
          </button>
        </div>
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
        <button
          type="button"
          class="secondary icon-btn"
          :aria-label="$t('common.close')"
          @click="showImportForm = false"
        >
          <X :size="16" />
        </button>
      </form>
      <p v-if="importError" class="muted">{{ importError }}</p>
    </div>

    <!-- Desktop : filtres en colonne latérale à gauche ; mobile : au-dessus de la liste. -->
    <div class="recipes-layout">
      <RecipeFilters v-model="filters" class="recipes-sidebar" :my-allergens="myAllergens" />

      <div class="recipes-main">
        <p v-if="deleteError" class="error">{{ deleteError }}</p>
        <AsyncState
          v-if="isLoading || !recipes.length"
          :loading="isLoading"
          :loading-text="$t('common.loading')"
          :empty-text="$t('recipes.noResults')"
        />
        <div v-else class="recipe-grid">
          <div v-for="recipe in recipes" :key="recipe.id" class="recipe-tile">
            <RecipeCard :recipe="recipe" manageable @delete="handleDelete" />
          </div>
        </div>

        <Pagination :page="page" :count="count" @update:page="goToPage" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.create-menu {
  position: relative;
}
.create-toggle .chevron {
  margin-left: -0.1rem;
  transition: transform 0.15s ease;
}
.create-toggle[aria-expanded='true'] .chevron {
  transform: rotate(180deg);
}
.create-panel {
  position: absolute;
  top: calc(100% + 0.4rem);
  right: 0;
  min-width: 230px;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.6rem;
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  z-index: 20;
}
.create-link {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.6rem;
  margin: 0;
  padding: 0.55rem 0.6rem;
  border-radius: 10px;
  color: var(--color-text);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  background: none;
  border: none;
  min-height: auto;
}
.create-link:hover {
  background: var(--color-surface-muted);
}

.recipes-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
}
.recipes-main {
  min-width: 0;
}
.recipe-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.75rem;
}
.recipe-tile {
  min-width: 0;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* Desktop large : deux recettes par ligne. */
@media (min-width: 900px) {
  .recipe-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .recipe-tile {
    display: flex;
  }
  .recipe-tile > :deep(.recipe-card) {
    flex: 1;
  }
}

@media (max-width: 600px) {
  .recipes-layout {
    display: block;
  }
}
</style>
