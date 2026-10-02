<script setup lang="ts">
import { Link2, Lock } from '@lucide/vue'
import AllergenBadges from './AllergenBadges.vue'
import ImageWithCredit from './ImageWithCredit.vue'
import RecipeRating from './RecipeRating.vue'
import type { RecipeRatingResult } from '../api/recipes'
import type { Recipe } from '../types/models'

defineProps<{
  recipe: Recipe
}>()

const emit = defineEmits<{
  rated: [result: RecipeRatingResult]
}>()
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
    <ImageWithCredit
      v-else-if="recipe.image || recipe.image_url"
      class="hero-photo-wrapper"
      :image-url="recipe.image || recipe.image_url"
      :source-url="recipe.image ? null : recipe.source_url"
      :license="recipe.image_license"
      :credit-author="recipe.image_credit_author"
      :credit-source-url="recipe.image_credit_source_url"
      :credit-license-url="recipe.image_credit_license_url"
      :credit-note="recipe.image_credit_note"
      overlay
    >
      <a
        v-if="recipe.source_url"
        :href="recipe.source_url"
        target="_blank"
        rel="noopener noreferrer"
        class="hero-source-button"
      >
        <Link2 :size="18" /><span>{{ $t('recipes.source') }}</span>
      </a>
    </ImageWithCredit>
    <a
      v-else-if="recipe.source_url"
      :href="recipe.source_url"
      target="_blank"
      rel="noopener noreferrer"
      class="secondary fallback-source-link"
    >
      <Link2 :size="18" /><span>{{ $t('recipes.source') }}</span>
    </a>

    <div class="restricted-banner" role="note">
      <Lock :size="18" />
      <i18n-t keypath="recipes.restrictedNotice" tag="p" scope="global">
        <template #copyright><strong>{{ $t('recipes.restrictedNoticeCopyright') }}</strong></template>
        <template #visibility><strong>{{ $t('recipes.restrictedNoticeVisibility') }}</strong></template>
      </i18n-t>
    </div>

    <AllergenBadges :allergens="recipe.allergens ?? []" :unverified="recipe.allergens_unverified" />

    <RecipeRating
      :key="recipe.id"
      :recipe-id="recipe.id"
      :average-rating="recipe.average_rating"
      :ratings-count="recipe.ratings_count"
      :my-rating="recipe.my_rating"
      @rated="emit('rated', $event)"
    />

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
  border-radius: 20px;
  overflow: hidden;
}

.hero-photo-wrapper :deep(img) {
  display: block;
  width: 100%;
  height: 320px;
  object-fit: cover;
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
  color: var(--color-on-primary);
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

.restricted-banner {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-primary-soft);
  border-radius: 14px;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.restricted-banner p {
  margin: 0;
  font-weight: 600;
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
