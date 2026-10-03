<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDebouncedSearch } from '../../composables/useDebouncedSearch'
import { listRecipes } from '../../api/recipes'
import type { Recipe } from '../../types/models'

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
const { results: suggestions, search, cancel, clear } = useDebouncedSearch<Recipe>(
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

// La recherche n'est déclenchée que par une saisie de l'utilisateur (événement `input`), pas par
// un changement programmatique de `query` (sélection, resynchronisation depuis le parent) : sinon
// la liste se rouvrirait juste après la sélection (le `watch(query, ...)` qu'il y avait ici avant
// réagissait aussi à `select()` affectant `query.value`, ce qui rouvrait le menu ~250ms après le
// clic sur une suggestion).
function onInput() {
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
}

function select(recipe: Recipe) {
  query.value = recipe.title
  suggestions.value = []
  close()
  emit('update:modelValue', recipe)
}

function closeSoon() {
  setTimeout(close, 150)
}
</script>

<template>
  <div class="picker">
    <input
      :id="id"
      v-model="query"
      type="text"
      :placeholder="t('recipePicker.placeholder')"
      @input="onInput"
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
