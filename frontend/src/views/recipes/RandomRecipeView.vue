<script setup lang="ts">
import { Shuffle } from '@lucide/vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import DiceRoller from '../../components/recipes/DiceRoller.vue'
import RecipeCard from '../../components/recipes/RecipeCard.vue'
import RecipeFilters, { type RecipeFilterValues } from '../../components/recipes/RecipeFilters.vue'
import { getRandomRecipe } from '../../api/recipes'
import { getErrorStatus } from '../../utils/apiError'
import { useAuthStore } from '../../stores/auth'
import type { RecipeListParams } from '../../types/api'
import type { Recipe } from '../../types/models'

// Durée minimale d'un lancer : laisse le temps au dé de rouler même si l'API répond tout de
// suite (supprimée si l'utilisateur préfère réduire les animations).
const ROLL_MS = 900

const authStore = useAuthStore()

const myAllergens = computed(() => [
  ...(authStore.user?.allergies ?? []),
  ...(authStore.user?.intolerances ?? []),
])

const recipe = ref<Recipe | null>(null)
const isLoading = ref(false)
const notFound = ref(false)
// Tant que rien n'a été tiré, la page n'affiche que le grand dé.
const hasRolled = computed(() => recipe.value !== null || notFound.value)

// Mêmes filtres que la liste des recettes (l'endpoint /random/ partage son FilterSet).
const filters = ref<RecipeFilterValues>({
  search: '',
  diet_type: '',
  max_prep_time: '',
  max_cook_time: '',
  ingredients: '',
  in_season: false,
  carbon_level: '',
  // Pré-rempli avec les allergies/intolérances du profil, si elles sont définies (décochable).
  exclude_allergens: myAllergens.value.join(','),
  cookware: '',
})

const prefersReducedMotion = () =>
  typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

function rollDelay() {
  return new Promise<void>((resolve) => setTimeout(resolve, prefersReducedMotion() ? 0 : ROLL_MS))
}

// Un filtre modifié pendant un lancer relance le dé juste après, plutôt que d'être ignoré.
let redrawQueued = false

async function draw() {
  if (isLoading.value) {
    redrawQueued = true
    return
  }
  isLoading.value = true
  const params: RecipeListParams = {}
  for (const [key, value] of Object.entries(filters.value)) {
    if (value !== '' && value !== false) (params as Record<string, unknown>)[key] = value
  }
  const [result] = await Promise.allSettled([getRandomRecipe(params), rollDelay()])
  if (result.status === 'fulfilled') {
    recipe.value = result.value
    notFound.value = false
  } else {
    recipe.value = null
    notFound.value = getErrorStatus(result.reason) === 404
  }
  isLoading.value = false
  if (redrawQueued) {
    redrawQueued = false
    draw()
  }
}

// Une fois un premier tirage fait, changer un filtre relance le dé (après une courte pause,
// pour ne pas tirer à chaque frappe dans la recherche) ; avant, les filtres s'appliqueront
// simplement au premier lancer.
let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(
  filters,
  () => {
    clearTimeout(debounceTimer)
    if (hasRolled.value) debounceTimer = setTimeout(draw, 300)
  },
  { deep: true },
)

onBeforeUnmount(() => clearTimeout(debounceTimer))
</script>

<template>
  <div>
    <PageHeader :icon="Shuffle" :title="$t('random.title')" />

    <RecipeFilters v-model="filters" collapsible :my-allergens="myAllergens" class="random-filters" />

    <section v-if="!hasRolled" class="dice-stage">
      <DiceRoller :label="$t('random.roll')" :rolling="isLoading" :disabled="isLoading" @roll="draw" />
      <p class="dice-prompt">{{ $t('random.rollPrompt') }}</p>
    </section>

    <section v-else class="random-result">
      <RecipeCard v-if="recipe" :key="recipe.id" :recipe="recipe" variant="feature" :class="{ stale: isLoading }" />
      <p v-else class="muted no-result">{{ $t('random.noResult') }}</p>

      <div class="reroll">
        <DiceRoller
          :label="$t('random.another')"
          size="small"
          :rolling="isLoading"
          :disabled="isLoading"
          @roll="draw"
        />
        <span class="muted" aria-hidden="true">{{ $t('random.another') }}</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.random-filters {
  margin-bottom: 1rem;
}

.dice-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  min-height: 50vh;
  text-align: center;
}

.dice-prompt {
  margin: 0;
  font-size: 1.1rem;
  color: var(--color-muted);
}

.random-result {
  max-width: 40rem;
  margin: 0 auto;
}

.stale {
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.no-result {
  text-align: center;
  padding: 2rem 0;
}

.reroll {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  margin: 1rem 0 1.5rem;
}
</style>
