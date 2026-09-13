<script setup lang="ts">
import { Download } from '@lucide/vue'
import NutritionCard from './NutritionCard.vue'
import { downloadRecipePdf } from '../api/recipes'
import { downloadBlob } from '../utils/download'
import { formatDuration } from '../utils/format'
import type { Recipe } from '../types/models'

const props = defineProps<{
  recipe: Recipe
}>()

async function handleDownloadPdf() {
  const blob = await downloadRecipePdf(props.recipe.id)
  downloadBlob(blob, `${props.recipe.slug}.pdf`)
}
</script>

<template>
  <div>
    <div class="row summary-header">
      <p class="muted" style="margin: 0">
        {{ $t(`diet.${recipe.diet_type}`) }} · {{ recipe.servings }} {{ $t('recipes.servings') }} ·
        {{ $t('recipes.prep') }} {{ formatDuration(recipe.prep_time_minutes) }} · {{ $t('recipes.cook') }}
        {{ formatDuration(recipe.cook_time_minutes) }}
      </p>
      <button class="secondary" @click="handleDownloadPdf"><Download :size="16" />{{ $t('recipes.downloadPdf') }}</button>
    </div>

    <div v-if="recipe.image || recipe.image_url || recipe.youtube_id" class="media-row">
      <img
        v-if="recipe.image || recipe.image_url"
        :src="recipe.image || recipe.image_url"
        class="recipe-photo"
        alt=""
      />

      <div v-if="recipe.youtube_id" class="video-wrapper">
        <iframe
          :src="`https://www.youtube-nocookie.com/embed/${recipe.youtube_id}`"
          title="YouTube video player"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
        />
      </div>
    </div>

    <p v-if="recipe.description">{{ recipe.description }}</p>

    <div class="row" style="align-items: flex-start">
      <div class="card" style="flex: 1; min-width: 260px">
        <h2>{{ $t('recipes.ingredients') }}</h2>
        <ul>
          <li v-for="item in recipe.ingredients" :key="item.id">
            {{ item.quantity }} {{ item.unit }} —
            <RouterLink :to="{ name: 'recipes', query: { ingredients: item.ingredient.name } }">
              {{ item.ingredient.name }}
            </RouterLink>
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

    <p v-if="recipe.source_url" class="muted source-line">
      {{ $t('recipes.source') }} :
      <a :href="recipe.source_url" target="_blank" rel="noopener noreferrer">{{ recipe.source_url }}</a>
    </p>

    <NutritionCard :recipe-id="recipe.id" style="margin-top: 1rem" />
  </div>
</template>

<style scoped>
.summary-header {
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.media-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.recipe-photo {
  display: block;
  flex: 1;
  min-width: 260px;
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 20px;
}

.video-wrapper {
  position: relative;
  flex: 1;
  min-width: 260px;
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 320px;
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

.source-line {
  margin-top: 0.75rem;
  word-break: break-all;
}
</style>
