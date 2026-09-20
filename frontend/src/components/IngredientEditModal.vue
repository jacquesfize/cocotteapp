<script setup lang="ts">
import { Sparkles, X } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createIngredient, suggestIngredientNutrition, updateIngredient } from '../api/ingredients'
import { NUTRIENT_LABEL_KEYS } from '../utils/nutrition'
import { formatUnit } from '../utils/format'
import type { Ingredient, IngredientCategory, Unit } from '../types/models'

const { t } = useI18n()

const props = defineProps<{
  initialName?: string
  // Mode édition (admin) : ingrédient existant à modifier. Sans lui, le modal crée.
  ingredient?: Ingredient | null
  // Expose noms traduits + mois de saison (page admin uniquement).
  advanced?: boolean
}>()
const emit = defineEmits<{
  created: [ingredient: Ingredient]
  updated: [ingredient: Ingredient]
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

const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1)
const isEdit = !!props.ingredient

const form = ref({
  name: props.ingredient?.name ?? props.initialName ?? '',
  name_en: props.ingredient?.translations?.en ?? '',
  available_months: [...(props.ingredient?.available_months ?? [])] as number[],
  category: (props.ingredient?.category ?? 'other') as IngredientCategory,
  default_unit: (props.ingredient?.default_unit ?? 'g') as Unit,
  calories_kcal: props.ingredient?.calories_kcal ?? 0,
  protein_g: props.ingredient?.protein_g ?? 0,
  carbs_g: props.ingredient?.carbs_g ?? 0,
  fat_g: props.ingredient?.fat_g ?? 0,
  fiber_g: props.ingredient?.fiber_g ?? 0,
  iron_mg: props.ingredient?.iron_mg ?? 0,
  vitamin_b12_ug: props.ingredient?.vitamin_b12_ug ?? 0,
  calcium_mg: props.ingredient?.calcium_mg ?? 0,
  omega3_g: props.ingredient?.omega3_g ?? 0,
  zinc_mg: props.ingredient?.zinc_mg ?? 0,
  carbon_kg_co2e_per_kg: props.ingredient?.carbon_kg_co2e_per_kg ?? 0,
})
const error = ref('')
const isSubmitting = ref(false)
const isSuggesting = ref(false)
const suggestMessage = ref('')

async function handleSuggest() {
  suggestMessage.value = ''
  isSuggesting.value = true
  try {
    const { found, suggestion } = await suggestIngredientNutrition(form.value.name)
    if (found && suggestion) {
      Object.assign(form.value, suggestion)
      suggestMessage.value = t('ingredientModal.suggestApplied')
    } else {
      suggestMessage.value = t('ingredientModal.suggestNotFound')
    }
  } catch {
    suggestMessage.value = t('ingredientModal.suggestNotFound')
  } finally {
    isSuggesting.value = false
  }
}

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    const { name_en, ...rest } = form.value
    const payload: Partial<Ingredient> = { ...rest }
    if (props.advanced) {
      // On conserve les autres langues déjà présentes ; seul "en" est édité ici.
      const translations = { ...(props.ingredient?.translations ?? {}) }
      if (name_en.trim()) translations.en = name_en.trim()
      else delete translations.en
      payload.translations = translations
    } else {
      delete payload.available_months
    }
    if (props.ingredient) {
      emit('updated', await updateIngredient(props.ingredient.id, payload))
    } else {
      emit('created', await createIngredient(payload))
    }
  } catch {
    error.value = t(isEdit ? 'ingredientModal.updateError' : 'ingredientModal.error')
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
    <div class="card modal" role="dialog" aria-modal="true" :aria-label="t(isEdit ? 'ingredientModal.editTitle' : 'ingredientModal.title')">
      <div class="row modal-header">
        <h2>{{ t(isEdit ? 'ingredientModal.editTitle' : 'ingredientModal.title') }}</h2>
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
          <div class="row" style="align-items: center">
            <input id="ingredient-modal-name" v-model="form.name" required autofocus style="flex: 1" />
            <button
              id="ingredient-modal-suggest"
              type="button"
              class="secondary"
              :disabled="!form.name || isSuggesting"
              @click="handleSuggest"
            >
              <Sparkles :size="16" />{{ isSuggesting ? t('ingredientModal.suggestLoading') : t('ingredientModal.suggestButton') }}
            </button>
          </div>
          <p v-if="suggestMessage" class="muted">{{ suggestMessage }}</p>
        </div>
        <div v-if="advanced" class="field">
          <label for="ingredient-modal-name-en">{{ t('ingredientModal.nameEn') }}</label>
          <input id="ingredient-modal-name-en" v-model="form.name_en" />
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
              <option v-for="unit in UNITS" :key="unit" :value="unit">{{ formatUnit(unit) }}</option>
            </select>
          </div>
        </div>

        <template v-if="advanced">
          <h3>{{ t('ingredientModal.seasonTitle') }}</h3>
          <p class="muted">{{ t('ingredientModal.seasonHint') }}</p>
          <div class="months">
            <label v-for="month in MONTHS" :key="month" class="month">
              <input v-model="form.available_months" type="checkbox" :value="month" />
              {{ t(`ingredientModal.months.${month}`) }}
            </label>
          </div>
        </template>

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
          <button type="submit" :disabled="isSubmitting">{{ t(isEdit ? 'common.save' : 'ingredientModal.submit') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.months {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 0.25rem 0.75rem;
}

.month {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.month input {
  width: auto;
}

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
