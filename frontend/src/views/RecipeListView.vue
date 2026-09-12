<script setup>
import { onMounted, ref, watch } from 'vue'
import RecipeCard from '../components/RecipeCard.vue'
import { importRecipeFromUrl } from '../api/importer'
import { listRecipes } from '../api/recipes'

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
    importMessage.value = "Import lancé, la recette apparaîtra dans quelques instants."
    importUrl.value = ''
  } catch {
    importMessage.value = "Échec de l'import."
  }
}
</script>

<template>
  <div>
    <div class="row" style="justify-content: space-between; align-items: center; margin-bottom: 1rem">
      <h1>Recettes</h1>
      <RouterLink :to="{ name: 'recipe-new' }">
        <button>+ Nouvelle recette</button>
      </RouterLink>
    </div>

    <div class="card" style="margin-bottom: 1rem">
      <form class="row" @submit.prevent="handleImport" style="align-items: flex-end">
        <div class="field" style="flex: 1; min-width: 220px">
          <label for="import-url">Importer depuis une URL</label>
          <input id="import-url" v-model="importUrl" type="url" placeholder="https://..." required />
        </div>
        <button type="submit">Importer</button>
      </form>
      <p v-if="importMessage" class="muted">{{ importMessage }}</p>
    </div>

    <div class="card filters">
      <div class="row">
        <div class="field" style="flex: 2; min-width: 200px">
          <label for="search">Recherche</label>
          <input id="search" v-model="filters.search" placeholder="Titre, description..." />
        </div>
        <div class="field">
          <label for="diet_type">Régime</label>
          <select id="diet_type" v-model="filters.diet_type">
            <option value="">Tous</option>
            <option value="omnivore">Omnivore</option>
            <option value="vegetarian">Végétarien</option>
            <option value="vegan">Végan</option>
          </select>
        </div>
        <div class="field">
          <label for="ingredients">Ingrédients (séparés par une virgule)</label>
          <input id="ingredients" v-model="filters.ingredients" placeholder="tomate, oignon" />
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label for="max_prep">Prépa max (min)</label>
          <input id="max_prep" v-model.number="filters.max_prep_time" type="number" min="0" />
        </div>
        <div class="field">
          <label for="max_cook">Cuisson max (min)</label>
          <input id="max_cook" v-model.number="filters.max_cook_time" type="number" min="0" />
        </div>
        <div class="field" style="align-self: center; flex-direction: row; align-items: center; gap: 0.5rem">
          <input id="in_season" v-model="filters.in_season" type="checkbox" style="width: auto" />
          <label for="in_season" style="margin: 0">Ingrédients de saison uniquement</label>
        </div>
      </div>
    </div>

    <p v-if="isLoading" class="muted">Chargement...</p>
    <p v-else-if="!recipes.length" class="muted">Aucune recette ne correspond à ces critères.</p>
    <RecipeCard v-for="recipe in recipes" :key="recipe.id" :recipe="recipe" />
  </div>
</template>
