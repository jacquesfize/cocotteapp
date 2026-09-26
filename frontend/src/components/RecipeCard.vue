<script setup lang="ts">
import { Lock } from '@lucide/vue'
import { computed } from 'vue'
import { formatDuration } from '../utils/format'
import { imageCreditDomain } from '../utils/imageCredit'
import AllergenBadges from './AllergenBadges.vue'
import type { Recipe } from '../types/models'

const props = defineProps<{
  recipe: Recipe
  variant?: 'row' | 'tile'
}>()

const credit = computed(() =>
  !props.recipe.image && props.recipe.image_url ? imageCreditDomain(props.recipe.source_url) : null,
)
</script>

<template>
  <RouterLink :to="{ name: 'recipe-detail', params: { id: recipe.id } }" class="recipe-card" :class="{ tile: variant === 'tile' }">
    <div v-if="recipe.image || recipe.image_url" class="thumb-wrapper">
      <img :src="recipe.image || recipe.image_url" class="thumb" alt="" />
      <span v-if="credit && variant !== 'tile'" class="thumb-credit">{{ credit }}</span>
    </div>
    <div v-else-if="variant === 'tile'" class="thumb thumb-placeholder" aria-hidden="true">🍲</div>
    <div v-if="variant === 'tile'" class="scrim" />
    <div class="recipe-card-body">
      <h3>
        {{ recipe.title }}
        <Lock v-if="recipe.content_restricted" :size="14" class="restricted-icon" :aria-label="$t('recipes.restrictedNotice')" />
      </h3>
      <p class="muted">
        {{ $t(`diet.${recipe.diet_type}`) }} · {{ formatDuration(recipe.total_time_minutes) }}
      </p>
      <AllergenBadges :allergens="recipe.allergens ?? []" only-mine class="card-allergens" />
      <p v-if="recipe.description" class="description">{{ recipe.description }}</p>
      <p v-if="credit && variant === 'tile'" class="tile-credit">{{ $t('recipes.imageCredit', { domain: credit }) }}</p>
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

.thumb-wrapper {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.thumb {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 10px;
  flex-shrink: 0;
}

.thumb-credit {
  max-width: 64px;
  font-size: 0.6rem;
  color: var(--color-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tile-credit {
  margin: 0.35rem 0 0;
  font-size: 0.68rem;
  color: inherit;
  opacity: 0.8;
}

.recipe-card-body {
  min-width: 0;
}

.recipe-card h3 {
  margin: 0 0 0.25rem;
}

.restricted-icon {
  vertical-align: middle;
  margin-left: 0.3rem;
  color: var(--color-muted);
}

.card-allergens {
  margin-top: 0.4rem;
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
  position: relative;
  display: block;
  aspect-ratio: 1;
  padding: 0;
  overflow: hidden;
  border-radius: 16px;
  border-bottom: 0;
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
}

.tile .thumb {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 0;
}

.thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  background: var(--color-primary-soft);
}

.scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0) 60%);
}

.tile .recipe-card-body {
  position: absolute;
  left: 0.85rem;
  right: 0.85rem;
  bottom: 0.75rem;
}

.tile h3 {
  margin: 0 0 0.15rem;
  font-size: 1rem;
  line-height: 1.25;
  color: inherit;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tile .muted {
  margin: 0;
  font-size: 0.8rem;
  color: inherit;
  opacity: 0.9;
}
</style>
