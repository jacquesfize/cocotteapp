<script setup lang="ts">
import { Link2, Lock } from '@lucide/vue'
import { computed } from 'vue'
import AllergenBadges from '../nutrition/AllergenBadges.vue'
import ImageWithCredit from '../shared/ImageWithCredit.vue'
import RecipeRating from './RecipeRating.vue'
import { formatQuantity, formatUnit } from '../../utils/format'
import { recipeImageUrl } from '../../utils/recipeImageUrl'
import { groupIngredients } from '../../utils/recipeSteps'
import type { RecipeRatingResult } from '../../api/recipes'
import type { Recipe } from '../../types/models'

const props = defineProps<{
  recipe: Recipe
}>()

// La liste d'ingrédients (et les temps) ne relève pas du droit d'auteur : l'API l'expose même
// quand le contenu rédactionnel (description, étapes) est masqué.
const ingredientGroups = computed(() => groupIngredients(props.recipe.ingredients ?? []))

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
      v-else-if="recipeImageUrl(recipe)"
      class="hero-photo-wrapper"
      :image-url="recipeImageUrl(recipe)"
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
        class="hero-source-button photo-cta-pill"
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

    <section v-if="ingredientGroups.length" class="restricted-ingredients">
      <h2>{{ $t('recipes.ingredients') }}</h2>
      <template v-for="(group, index) in ingredientGroups" :key="index">
        <h3 v-if="group.name" class="ingredient-group-label">{{ group.name }}</h3>
        <ul class="ingredient-list">
          <li v-for="item in group.items" :key="item.id" class="ingredient-row">
            <span class="ingredient-qty">{{ formatQuantity(item.quantity, item.unit) }} {{ formatUnit(item.unit, item.quantity) }}</span>
            <span class="ingredient-name">{{ item.ingredient.name }}</span>
          </li>
        </ul>
      </template>
    </section>

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

.restricted-ingredients h2 {
  margin: 0 0 0.25rem;
}

.ingredient-group-label {
  margin: 1.1rem 0 0.4rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-muted);
}

.ingredient-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.ingredient-row {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border);
}

.ingredient-row:last-child {
  border-bottom: none;
}

.ingredient-qty {
  flex-shrink: 0;
  min-width: 4.5rem;
  color: var(--color-muted);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.ingredient-name {
  font-weight: 500;
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
