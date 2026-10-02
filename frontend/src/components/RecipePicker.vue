<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDebouncedSearch } from '../composables/useDebouncedSearch'
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
const isOpen = ref(false)
const { results: suggestions, search, clear } = useDebouncedSearch<Recipe>(
  async (value) => (await listRecipes({ search: value })).results,
  { onResults: () => { isOpen.value = true } },
)

// Même précaution que IngredientPicker.vue : resynchronise l'affichage si le parent
// remplace `modelValue` après le montage (ex. rechargement asynchrone d'un formulaire).
watch(
  () => props.modelValue,
  (value) => {
    query.value = value?.title ?? ''
  },
)

watch(query, (value) => {
  if (!value) {
    clear()
    return
  }
  search(value)
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
    <ul v-if="isOpen && suggestions.length" class="suggestions-dropdown">
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
</style>
