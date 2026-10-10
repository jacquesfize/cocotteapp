<script setup lang="ts">
import { ArrowLeft, Dices, X } from '@lucide/vue'
import { nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AllergenWarning from '../nutrition/AllergenWarning.vue'
import BaseModal from '../shared/BaseModal.vue'
import { useDebouncedSearch } from '../../composables/useDebouncedSearch'
import { getRandomRecipe, listRecipes } from '../../api/recipes'
import { createMealPlanEntry } from '../../api/planning'
import type { MealType, Recipe } from '../../types/models'

// Recipe picker for one known (date, meal type) slot: search or "surprise me", then confirm
// servings. Shared by the planner's MealSlot and the homepage week strip's empty slots.
const props = defineProps<{
  date: string
  mealType: MealType
  owner?: number | string
}>()
const emit = defineEmits<{
  close: []
  added: []
}>()

const { t } = useI18n()
const query = ref('')
const searchEl = ref<HTMLInputElement | null>(null)
const selectedRecipe = ref<Recipe | null>(null)
const newServings = ref(2)
const error = ref('')

const { results: searchResults, search, cancel: cancelSearch, clear: clearSearch } = useDebouncedSearch<Recipe>(
  async (value) => (await listRecipes({ search: value })).results,
)

onMounted(() => nextTick(() => searchEl.value?.focus()))

function close() {
  cancelSearch()
  emit('close')
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
    cancelSearch()
    emit('added')
  } catch {
    error.value = t('planning.addError')
  }
}
</script>

<template>
  <BaseModal :title="selectedRecipe ? selectedRecipe.title : $t('planning.addEntry')" @close="close">
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
      <p v-if="error" class="error" style="margin: 0">{{ error }}</p>
      <div class="picker-foot">
        <button type="button" class="secondary surprise-btn" @click="surprise">
          <Dices :size="14" />{{ t('planning.surpriseMe') }}
        </button>
        <button type="button" class="secondary" @click="close">{{ $t('common.cancel') }}</button>
      </div>
    </template>

    <form v-else class="add-meal-form" novalidate @submit.prevent="handleAdd">
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
        <button type="button" class="secondary icon-btn" :aria-label="$t('common.cancel')" @click="close">
          <X :size="14" />
        </button>
      </div>
      <p v-if="error" class="error" style="margin: 0">{{ error }}</p>
    </form>
  </BaseModal>
</template>

<style scoped>
.add-meal-form {
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
  border-radius: 0;
  min-height: auto;
  color: inherit;
}

.picker-results button:hover {
  background: var(--color-primary-soft);
}

.entry-thumb {
  flex: none;
  width: 24px;
  height: 24px;
  border-radius: 0;
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
</style>
