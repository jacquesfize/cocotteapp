<script setup lang="ts">
import { Plus, X } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AllergenWarning from './AllergenWarning.vue'
import RecipePicker from './RecipePicker.vue'
import { createMealPlanEntry, deleteMealPlanEntry } from '../api/planning'
import type { MealPlanEntry, MealType, Recipe } from '../types/models'

const props = defineProps<{
  date: string
  mealType: MealType
  entries?: MealPlanEntry[]
  owner?: number | string
  readOnly?: boolean
}>()
const emit = defineEmits<{
  changed: []
}>()

const { t } = useI18n()
const isAdding = ref(false)
const newRecipe = ref<Recipe | null>(null)
const newServings = ref(2)
const error = ref('')

function openForm() {
  isAdding.value = true
  error.value = ''
}

function closeForm() {
  isAdding.value = false
  newRecipe.value = null
  newServings.value = 2
  error.value = ''
}

async function handleAdd() {
  if (!newRecipe.value) {
    error.value = t('planning.chooseRecipe')
    return
  }
  try {
    await createMealPlanEntry(
      {
        recipe: newRecipe.value.id,
        date: props.date,
        meal_type: props.mealType,
        servings: newServings.value,
      },
      props.owner,
    )
    closeForm()
    emit('changed')
  } catch {
    error.value = t('planning.addError')
  }
}

async function handleRemove(entryId: number) {
  await deleteMealPlanEntry(entryId, props.owner)
  emit('changed')
}
</script>

<template>
  <div class="meal-slot">
    <span class="meal-label">{{ $t(`mealType.${mealType}`) }}</span>

    <ul v-if="entries?.length" class="entry-list">
      <li v-for="entry in entries" :key="entry.id">
        <RouterLink :to="{ name: 'recipe-detail', params: { id: entry.recipe } }">
          {{ entry.recipe_title }}
        </RouterLink>
        <AllergenWarning :allergens="entry.recipe_allergens" class="entry-warning" />
        <button
          v-if="!readOnly"
          type="button"
          class="remove-btn"
          :aria-label="$t('planning.remove')"
          @click="handleRemove(entry.id)"
        >
          <X :size="14" />
        </button>
      </li>
    </ul>

    <template v-if="!readOnly">
      <button
        v-if="!isAdding"
        type="button"
        class="add-btn secondary"
        :aria-label="$t('planning.addEntry')"
        @click="openForm"
      >
        <Plus :size="14" />
      </button>
      <form v-else class="add-form" @submit.prevent="handleAdd">
        <RecipePicker v-model="newRecipe" />
        <AllergenWarning :allergens="newRecipe?.allergens" />
        <div class="row" style="align-items: center; gap: 0.4rem">
          <input v-model.number="newServings" type="number" min="1" style="width: 4.5rem" />
          <button type="submit">{{ $t('common.add') }}</button>
          <button type="button" class="secondary icon-btn" :aria-label="$t('common.cancel')" @click="closeForm">
            <X :size="14" />
          </button>
        </div>
        <p v-if="error" class="error" style="margin: 0">{{ error }}</p>
      </form>
    </template>
  </div>
</template>

<style scoped>
.meal-slot {
  padding: 0.55rem 0;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.meal-slot:first-child {
  border-top: none;
  padding-top: 0;
}

.meal-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-muted);
}

.entry-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.entry-list li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  font-size: 0.85rem;
}

.entry-warning {
  flex-basis: 100%;
  order: 3;
}

.entry-list a {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: transparent;
  border: none;
  color: var(--color-muted);
  min-height: auto;
  padding: 0 0.3rem;
  line-height: 1;
  font-size: 1rem;
}

.remove-btn:hover {
  color: var(--color-danger);
  background: transparent;
}

.add-btn {
  align-self: flex-start;
  width: 1.9rem;
  min-height: 1.9rem;
  padding: 0;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
</style>
