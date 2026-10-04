<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AllergenWarning from '../nutrition/AllergenWarning.vue'
import { createMealPlanEntry } from '../../api/planning'
import { toISODate } from '../../utils/dates'
import type { MealType, Recipe } from '../../types/models'

// `inModal`: rendered inside a BaseModal (homepage "Plan for later") — no card/heading of its
// own, and a successful add emits `added` so the parent can close.
// La date est préremplie avec aujourd'hui (date locale via toISODate, pas toISOString qui
// passerait en UTC et pourrait décaler d'un jour) dans les deux modes.
const props = defineProps<{
  recipe: Recipe
  inModal?: boolean
}>()
const emit = defineEmits<{ added: [] }>()

const { t } = useI18n()
const form = ref<{ date: string; meal_type: MealType; servings: number }>({
  date: toISODate(new Date()),
  meal_type: 'dinner',
  servings: props.recipe.servings,
})
const message = ref('')

async function handleSubmit() {
  message.value = ''
  try {
    await createMealPlanEntry({
      recipe: props.recipe.id,
      date: form.value.date,
      meal_type: form.value.meal_type,
      servings: form.value.servings,
    })
    message.value = t('recipes.addedToPlanning')
    emit('added')
  } catch {
    message.value = t('recipes.addToPlanningError')
  }
}
</script>

<template>
  <div :class="{ card: !inModal }" :style="inModal ? undefined : 'margin-top: 1rem'">
    <h2 v-if="!inModal">{{ $t('recipes.addToPlanning') }}</h2>
    <form class="row" style="align-items: flex-end" @submit.prevent="handleSubmit">
      <div class="field">
        <label :for="`plan-date-${recipe.id}`">{{ $t('recipes.date') }}</label>
        <input :id="`plan-date-${recipe.id}`" v-model="form.date" type="date" required />
      </div>
      <div class="field">
        <label :for="`plan-meal-${recipe.id}`">{{ $t('recipes.meal') }}</label>
        <select :id="`plan-meal-${recipe.id}`" v-model="form.meal_type">
          <option value="breakfast">{{ $t('mealType.breakfast') }}</option>
          <option value="lunch">{{ $t('mealType.lunch') }}</option>
          <option value="dinner">{{ $t('mealType.dinner') }}</option>
          <option value="snack">{{ $t('mealType.snack') }}</option>
        </select>
      </div>
      <div class="field">
        <label :for="`plan-servings-${recipe.id}`">{{ $t('planning.servings') }}</label>
        <input :id="`plan-servings-${recipe.id}`" v-model.number="form.servings" type="number" min="1" />
      </div>
      <button type="submit">{{ $t('common.add') }}</button>
    </form>
    <AllergenWarning :allergens="recipe.allergens" />
    <p v-if="message" class="muted">{{ message }}</p>
  </div>
</template>
