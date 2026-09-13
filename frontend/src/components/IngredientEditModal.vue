<script setup lang="ts">
import { X } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createIngredient } from '../api/ingredients'
import { NUTRIENT_LABEL_KEYS } from '../utils/nutrition'
import type { Ingredient, IngredientCategory, Unit } from '../types/models'

const { t } = useI18n()

const props = defineProps<{
  initialName: string
}>()
const emit = defineEmits<{
  created: [ingredient: Ingredient]
  close: []
}>()

const CATEGORIES: IngredientCategory[] = [
  'vegetable',
  'fruit',
  'legume',
  'grain',
  'nut_seed',
  'dairy',
  'meat_fish',
  'egg',
  'fat',
  'condiment',
  'other',
]
const UNITS: Unit[] = ['g', 'kg', 'ml', 'l', 'piece', 'tbsp', 'tsp', 'pinch']
const NUTRIENT_FIELDS = Object.keys(NUTRIENT_LABEL_KEYS) as Array<keyof typeof NUTRIENT_LABEL_KEYS>

const form = ref({
  name: props.initialName,
  category: 'other' as IngredientCategory,
  default_unit: 'g' as Unit,
  calories_kcal: 0,
  protein_g: 0,
  carbs_g: 0,
  fat_g: 0,
  fiber_g: 0,
  iron_mg: 0,
  vitamin_b12_ug: 0,
  calcium_mg: 0,
  omega3_g: 0,
  zinc_mg: 0,
  carbon_kg_co2e_per_kg: 0,
})
const error = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    const ingredient = await createIngredient(form.value)
    emit('created', ingredient)
  } catch {
    error.value = t('ingredientModal.error')
  } finally {
    isSubmitting.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <div class="overlay" @mousedown.self="emit('close')">
    <div class="card modal" role="dialog" aria-modal="true" :aria-label="t('ingredientModal.title')">
      <div class="row modal-header">
        <h2>{{ t('ingredientModal.title') }}</h2>
        <button
          type="button"
          class="secondary icon-btn"
          :aria-label="t('common.cancel')"
          @click="emit('close')"
        >
          <X :size="16" />
        </button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="field">
          <label for="ingredient-modal-name">{{ t('ingredientModal.name') }}</label>
          <input id="ingredient-modal-name" v-model="form.name" required autofocus />
        </div>
        <div class="row">
          <div class="field">
            <label for="ingredient-modal-category">{{ t('ingredientModal.category') }}</label>
            <select id="ingredient-modal-category" v-model="form.category">
              <option v-for="category in CATEGORIES" :key="category" :value="category">
                {{ t(`ingredientCategory.${category}`) }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="ingredient-modal-unit">{{ t('ingredientModal.defaultUnit') }}</label>
            <select id="ingredient-modal-unit" v-model="form.default_unit">
              <option v-for="unit in UNITS" :key="unit" :value="unit">{{ unit }}</option>
            </select>
          </div>
        </div>

        <h3>{{ t('ingredientModal.nutritionTitle') }}</h3>
        <div class="nutrition-grid">
          <div v-for="field in NUTRIENT_FIELDS" :key="field" class="field">
            <label :for="`ingredient-modal-${field}`">{{ t(NUTRIENT_LABEL_KEYS[field]) }}</label>
            <input :id="`ingredient-modal-${field}`" v-model.number="form[field]" type="number" step="0.01" min="0" />
          </div>
        </div>

        <h3>{{ t('ingredientModal.carbonTitle') }}</h3>
        <div class="field">
          <label for="ingredient-modal-carbon">{{ t('nutrition.carbonPerKg') }}</label>
          <input
            id="ingredient-modal-carbon"
            v-model.number="form.carbon_kg_co2e_per_kg"
            type="number"
            step="0.01"
            min="0"
          />
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <div class="row" style="margin-top: 1rem; justify-content: flex-end">
          <button type="button" class="secondary" @click="emit('close')">{{ t('common.cancel') }}</button>
          <button type="submit" :disabled="isSubmitting">{{ t('ingredientModal.submit') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(36, 31, 29, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal {
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.modal-header h2 {
  margin: 0;
}

.modal h3 {
  margin: 1rem 0 0.5rem;
  font-size: 0.95rem;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
}
</style>
