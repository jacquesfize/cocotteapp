<script setup lang="ts">
import { Plus, X } from '@lucide/vue'
import { ref } from 'vue'
import AddMealModal from './AddMealModal.vue'
import AllergenWarning from '../nutrition/AllergenWarning.vue'
import { deleteMealPlanEntry } from '../../api/planning'
import type { MealPlanEntry, MealType } from '../../types/models'

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

const isAdding = ref(false)

function handleAdded() {
  isAdding.value = false
  emit('changed')
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
      @click="isAdding = true"
    >
      <Plus :size="16" :stroke-width="2.4" />
    </button>

    <AddMealModal
      v-if="isAdding"
      :date="date"
      :meal-type="mealType"
      :owner="owner"
      @close="isAdding = false"
      @added="handleAdded"
    />
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
  border-radius: 0;
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
  border-radius: 0;
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
  border-radius: 0;
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
