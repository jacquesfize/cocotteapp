<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { deleteRecipe, getRecipe } from '../api/recipes'
import { createMealPlanEntry } from '../api/planning'
import { formatDuration } from '../utils/format'

const props = defineProps({
  id: { type: [String, Number], required: true },
})
const { t } = useI18n()
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
  if (!confirm(t('recipes.deleteConfirm'))) return
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
    planMessage.value = t('recipes.addedToPlanning')
  } catch {
    planMessage.value = t('recipes.addToPlanningError')
  }
}
</script>

<template>
  <div v-if="recipe">
    <div class="row page-header">
      <h1>{{ recipe.title }}</h1>
      <div class="row">
        <RouterLink :to="{ name: 'recipe-edit', params: { id: recipe.id } }">
          <button class="secondary">{{ $t('common.edit') }}</button>
        </RouterLink>
        <button class="danger" @click="handleDelete">{{ $t('common.delete') }}</button>
      </div>
    </div>

    <p class="muted">
      {{ $t(`diet.${recipe.diet_type}`) }} · {{ recipe.servings }} {{ $t('recipes.servings') }} ·
      {{ $t('recipes.prep') }} {{ formatDuration(recipe.prep_time_minutes) }} · {{ $t('recipes.cook') }}
      {{ formatDuration(recipe.cook_time_minutes) }}
    </p>
    <p v-if="recipe.description">{{ recipe.description }}</p>

    <div class="row" style="align-items: flex-start">
      <div class="card" style="flex: 1; min-width: 260px">
        <h2>{{ $t('recipes.ingredients') }}</h2>
        <ul>
          <li v-for="item in recipe.ingredients" :key="item.id">
            {{ item.quantity }} {{ item.unit }} — {{ item.ingredient.name }}
            <span v-if="item.group_name" class="muted">({{ item.group_name }})</span>
          </li>
        </ul>
      </div>

      <div class="card" style="flex: 2; min-width: 260px">
        <h2>{{ $t('recipes.steps') }}</h2>
        <ol>
          <li v-for="step in recipe.steps" :key="step.id">{{ step.instruction }}</li>
        </ol>
      </div>
    </div>

    <div class="card" style="margin-top: 1rem">
      <h2>{{ $t('recipes.addToPlanning') }}</h2>
      <form class="row" style="align-items: flex-end" @submit.prevent="handleAddToPlan">
        <div class="field">
          <label for="plan-date">{{ $t('recipes.date') }}</label>
          <input id="plan-date" v-model="planForm.date" type="date" required />
        </div>
        <div class="field">
          <label for="plan-meal">{{ $t('recipes.meal') }}</label>
          <select id="plan-meal" v-model="planForm.meal_type">
            <option value="breakfast">{{ $t('mealType.breakfast') }}</option>
            <option value="lunch">{{ $t('mealType.lunch') }}</option>
            <option value="dinner">{{ $t('mealType.dinner') }}</option>
            <option value="snack">{{ $t('mealType.snack') }}</option>
          </select>
        </div>
        <div class="field">
          <label for="plan-servings">{{ $t('planning.servings') }}</label>
          <input id="plan-servings" v-model.number="planForm.servings" type="number" min="1" />
        </div>
        <button type="submit">{{ $t('common.add') }}</button>
      </form>
      <p v-if="planMessage" class="muted">{{ planMessage }}</p>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
}
</style>
