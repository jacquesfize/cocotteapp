<script setup>
import { formatDuration } from '../utils/format'

defineProps({
  recipe: { type: Object, required: true },
})
</script>

<template>
  <RouterLink :to="{ name: 'recipe-detail', params: { id: recipe.id } }" class="recipe-card card">
    <img v-if="recipe.image || recipe.image_url" :src="recipe.image || recipe.image_url" class="thumb" alt="" />
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
  margin-bottom: 0.75rem;
}

.thumb {
  width: 84px;
  height: 84px;
  object-fit: cover;
  border-radius: 14px;
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
</style>
