<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import RecipePicker from '../components/RecipePicker.vue'
import { createMealPlanEntry, deleteMealPlanEntry, listMealPlanEntries } from '../api/planning'
import { createShoppingList } from '../api/shopping'

const { t } = useI18n()
const router = useRouter()

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

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
    error.value = t('planning.chooseRecipe')
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
    error.value = t('planning.addError')
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
    <h1>{{ $t('planning.title') }}</h1>

    <div class="card">
      <h2>{{ $t('planning.planRecipe') }}</h2>
      <form class="row" style="align-items: flex-end" @submit.prevent="handleAdd">
        <div class="field" style="flex: 1; min-width: 220px">
          <label for="plan-recipe">{{ $t('planning.recipe') }}</label>
          <RecipePicker id="plan-recipe" v-model="newEntry.recipe" />
        </div>
        <div class="field">
          <label for="plan-new-date">{{ $t('planning.date') }}</label>
          <input id="plan-new-date" v-model="newEntry.date" type="date" required />
        </div>
        <div class="field">
          <label for="plan-new-meal">{{ $t('planning.meal') }}</label>
          <select id="plan-new-meal" v-model="newEntry.meal_type">
            <option v-for="type in MEAL_TYPES" :key="type" :value="type">{{ $t(`mealType.${type}`) }}</option>
          </select>
        </div>
        <div class="field" style="width: 90px">
          <label for="plan-new-servings">{{ $t('planning.servings') }}</label>
          <input id="plan-new-servings" v-model.number="newEntry.servings" type="number" min="1" />
        </div>
        <button type="submit">{{ $t('planning.add') }}</button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div class="row page-header">
      <h2 style="margin: 0">{{ $t('planning.plannedMeals') }}</h2>
      <button :disabled="!selectedIds.length" @click="handleGenerateShoppingList">
        {{ $t('planning.generateShoppingList', { n: selectedIds.length }) }}
      </button>
    </div>

    <p v-if="!entries.length" class="muted">{{ $t('planning.noEntries') }}</p>
    <div v-for="entry in entries" :key="entry.id" class="card entry-row">
      <label class="row" style="align-items: center; gap: 0.75rem">
        <input v-model="selectedIds" type="checkbox" :value="entry.id" style="width: auto" />
        <div>
          <strong>{{ entry.date }}</strong> · {{ $t(`mealType.${entry.meal_type}`) }} ·
          {{ entry.recipe_title || entry.recipe }} · {{ entry.servings }} {{ $t('planning.servingsUnit') }}
        </div>
      </label>
      <button class="secondary" @click="handleRemove(entry.id)">{{ $t('planning.remove') }}</button>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin: 1rem 0;
}

.entry-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>
