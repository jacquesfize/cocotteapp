<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listRecipes } from '../api/recipes'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Object, default: null },
  id: { type: String, default: undefined },
})
const emit = defineEmits(['update:modelValue'])

const query = ref(props.modelValue?.title ?? '')
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
    const data = await listRecipes({ search: value })
    suggestions.value = data.results
    isOpen.value = true
  }, 250)
})

function select(recipe) {
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
</style>
