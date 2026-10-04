<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { getRecipeNutrition } from '../../api/recipes'
import type { NutrientTotals } from '../../types/models'
import { formatNumber } from '../../utils/format'

const props = defineProps<{
  recipeId: string | number
}>()

const nutrition = ref<NutrientTotals | null>(null)
const carbonPerServing = ref<number | null>(null)

async function load() {
  nutrition.value = null
  carbonPerServing.value = null
  const data = await getRecipeNutrition(props.recipeId)
  nutrition.value = data.per_serving
  carbonPerServing.value = data.carbon_footprint_per_serving_kg_co2e
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
        <span class="value">{{ formatNumber(nutrition.calories_kcal, 0) }}</span>
        <span class="label">{{ $t('nutrition.calories') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.protein_g, 1, { fixed: true }) }} g</span>
        <span class="label">{{ $t('nutrition.protein') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.carbs_g, 1, { fixed: true }) }} g</span>
        <span class="label">{{ $t('nutrition.carbs') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.fat_g, 1, { fixed: true }) }} g</span>
        <span class="label">{{ $t('nutrition.fat') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.iron_mg, 1, { fixed: true }) }} mg</span>
        <span class="label">{{ $t('nutrition.iron') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.vitamin_b12_ug, 1, { fixed: true }) }} µg</span>
        <span class="label">{{ $t('nutrition.b12') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.calcium_mg, 0, { fixed: true }) }} mg</span>
        <span class="label">{{ $t('nutrition.calcium') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.omega3_g, 1, { fixed: true }) }} g</span>
        <span class="label">{{ $t('nutrition.omega3') }}</span>
      </div>
      <div>
        <span class="value">{{ formatNumber(nutrition.zinc_mg, 1, { fixed: true }) }} mg</span>
        <span class="label">{{ $t('nutrition.zinc') }}</span>
      </div>
    </div>
    <!-- 0 = aucun ingrédient avec une donnée carbone : on masque plutôt qu'afficher "0 kg CO₂e". -->
    <p v-if="carbonPerServing" class="carbon-footprint">
      <span class="value">{{ formatNumber(carbonPerServing, 2) }} kg CO₂e</span>
      <span class="label">{{ $t('nutrition.carbonPerServing') }}</span>
    </p>
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

.carbon-footprint {
  margin: 0.9rem 0 0;
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
