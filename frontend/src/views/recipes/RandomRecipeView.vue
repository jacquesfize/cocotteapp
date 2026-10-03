<script setup lang="ts">
import { Dices, ListFilter, Shuffle } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import AddToPlanForm from '../../components/planning/AddToPlanForm.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import RecipeRestrictedNotice from '../../components/recipes/RecipeRestrictedNotice.vue'
import RecipeSummary from '../../components/recipes/RecipeSummary.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import { listAllergens } from '../../api/allergens'
import { getRandomRecipe } from '../../api/recipes'
import { getErrorStatus } from '../../utils/apiError'
import { useAuthStore } from '../../stores/auth'
import type { RecipeListParams } from '../../types/api'
import type { Allergen, DietType, Recipe } from '../../types/models'

const authStore = useAuthStore()

const myAllergens = computed(() => [
  ...(authStore.user?.allergies ?? []),
  ...(authStore.user?.intolerances ?? []),
])

const recipe = ref<Recipe | null>(null)
const isLoading = ref(false)
const notFound = ref(false)
const isFiltersOpen = ref(false)
const allergens = ref<Allergen[]>([])

const filters = ref<{ diet_type: DietType | ''; in_season: boolean; exclude_allergens: string[] }>({
  diet_type: '',
  in_season: false,
  // Pré-rempli avec les allergies/intolérances du profil, si elles sont définies (décochable).
  exclude_allergens: [...myAllergens.value],
})

const activeFiltersCount = computed(
  () =>
    (filters.value.diet_type ? 1 : 0) +
    (filters.value.in_season ? 1 : 0) +
    (filters.value.exclude_allergens.length ? 1 : 0),
)

function toggleFilters() {
  isFiltersOpen.value = !isFiltersOpen.value
}

async function draw() {
  isLoading.value = true
  notFound.value = false
  try {
    const params: RecipeListParams = {}
    if (filters.value.diet_type) params.diet_type = filters.value.diet_type
    if (filters.value.in_season) params.in_season = true
    if (filters.value.exclude_allergens.length) params.exclude_allergens = filters.value.exclude_allergens.join(',')
    recipe.value = await getRandomRecipe(params)
  } catch (err) {
    recipe.value = null
    if (getErrorStatus(err) === 404) notFound.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  listAllergens()
    .then((data) => {
      allergens.value = data
    })
    .catch(() => {
      allergens.value = []
    })
  draw()
})
</script>

<template>
  <div>
    <div class="row page-header">
      <PageHeader :icon="Shuffle" :title="$t('random.title')" />
      <div class="row header-actions">
        <button :disabled="isLoading" @click="draw"><Dices :size="16" />{{ $t('random.another') }}</button>
        <button
          type="button"
          class="secondary toggle"
          :aria-expanded="isFiltersOpen"
          aria-controls="random-filters-panel"
          :aria-label="$t('random.toggleFilters')"
          @click="toggleFilters"
        >
          <ListFilter :size="16" />
          <span
            v-if="activeFiltersCount"
            class="badge"
            data-testid="filters-badge"
            :aria-label="$t('recipes.activeFilters', { count: activeFiltersCount })"
          >{{ activeFiltersCount }}</span>
        </button>
      </div>
    </div>

    <div v-show="isFiltersOpen" id="random-filters-panel" class="card filters">
      <div class="row">
        <div class="field">
          <label for="random-diet">{{ $t('recipes.dietFilter') }}</label>
          <select id="random-diet" v-model="filters.diet_type" @change="draw">
            <option value="">{{ $t('recipes.allDiets') }}</option>
            <option value="omnivore">{{ $t('diet.omnivore') }}</option>
            <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
            <option value="vegan">{{ $t('diet.vegan') }}</option>
          </select>
        </div>
        <div class="field checkbox-field">
          <input id="random-in-season" v-model="filters.in_season" type="checkbox" style="width: auto" @change="draw" />
          <label for="random-in-season" style="margin: 0">{{ $t('recipes.inSeasonOnly') }}</label>
        </div>
      </div>
      <div class="field">
        <label for="random-exclude-allergens">{{ $t('random.excludeAllergens') }}</label>
        <select
          id="random-exclude-allergens"
          v-model="filters.exclude_allergens"
          multiple
          @change="draw"
        >
          <option v-for="allergen in allergens" :key="allergen.slug" :value="allergen.slug">
            {{ allergen.name }}
          </option>
        </select>
      </div>
    </div>

    <AsyncState
      v-if="isLoading || notFound"
      :loading="isLoading"
      :loading-text="$t('common.loading')"
      :empty-text="$t('random.noResult')"
    />

    <template v-if="recipe && !isLoading">
      <RouterLink :to="{ name: 'recipe-detail', params: { id: recipe.id } }" class="random-title-link">
        <h2>{{ recipe.title }}</h2>
      </RouterLink>
      <!-- Une recette restreinte arrive sans ingrédients ni étapes : RecipeSummary n'en
           supporte pas l'absence (comme dans RecipeDetailView.vue). -->
      <RecipeSummary v-if="!recipe.content_restricted" :recipe="recipe" />
      <RecipeRestrictedNotice v-else :recipe="recipe" />
      <AddToPlanForm v-if="authStore.isAuthenticated" :key="recipe.id" :recipe="recipe" />
    </template>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header-actions {
  align-items: center;
}

.toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.badge {
  min-width: 1.35rem;
  height: 1.35rem;
  padding: 0 0.35rem;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.filters {
  margin-bottom: 1rem;
}

.checkbox-field {
  align-self: center;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.random-title-link {
  text-decoration: none;
  color: inherit;
}
</style>
