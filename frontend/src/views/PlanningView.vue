<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import RecipePicker from '../components/RecipePicker.vue'
import { createMealPlanEntry, deleteMealPlanEntry, listMealPlanEntries } from '../api/planning'
import { createShoppingList } from '../api/shopping'
import { MEAL_TYPE_LABELS } from '../utils/format'

const router = useRouter()

const entries = ref([])
const selectedIds = ref([])
const error = ref('')

const newEntry = ref({ recipe: null, date: '', meal_type: 'dinner', servings: 2 })

async function load() {
  const data = await listMealPlanEntries()
  entries.value = data.results
  selectedIds.value = selectedIds.value.filter((id) => entries.value.some((entry) => entry.id === id))
}

onMounted(load)

async function handleAdd() {
  error.value = ''
  if (!newEntry.value.recipe) {
    error.value = 'Choisissez une recette.'
    return
  }
  try {
    await createMealPlanEntry({
      recipe: newEntry.value.recipe.id,
      date: newEntry.value.date,
      meal_type: newEntry.value.meal_type,
      servings: newEntry.value.servings,
    })
    newEntry.value = { recipe: null, date: '', meal_type: 'dinner', servings: 2 }
    await load()
  } catch {
    error.value = "Impossible d'ajouter cette entrée (date déjà planifiée pour cette recette et ce repas ?)."
  }
}

async function handleRemove(id) {
  await deleteMealPlanEntry(id)
  await load()
}

async function handleGenerateShoppingList() {
  if (!selectedIds.value.length) return
  const shoppingList = await createShoppingList(selectedIds.value)
  router.push({ name: 'shopping-list-detail', params: { id: shoppingList.id } })
}
</script>

<template>
  <div>
    <h1>Agenda</h1>

    <div class="card">
      <h2>Planifier une recette</h2>
      <form class="row" style="align-items: flex-end" @submit.prevent="handleAdd">
        <div class="field" style="flex: 1; min-width: 220px">
          <label for="plan-recipe">Recette</label>
          <RecipePicker id="plan-recipe" v-model="newEntry.recipe" />
        </div>
        <div class="field">
          <label for="plan-new-date">Date</label>
          <input id="plan-new-date" v-model="newEntry.date" type="date" required />
        </div>
        <div class="field">
          <label for="plan-new-meal">Repas</label>
          <select id="plan-new-meal" v-model="newEntry.meal_type">
            <option v-for="(label, value) in MEAL_TYPE_LABELS" :key="value" :value="value">{{ label }}</option>
          </select>
        </div>
        <div class="field" style="width: 90px">
          <label for="plan-new-servings">Portions</label>
          <input id="plan-new-servings" v-model.number="newEntry.servings" type="number" min="1" />
        </div>
        <button type="submit">Ajouter</button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div class="row" style="justify-content: space-between; align-items: center; margin: 1rem 0">
      <h2 style="margin: 0">Repas planifiés</h2>
      <button :disabled="!selectedIds.length" @click="handleGenerateShoppingList">
        Générer la liste de courses ({{ selectedIds.length }})
      </button>
    </div>

    <p v-if="!entries.length" class="muted">Aucun repas planifié pour l'instant.</p>
    <div v-for="entry in entries" :key="entry.id" class="card entry-row">
      <label class="row" style="align-items: center; gap: 0.75rem">
        <input v-model="selectedIds" type="checkbox" :value="entry.id" style="width: auto" />
        <div>
          <strong>{{ entry.date }}</strong> · {{ MEAL_TYPE_LABELS[entry.meal_type] }} ·
          {{ entry.recipe_title || entry.recipe }} · {{ entry.servings }} portions
        </div>
      </label>
      <button class="secondary" @click="handleRemove(entry.id)">Retirer</button>
    </div>
  </div>
</template>

<style scoped>
.entry-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
</style>
