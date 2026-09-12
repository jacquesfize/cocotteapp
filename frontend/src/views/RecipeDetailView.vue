<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteRecipe, getRecipe } from '../api/recipes'
import { createMealPlanEntry } from '../api/planning'
import { DIET_LABELS, formatDuration } from '../utils/format'

const props = defineProps({
  id: { type: [String, Number], required: true },
})
const router = useRouter()

const recipe = ref(null)
const planForm = ref({ date: '', meal_type: 'dinner', servings: 4 })
const planMessage = ref('')

async function load() {
  recipe.value = await getRecipe(props.id)
  planForm.value.servings = recipe.value.servings
}

onMounted(load)

async function handleDelete() {
  if (!confirm('Supprimer cette recette ?')) return
  await deleteRecipe(props.id)
  router.push({ name: 'recipes' })
}

async function handleAddToPlan() {
  planMessage.value = ''
  try {
    await createMealPlanEntry({
      recipe: recipe.value.id,
      date: planForm.value.date,
      meal_type: planForm.value.meal_type,
      servings: planForm.value.servings,
    })
    planMessage.value = "Ajoutée à l'agenda."
  } catch {
    planMessage.value = "Impossible d'ajouter cette recette (date déjà utilisée ?)."
  }
}
</script>

<template>
  <div v-if="recipe">
    <div class="row" style="justify-content: space-between; align-items: center">
      <h1>{{ recipe.title }}</h1>
      <div class="row">
        <RouterLink :to="{ name: 'recipe-edit', params: { id: recipe.id } }">
          <button class="secondary">Modifier</button>
        </RouterLink>
        <button class="danger" @click="handleDelete">Supprimer</button>
      </div>
    </div>

    <p class="muted">
      {{ DIET_LABELS[recipe.diet_type] }} · {{ recipe.servings }} portions · prépa
      {{ formatDuration(recipe.prep_time_minutes) }} · cuisson {{ formatDuration(recipe.cook_time_minutes) }}
    </p>
    <p v-if="recipe.description">{{ recipe.description }}</p>

    <div class="row" style="align-items: flex-start">
      <div class="card" style="flex: 1; min-width: 260px">
        <h2>Ingrédients</h2>
        <ul>
          <li v-for="item in recipe.ingredients" :key="item.id">
            {{ item.quantity }} {{ item.unit }} — {{ item.ingredient.name }}
            <span v-if="item.group_name" class="muted">({{ item.group_name }})</span>
          </li>
        </ul>
      </div>

      <div class="card" style="flex: 2; min-width: 260px">
        <h2>Étapes</h2>
        <ol>
          <li v-for="step in recipe.steps" :key="step.id">{{ step.instruction }}</li>
        </ol>
      </div>
    </div>

    <div class="card" style="margin-top: 1rem">
      <h2>Ajouter à l'agenda</h2>
      <form class="row" style="align-items: flex-end" @submit.prevent="handleAddToPlan">
        <div class="field">
          <label for="plan-date">Date</label>
          <input id="plan-date" v-model="planForm.date" type="date" required />
        </div>
        <div class="field">
          <label for="plan-meal">Repas</label>
          <select id="plan-meal" v-model="planForm.meal_type">
            <option value="breakfast">Petit-déjeuner</option>
            <option value="lunch">Déjeuner</option>
            <option value="dinner">Dîner</option>
            <option value="snack">Collation</option>
          </select>
        </div>
        <div class="field">
          <label for="plan-servings">Portions</label>
          <input id="plan-servings" v-model.number="planForm.servings" type="number" min="1" />
        </div>
        <button type="submit">Ajouter</button>
      </form>
      <p v-if="planMessage" class="muted">{{ planMessage }}</p>
    </div>
  </div>
</template>
