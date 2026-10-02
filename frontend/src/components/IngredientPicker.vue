<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import IngredientEditModal from './IngredientEditModal.vue'
import { useDebouncedSearch } from '../composables/useDebouncedSearch'
import { listIngredients } from '../api/ingredients'
import type { Ingredient } from '../types/models'

const { t } = useI18n()

const props = defineProps<{
  modelValue?: Ingredient | null
  id?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [ingredient: Ingredient]
}>()

const query = ref(props.modelValue?.name ?? '')
const { results: suggestions, search, cancel, clear } = useDebouncedSearch<Ingredient>(
  async (value) => (await listIngredients({ search: value })).results,
)
const isOpen = ref(false)

// `query` n'est initialisé qu'une fois à partir de `modelValue` : si le parent remplace la
// valeur après coup (ex. RecipeFormView qui charge la recette de manière asynchrone en mode
// édition), il faut resynchroniser l'affichage nous-mêmes.
watch(
  () => props.modelValue,
  (value) => {
    query.value = value?.name ?? ''
  },
)

// La recherche n'est déclenchée que par une saisie de l'utilisateur (événement `input`), pas par
// un changement programmatique de `query` (sélection, resynchronisation depuis le parent) : sinon
// la liste se rouvrirait juste après la sélection.
const activeIndex = ref(-1)

function onInput() {
  activeIndex.value = -1
  const value = query.value
  if (!value) {
    clear()
    isOpen.value = false
    return
  }
  isOpen.value = true
  search(value)
}

function close() {
  cancel()
  isOpen.value = false
  activeIndex.value = -1
}

function select(ingredient: Ingredient) {
  query.value = ingredient.name
  suggestions.value = []
  close()
  emit('update:modelValue', ingredient)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    if (isOpen.value) {
      event.preventDefault()
      close()
    }
    return
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    if (!isOpen.value || !suggestions.value.length) return
    event.preventDefault()
    const count = suggestions.value.length
    const delta = event.key === 'ArrowDown' ? 1 : -1
    activeIndex.value = (activeIndex.value + delta + count) % count
    return
  }
  if (event.key === 'Enter' && isOpen.value && activeIndex.value >= 0) {
    event.preventDefault()
    select(suggestions.value[activeIndex.value])
  }
}

const showCreateModal = ref(false)

function openCreateModal() {
  isOpen.value = false
  showCreateModal.value = true
}

function handleIngredientCreated(ingredient: Ingredient) {
  showCreateModal.value = false
  select(ingredient)
}

function closeSoon() {
  setTimeout(close, 150)
}

const exactMatch = () =>
  suggestions.value.some((i) => i.name.toLowerCase() === query.value.toLowerCase())
</script>

<template>
  <div class="picker">
    <input
      :id="id"
      v-model="query"
      type="text"
      :placeholder="t('ingredientPicker.placeholder')"
      autocomplete="off"
      @input="onInput"
      @keydown="onKeydown"
      @blur="closeSoon"
    />
    <ul v-if="isOpen && query" class="suggestions-dropdown">
      <li
        v-for="(ingredient, i) in suggestions"
        :key="ingredient.id"
        :class="{ active: i === activeIndex }"
        @mousedown.prevent="select(ingredient)">
        {{ ingredient.name }}
      </li>
      <li v-if="!exactMatch()" class="create" @mousedown.prevent="openCreateModal">
        {{ t('ingredientPicker.create', { name: query }) }}
      </li>
    </ul>

    <IngredientEditModal
      v-if="showCreateModal"
      :initial-name="query"
      @created="handleIngredientCreated"
      @close="showCreateModal = false"
    />
  </div>
</template>

<style scoped>
.picker {
  position: relative;
}
</style>
