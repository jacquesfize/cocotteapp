<script setup lang="ts">
import { Dices, Shuffle } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import AddToPlanForm from '../components/AddToPlanForm.vue'
import PageHeader from '../components/shared/PageHeader.vue'
import RecipeRestrictedNotice from '../components/recipes/RecipeRestrictedNotice.vue'
import RecipeSummary from '../components/recipes/RecipeSummary.vue'
import AsyncState from '../components/shared/AsyncState.vue'
import { getRandomRecipe } from '../api/recipes'
import { getErrorStatus } from '../utils/apiError'
import { useAuthStore } from '../stores/auth'
import type { RecipeListParams } from '../types/api'
import type { DietType, Recipe } from '../types/models'

const authStore = useAuthStore()

const recipe = ref<Recipe | null>(null)
const isLoading = ref(false)
const notFound = ref(false)

const filters = ref<{ diet_type: DietType | ''; in_season: boolean }>({ diet_type: '', in_season: false })

async function draw() {
  isLoading.value = true
  notFound.value = false
  try {
    const params: RecipeListParams = {}
    if (filters.value.diet_type) params.diet_type = filters.value.diet_type
    if (filters.value.in_season) params.in_season = true
    recipe.value = await getRandomRecipe(params)
  } catch (err) {
    recipe.value = null
    if (getErrorStatus(err) === 404) notFound.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(draw)
</script>

<template>
  <div>
    <div class="row page-header">
      <PageHeader :icon="Shuffle" :title="$t('random.title')" />
      <button :disabled="isLoading" @click="draw"><Dices :size="16" />{{ $t('random.another') }}</button>
    </div>

    <div class="card filters">
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
