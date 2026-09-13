<script setup>
import { Dices } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import AddToPlanForm from '../components/AddToPlanForm.vue'
import RecipeSummary from '../components/RecipeSummary.vue'
import { getRandomRecipe } from '../api/recipes'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const recipe = ref(null)
const isLoading = ref(false)
const notFound = ref(false)

const filters = ref({ diet_type: '', in_season: false })

async function draw() {
  isLoading.value = true
  notFound.value = false
  try {
    const params = {}
    if (filters.value.diet_type) params.diet_type = filters.value.diet_type
    if (filters.value.in_season) params.in_season = true
    recipe.value = await getRandomRecipe(params)
  } catch (err) {
    recipe.value = null
    if (err.response?.status === 404) notFound.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(draw)
</script>

<template>
  <div>
    <div class="row page-header">
      <h1>{{ $t('random.title') }}</h1>
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

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
    <p v-else-if="notFound" class="muted">{{ $t('random.noResult') }}</p>

    <template v-if="recipe && !isLoading">
      <RouterLink :to="{ name: 'recipe-detail', params: { id: recipe.id } }" class="random-title-link">
        <h2>{{ recipe.title }}</h2>
      </RouterLink>
      <RecipeSummary :recipe="recipe" />
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
