<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { createIngredient, listIngredients } from '../api/ingredients'
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
const suggestions = ref<Ingredient[]>([])
const isOpen = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | undefined

watch(query, (value) => {
  clearTimeout(debounceTimer)
  if (!value) {
    suggestions.value = []
    return
  }
  debounceTimer = setTimeout(async () => {
    const data = await listIngredients({ search: value })
    suggestions.value = data.results
    isOpen.value = true
  }, 250)
})

function select(ingredient: Ingredient) {
  query.value = ingredient.name
  isOpen.value = false
  emit('update:modelValue', ingredient)
}

async function createAndSelect() {
  const ingredient = await createIngredient({ name: query.value })
  select(ingredient)
}

function closeSoon() {
  setTimeout(() => {
    isOpen.value = false
  }, 150)
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
      @focus="isOpen = true"
      @blur="closeSoon"
    />
    <ul v-if="isOpen && query" class="suggestions">
      <li v-for="ingredient in suggestions" :key="ingredient.id" @mousedown.prevent="select(ingredient)">
        {{ ingredient.name }}
      </li>
      <li v-if="!exactMatch()" class="create" @mousedown.prevent="createAndSelect">
        {{ t('ingredientPicker.create', { name: query }) }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.picker {
  position: relative;
}

.suggestions {
  position: absolute;
  z-index: 10;
  top: 100%;
  left: 0;
  right: 0;
  margin: 0.35rem 0 0;
  padding: 0.35rem;
  list-style: none;
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  max-height: 220px;
  overflow-y: auto;
}

.suggestions li {
  padding: 0.5rem 0.7rem;
  border-radius: 10px;
  cursor: pointer;
}

.suggestions li:hover {
  background: var(--color-surface-muted);
}

.suggestions li.create {
  color: var(--color-primary-dark);
  font-weight: 600;
}
</style>
