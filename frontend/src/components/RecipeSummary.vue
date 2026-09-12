<script setup>
import { formatDuration } from '../utils/format'

defineProps({
  recipe: { type: Object, required: true },
})
</script>

<template>
  <div>
    <p class="muted">
      {{ $t(`diet.${recipe.diet_type}`) }} · {{ recipe.servings }} {{ $t('recipes.servings') }} ·
      {{ $t('recipes.prep') }} {{ formatDuration(recipe.prep_time_minutes) }} · {{ $t('recipes.cook') }}
      {{ formatDuration(recipe.cook_time_minutes) }}
    </p>
    <p v-if="recipe.description">{{ recipe.description }}</p>

    <div class="row" style="align-items: flex-start">
      <div class="card" style="flex: 1; min-width: 260px">
        <h2>{{ $t('recipes.ingredients') }}</h2>
        <ul>
          <li v-for="item in recipe.ingredients" :key="item.id">
            {{ item.quantity }} {{ item.unit }} — {{ item.ingredient.name }}
            <span v-if="item.group_name" class="muted">({{ item.group_name }})</span>
          </li>
        </ul>
      </div>

      <div class="card" style="flex: 2; min-width: 260px">
        <h2>{{ $t('recipes.steps') }}</h2>
        <ol>
          <li v-for="step in recipe.steps" :key="step.id">{{ step.instruction }}</li>
        </ol>
      </div>
    </div>
  </div>
</template>
