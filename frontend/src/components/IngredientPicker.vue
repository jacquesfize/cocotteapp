<script setup>
import { ref, watch } from 'vue'
import { createIngredient, listIngredients } from '../api/ingredients'

const props = defineProps({
  modelValue: { type: Object, default: null },
  id: { type: String, default: undefined },
})
const emit = defineEmits(['update:modelValue'])

const query = ref(props.modelValue?.name ?? '')
const suggestions = ref([])
const isOpen = ref(false)
let debounceTimer = null

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

function select(ingredient) {
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

const exactMatch = () => suggestions.value.some((i) => i.name.toLowerCase() === query.value.toLowerCase())
</script>

<template>
  <div class="picker">
    <input
      :id="id"
      v-model="query"
      type="text"
      placeholder="Rechercher un ingrédient..."
      @focus="isOpen = true"
      @blur="closeSoon"
    />
    <ul v-if="isOpen && query" class="suggestions">
      <li v-for="ingredient in suggestions" :key="ingredient.id" @mousedown.prevent="select(ingredient)">
        {{ ingredient.name }}
      </li>
      <li v-if="!exactMatch()" class="create" @mousedown.prevent="createAndSelect">
        + Créer « {{ query }} »
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
  margin: 0.25rem 0 0;
  padding: 0.25rem 0;
  list-style: none;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  max-height: 220px;
  overflow-y: auto;
}

.suggestions li {
  padding: 0.4rem 0.6rem;
  cursor: pointer;
}

.suggestions li:hover {
  background: var(--color-bg);
}

.suggestions li.create {
  color: var(--color-primary-dark);
  font-weight: 600;
}
</style>
