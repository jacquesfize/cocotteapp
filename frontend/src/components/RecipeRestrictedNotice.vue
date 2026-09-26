<script setup lang="ts">
import { Link2, Lock } from '@lucide/vue'
import { computed } from 'vue'
import AllergenBadges from './AllergenBadges.vue'
import { imageCreditDomain } from '../utils/imageCredit'
import type { Recipe } from '../types/models'

const props = defineProps<{
  recipe: Recipe
}>()

const imageCredit = computed(() =>
  !props.recipe.youtube_id && !props.recipe.image && props.recipe.image_url
    ? imageCreditDomain(props.recipe.source_url)
    : null,
)
</script>

<template>
  <div class="card restricted-notice">
    <div v-if="recipe.youtube_id" class="video-wrapper">
      <iframe
        :src="`https://www.youtube-nocookie.com/embed/${recipe.youtube_id}`"
        title="YouTube video player"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
      />
    </div>
    <div v-else-if="recipe.image || recipe.image_url" class="hero-photo-wrapper">
      <img :src="recipe.image || recipe.image_url" class="hero-photo" alt="" />
      <a
        v-if="recipe.source_url"
        :href="recipe.source_url"
        target="_blank"
        rel="noopener noreferrer"
        class="hero-source-button"
      >
        <Link2 :size="18" /><span>{{ $t('recipes.source') }}</span>
      </a>
    </div>
    <a
      v-else-if="recipe.source_url"
      :href="recipe.source_url"
      target="_blank"
      rel="noopener noreferrer"
      class="secondary fallback-source-link"
    >
      <Link2 :size="18" /><span>{{ $t('recipes.source') }}</span>
    </a>
    <p v-if="imageCredit" class="image-credit muted">{{ $t('recipes.imageCredit', { domain: imageCredit }) }}</p>

    <p class="restricted-message">
      <Lock :size="16" />
      {{ $t('recipes.restrictedNotice') }}
    </p>

    <AllergenBadges :allergens="recipe.allergens ?? []" :unverified="recipe.allergens_unverified" />

    <p v-if="recipe.carbon_footprint_kg_co2e !== undefined" class="carbon-footprint">
      <span class="value">{{ recipe.carbon_footprint_kg_co2e.toFixed(2) }} kg CO2e</span>
      <span class="label">{{ $t('recipes.carbonFootprint') }}</span>
    </p>
  </div>
</template>

<style scoped>
.restricted-notice {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hero-photo-wrapper {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
}

.hero-photo {
  display: block;
  width: 100%;
  height: 320px;
  object-fit: cover;
  filter: blur(14px) brightness(0.7);
  transform: scale(1.08);
}

.hero-source-button {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.85rem 2rem;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-primary-dark);
  font-size: 1.05rem;
  font-weight: 700;
  text-decoration: none;
  box-shadow: var(--shadow-card);
  white-space: nowrap;
}

.hero-source-button:hover {
  background: var(--color-primary);
  color: #fff;
}

.fallback-source-link {
  display: flex;
  align-self: center;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}

.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 360px;
  border-radius: 20px;
  overflow: hidden;
}

.video-wrapper iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
}

.image-credit {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
  text-align: center;
}

.restricted-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  color: var(--color-muted);
}

.carbon-footprint {
  margin: 0;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.carbon-footprint .value {
  font-weight: 700;
}

.carbon-footprint .label {
  font-size: 0.72rem;
  color: var(--color-muted);
}
</style>
