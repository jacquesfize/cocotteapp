<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { getRecipeNutrition } from '../api/recipes'
import type { NutrientTotals } from '../types/models'

const props = defineProps<{
  recipeId: string | number
}>()

const nutrition = ref<NutrientTotals | null>(null)

async function load() {
  nutrition.value = null
  const data = await getRecipeNutrition(props.recipeId)
  nutrition.value = data.per_serving
}

watch(() => props.recipeId, load)
onMounted(load)
</script>

<template>
  <div v-if="nutrition" class="card">
    <h2>{{ $t('nutrition.title') }}</h2>
    <p class="muted" style="margin: -0.5rem 0 0">{{ $t('nutrition.perServing') }}</p>
    <div class="nutrition-grid">
      <div>
        <span class="value">{{ Math.round(nutrition.calories_kcal) }}</span>
        <span class="label">{{ $t('nutrition.calories') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.protein_g.toFixed(1) }} g</span>
        <span class="label">{{ $t('nutrition.protein') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.carbs_g.toFixed(1) }} g</span>
        <span class="label">{{ $t('nutrition.carbs') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.fat_g.toFixed(1) }} g</span>
        <span class="label">{{ $t('nutrition.fat') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.iron_mg.toFixed(1) }} mg</span>
        <span class="label">{{ $t('nutrition.iron') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.vitamin_b12_ug.toFixed(1) }} µg</span>
        <span class="label">{{ $t('nutrition.b12') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.calcium_mg.toFixed(0) }} mg</span>
        <span class="label">{{ $t('nutrition.calcium') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.omega3_g.toFixed(1) }} g</span>
        <span class="label">{{ $t('nutrition.omega3') }}</span>
      </div>
      <div>
        <span class="value">{{ nutrition.zinc_mg.toFixed(1) }} mg</span>
        <span class="label">{{ $t('nutrition.zinc') }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 0.9rem;
  margin-top: 0.75rem;
}

.nutrition-grid > div {
  display: flex;
  flex-direction: column;
}

.nutrition-grid .value {
  font-weight: 700;
}

.nutrition-grid .label {
  font-size: 0.72rem;
  color: var(--color-muted);
}
</style>
