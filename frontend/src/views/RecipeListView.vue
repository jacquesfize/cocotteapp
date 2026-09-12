<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import RecipeCard from '../components/RecipeCard.vue'
import { importRecipeFromUrl } from '../api/importer'
import { listRecipes } from '../api/recipes'

const { t } = useI18n()

const recipes = ref([])
const isLoading = ref(false)

const filters = ref({
  search: '',
  diet_type: '',
  max_prep_time: '',
  max_cook_time: '',
  ingredients: '',
  in_season: false,
})

async function load() {
  isLoading.value = true
  try {
    const params = {}
    for (const [key, value] of Object.entries(filters.value)) {
      if (value !== '' && value !== false) params[key] = value
    }
    const data = await listRecipes(params)
    recipes.value = data.results
  } finally {
    isLoading.value = false
  }
}

let debounceTimer = null
watch(
  filters,
  () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(load, 300)
  },
  { deep: true },
)

onMounted(load)

const importUrl = ref('')
const importMessage = ref('')

async function handleImport() {
  importMessage.value = ''
  try {
    await importRecipeFromUrl(importUrl.value)
    importMessage.value = t('recipes.importSuccess')
    importUrl.value = ''
  } catch {
    importMessage.value = t('recipes.importError')
  }
}
</script>

<template>
  <div>
    <div class="row page-header">
      <h1>{{ $t('recipes.title') }}</h1>
      <RouterLink :to="{ name: 'recipe-new' }">
        <button>{{ $t('recipes.newRecipe') }}</button>
      </RouterLink>
    </div>

    <div class="card" style="margin-bottom: 1rem">
      <form class="row" style="align-items: flex-end" @submit.prevent="handleImport">
        <div class="field" style="flex: 1; min-width: 220px">
          <label for="import-url">{{ $t('recipes.importFromUrl') }}</label>
          <input id="import-url" v-model="importUrl" type="url" placeholder="https://..." required />
        </div>
        <button type="submit">{{ $t('recipes.importButton') }}</button>
      </form>
      <p v-if="importMessage" class="muted">{{ importMessage }}</p>
    </div>

    <div class="card filters">
      <div class="row">
        <div class="field" style="flex: 2; min-width: 200px">
          <label for="search">{{ $t('recipes.search') }}</label>
          <input id="search" v-model="filters.search" :placeholder="$t('recipes.searchPlaceholder')" />
        </div>
        <div class="field">
          <label for="diet_type">{{ $t('recipes.dietFilter') }}</label>
          <select id="diet_type" v-model="filters.diet_type">
            <option value="">{{ $t('recipes.allDiets') }}</option>
            <option value="omnivore">{{ $t('diet.omnivore') }}</option>
            <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
            <option value="vegan">{{ $t('diet.vegan') }}</option>
          </select>
        </div>
        <div class="field">
          <label for="ingredients">{{ $t('recipes.ingredientsFilter') }}</label>
          <input id="ingredients" v-model="filters.ingredients" :placeholder="$t('recipes.ingredientsPlaceholder')" />
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label for="max_prep">{{ $t('recipes.maxPrepTime') }}</label>
          <input id="max_prep" v-model.number="filters.max_prep_time" type="number" min="0" />
        </div>
        <div class="field">
          <label for="max_cook">{{ $t('recipes.maxCookTime') }}</label>
          <input id="max_cook" v-model.number="filters.max_cook_time" type="number" min="0" />
        </div>
        <div class="field checkbox-field">
          <input id="in_season" v-model="filters.in_season" type="checkbox" style="width: auto" />
          <label for="in_season" style="margin: 0">{{ $t('recipes.inSeasonOnly') }}</label>
        </div>
      </div>
    </div>

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
    <p v-else-if="!recipes.length" class="muted">{{ $t('recipes.noResults') }}</p>
    <RecipeCard v-for="recipe in recipes" :key="recipe.id" :recipe="recipe" />
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
</style>
