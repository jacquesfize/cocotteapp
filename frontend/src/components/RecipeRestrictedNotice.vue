<script setup lang="ts">
import { Lock } from '@lucide/vue'
import { computed } from 'vue'
import AllergenBadges from './AllergenBadges.vue'
import { imageCreditDomain } from '../utils/imageCredit'
import type { Recipe } from '../types/models'

const props = defineProps<{
  recipe: Recipe
}>()

const imageCredit = computed(() =>
  !props.recipe.image && props.recipe.image_url ? imageCreditDomain(props.recipe.source_url) : null,
)
</script>

<template>
  <div class="card restricted-notice">
    <div v-if="recipe.image || recipe.image_url" class="restricted-photo-wrapper">
      <img :src="recipe.image || recipe.image_url" class="restricted-photo" alt="" />
      <p v-if="imageCredit" class="image-credit muted">{{ $t('recipes.imageCredit', { domain: imageCredit }) }}</p>
    </div>

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

.restricted-photo-wrapper img {
  display: block;
  width: 100%;
  max-height: 360px;
  object-fit: cover;
  border-radius: 20px;
}

.image-credit {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
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
