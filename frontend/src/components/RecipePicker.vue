<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listRecipes } from '../api/recipes'
import type { Recipe } from '../types/models'

const { t } = useI18n()

const props = defineProps<{
  modelValue?: Recipe | null
  id?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [recipe: Recipe]
}>()

const query = ref(props.modelValue?.title ?? '')
const suggestions = ref<Recipe[]>([])
const isOpen = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | undefined

watch(query, (value) => {
  clearTimeout(debounceTimer)
  if (!value) {
    suggestions.value = []
    return
  }
  debounceTimer = setTimeout(async () => {
    const data = await listRecipes({ search: value })
    suggestions.value = data.results
    isOpen.value = true
  }, 250)
})

function select(recipe: Recipe) {
  query.value = recipe.title
  isOpen.value = false
  emit('update:modelValue', recipe)
}

function closeSoon() {
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}
</script>

<template>
  <div class="picker">
    <input
      :id="id"
      v-model="query"
      type="text"
      :placeholder="t('recipePicker.placeholder')"
      @focus="isOpen = true"
      @blur="closeSoon"
    />
    <ul v-if="isOpen && suggestions.length" class="suggestions">
      <li v-for="recipe in suggestions" :key="recipe.id" @mousedown.prevent="select(recipe)">
        {{ recipe.title }}
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
</style>
