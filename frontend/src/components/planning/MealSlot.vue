<script setup lang="ts">
import { ArrowLeft, Dices, Plus, X } from '@lucide/vue'
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AllergenWarning from '../nutrition/AllergenWarning.vue'
import BaseModal from '../shared/BaseModal.vue'
import { useDebouncedSearch } from '../../composables/useDebouncedSearch'
import { getRandomRecipe, listRecipes } from '../../api/recipes'
import { createMealPlanEntry, deleteMealPlanEntry } from '../../api/planning'
import type { MealPlanEntry, MealType, Recipe } from '../../types/models'

const props = defineProps<{
  date: string
  mealType: MealType
  entries?: MealPlanEntry[]
  owner?: number | string
  readOnly?: boolean
  over?: boolean
}>()
const emit = defineEmits<{
  changed: []
  removed: [entry: MealPlanEntry]
  'drag-start': [entry: MealPlanEntry]
  'drag-end': []
  'drag-over': []
  'drag-leave': []
  drop: [altKey: boolean]
}>()

const { t } = useI18n()
const isAdding = ref(false)
const query = ref('')
const searchEl = ref<HTMLInputElement | null>(null)
const selectedRecipe = ref<Recipe | null>(null)
const newServings = ref(2)
const error = ref('')

const { results: searchResults, search, cancel: cancelSearch, clear: clearSearch } = useDebouncedSearch<Recipe>(
  async (value) => (await listRecipes({ search: value })).results,
)

function openPicker() {
  isAdding.value = true
  query.value = ''
  selectedRecipe.value = null
  newServings.value = 2
  error.value = ''
  clearSearch()
  nextTick(() => searchEl.value?.focus())
}

function closePicker() {
  isAdding.value = false
  cancelSearch()
}

function onSearchInput() {
  if (!query.value) {
    clearSearch()
    return
  }
  search(query.value)
}

function choose(recipe: Recipe) {
  selectedRecipe.value = recipe
  newServings.value = recipe.servings
  error.value = ''
}

function backToSearch() {
  selectedRecipe.value = null
}

async function surprise() {
  error.value = ''
  try {
    choose(await getRandomRecipe())
  } catch {
    error.value = t('planning.addError')
  }
}

async function handleAdd() {
  if (!selectedRecipe.value) {
    error.value = t('planning.chooseRecipe')
    return
  }
  if (!newServings.value || newServings.value < 1) {
    error.value = t('planning.invalidServings')
    return
  }
  try {
    await createMealPlanEntry(
      {
        recipe: selectedRecipe.value.id,
        date: props.date,
        meal_type: props.mealType,
        servings: newServings.value,
      },
      props.owner,
    )
    closePicker()
    emit('changed')
  } catch {
    error.value = t('planning.addError')
  }
}

async function handleRemove(entry: MealPlanEntry) {
  await deleteMealPlanEntry(entry.id, props.owner)
  emit('removed', entry)
  emit('changed')
}
</script>

<template>
  <div
    class="meal-slot"
    :class="{ over, filled: entries?.length }"
    @dragover.prevent="emit('drag-over')"
    @dragleave="emit('drag-leave')"
    @drop.prevent="emit('drop', $event.altKey)"
  >
    <span class="meal-label">{{ $t(`mealType.${mealType}`) }}</span>

    <ul v-if="entries?.length" class="entry-list">
      <li
        v-for="entry in entries"
        :key="entry.id"
        class="entry-chip"
        :draggable="!readOnly"
        @dragstart="emit('drag-start', entry)"
        @dragend="emit('drag-end')"
      >
        <RouterLink :to="{ name: 'recipe-detail', params: { id: entry.recipe } }" class="entry-link">
          <span class="entry-thumb" aria-hidden="true">
            <img v-if="entry.recipe_image_url" :src="entry.recipe_image_url" :alt="''" loading="lazy" />
            <span v-else>🍲</span>
          </span>
          <span class="entry-title">{{ entry.recipe_title }}</span>
        </RouterLink>
        <AllergenWarning :allergens="entry.recipe_allergens" class="entry-warning" />
        <button
          v-if="!readOnly"
          type="button"
          class="remove-btn"
          :aria-label="$t('planning.remove', { title: entry.recipe_title })"
          @click="handleRemove(entry)"
        >
          <X :size="12" :stroke-width="2.6" />
        </button>
      </li>
    </ul>

    <button
      v-if="!readOnly"
      type="button"
      class="add-btn"
      :class="{ ghost: entries?.length }"
      :aria-label="$t('planning.addEntry')"
      @click="openPicker"
    >
      <Plus :size="16" :stroke-width="2.4" />
    </button>

    <BaseModal
      v-if="isAdding"
      :title="selectedRecipe ? selectedRecipe.title : $t('planning.addEntry')"
      @close="closePicker"
    >
      <template v-if="!selectedRecipe">
        <div class="picker-search-row">
          <input
            ref="searchEl"
            v-model="query"
            type="search"
            class="picker-search"
            :placeholder="t('recipePicker.placeholder')"
            @input="onSearchInput"
          />
        </div>
        <ul class="picker-results">
          <li v-for="recipe in searchResults" :key="recipe.id">
            <button type="button" @click="choose(recipe)">
              <span class="entry-thumb" aria-hidden="true">
                <img v-if="recipe.image_url" :src="recipe.image_url" :alt="''" loading="lazy" />
                <span v-else>🍲</span>
              </span>
              <span>{{ recipe.title }}</span>
            </button>
          </li>
          <li v-if="query && !searchResults.length" class="picker-none">
            {{ t('planning.noSearchResults', { query }) }}
          </li>
        </ul>
        <div class="picker-foot">
          <button type="button" class="secondary surprise-btn" @click="surprise">
            <Dices :size="14" />{{ t('planning.surpriseMe') }}
          </button>
          <button type="button" class="secondary" @click="closePicker">{{ $t('common.cancel') }}</button>
        </div>
      </template>

      <form v-else novalidate @submit.prevent="handleAdd">
        <button type="button" class="secondary back-btn" @click="backToSearch">
          <ArrowLeft :size="14" />{{ t('planning.chooseAnotherRecipe') }}
        </button>
        <AllergenWarning :allergens="selectedRecipe.allergens" />
        <div class="row" style="align-items: center; gap: 0.4rem">
          <label :for="`servings-${date}-${mealType}`">{{ $t('planning.servings') }}</label>
          <input
            :id="`servings-${date}-${mealType}`"
            v-model.number="newServings"
            type="number"
            min="1"
            style="width: 4.5rem"
          />
          <button type="submit">{{ $t('common.add') }}</button>
          <button type="button" class="secondary icon-btn" :aria-label="$t('common.cancel')" @click="closePicker">
            <X :size="14" />
          </button>
        </div>
        <p v-if="error" class="error" style="margin: 0">{{ error }}</p>
      </form>
    </BaseModal>
  </div>
</template>

<style scoped>
.meal-slot {
  position: relative;
  height: 100%;
  min-height: 5.75rem;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: background-color 0.12s, outline-color 0.12s;
}

.meal-slot.over {
  outline: 2px dashed var(--color-primary);
  outline-offset: -4px;
  background: var(--color-primary-soft);
}

.meal-label {
  display: none;
}

.entry-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.entry-chip {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  background: var(--color-primary-soft);
  border-radius: 10px;
  padding: 5px;
  cursor: grab;
}

.entry-chip:active {
  cursor: grabbing;
}

.entry-link {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  min-width: 0;
  flex: 1;
  color: var(--color-primary-dark);
  text-decoration: none;
}

.entry-link:hover .entry-title {
  text-decoration: underline;
}

.entry-thumb {
  flex: none;
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: var(--color-surface);
  overflow: hidden;
  display: grid;
  place-items: center;
  font-size: 14px;
  line-height: 1;
}

.entry-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.entry-title {
  padding-top: 2px;
  padding-right: 34px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.25;
  overflow: hidden;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.entry-warning {
  flex-basis: 100%;
}

.remove-btn {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 22px;
  height: 22px;
  min-height: auto;
  border: 0;
  border-radius: 50%;
  background: var(--color-surface);
  color: var(--color-primary-dark);
  display: grid;
  place-items: center;
  padding: 0;
  opacity: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.18);
}

.remove-btn::after {
  content: '';
  position: absolute;
  inset: -10px;
}

.entry-chip:hover .remove-btn,
.entry-chip:focus-within .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  color: var(--color-danger);
  background: var(--color-surface);
}

.add-btn {
  border: 0;
  background: transparent;
  color: var(--color-border);
  border-radius: 10px;
  display: grid;
  place-items: center;
  padding: 0;
  min-height: auto;
}

.add-btn:not(.ghost) {
  flex: 1;
  min-height: 4.75rem;
  border: 1.5px dashed transparent;
}

.add-btn:not(.ghost):hover,
.add-btn:not(.ghost):focus-visible {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-soft-hover);
  color: var(--color-primary-dark);
}

.add-btn.ghost {
  height: 24px;
  opacity: 0;
  border: 1px dashed var(--color-primary-soft-hover);
  color: var(--color-primary-dark);
}

.meal-slot:hover .add-btn.ghost,
.meal-slot:focus-within .add-btn.ghost {
  opacity: 1;
}

.add-btn.ghost:hover {
  background: var(--color-primary-soft);
}

.meal-slot form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.back-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  min-height: auto;
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.picker-search-row {
  margin-bottom: 0.6rem;
}

.picker-search {
  width: 100%;
}

.picker-results {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 45vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.picker-results button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  text-align: left;
  border: 0;
  background: transparent;
  padding: 0.5rem;
  border-radius: 8px;
  min-height: auto;
  color: inherit;
}

.picker-results button:hover {
  background: var(--color-primary-soft);
}

.picker-none {
  padding: 0.6rem 0.4rem;
  color: var(--color-muted);
  font-size: 0.85rem;
}

.picker-foot {
  margin-top: 0.6rem;
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.surprise-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

@media (hover: none) {
  .remove-btn {
    opacity: 1;
    width: 28px;
    height: 28px;
  }

  .add-btn.ghost {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: no-preference) {
  .remove-btn,
  .add-btn {
    transition: opacity 0.12s, background 0.12s, color 0.12s;
  }
}
</style>
