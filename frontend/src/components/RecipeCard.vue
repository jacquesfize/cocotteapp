<script setup lang="ts">
import { formatDuration } from '../utils/format'
import type { Recipe } from '../types/models'

defineProps<{
  recipe: Recipe
  variant?: 'row' | 'tile'
}>()
</script>

<template>
  <RouterLink :to="{ name: 'recipe-detail', params: { id: recipe.id } }" class="recipe-card">
    <img v-if="recipe.image || recipe.image_url" :src="recipe.image || recipe.image_url" class="thumb" alt="" />
    <div v-else-if="variant === 'tile'" class="thumb thumb-placeholder" aria-hidden="true">🍲</div>
    <div class="recipe-card-body">
      <h3>{{ recipe.title }}</h3>
      <p class="muted">
        {{ $t(`diet.${recipe.diet_type}`) }} · {{ formatDuration(recipe.total_time_minutes) }}
      </p>
      <p v-if="recipe.description" class="description">{{ recipe.description }}</p>
    </div>
  </RouterLink>
</template>

<style scoped>
.recipe-card {
  display: flex;
  gap: 1rem;
  align-items: center;
  text-decoration: none;
  color: inherit;
  padding: 0.85rem 1.25rem;
}

.recipe-card:not(:last-child) {
  border-bottom: 1px solid var(--color-border);
}

.recipe-card:hover {
  background: var(--color-surface-hover, rgba(127, 127, 127, 0.08));
}

.thumb {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 10px;
  flex-shrink: 0;
}

.recipe-card-body {
  min-width: 0;
}

.recipe-card h3 {
  margin: 0 0 0.25rem;
}

.description {
  margin: 0.5rem 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.recipe-card.tile {
  flex-direction: column;
  align-items: stretch;
  gap: 0.75rem;
  margin-bottom: 0;
  padding: 0;
  overflow: hidden;
}

.tile .thumb {
  width: 100%;
  height: auto;
  aspect-ratio: 4 / 3;
  border-radius: 0;
}

.thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  background: var(--color-primary-soft);
}

.tile .recipe-card-body {
  padding: 0 1rem 1rem;
}
</style>
