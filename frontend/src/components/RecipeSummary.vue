<script setup lang="ts">
import { Download } from '@lucide/vue'
import { computed } from 'vue'
import NutritionCard from './NutritionCard.vue'
import StepTimerButton from './StepTimerButton.vue'
import { downloadRecipePdf } from '../api/recipes'
import { parseIngredientMentions } from '../utils/cooklangMentions'
import { parseTimerMentions } from '../utils/cooklangTimers'
import { downloadBlob } from '../utils/download'
import { formatDuration } from '../utils/format'
import type { Recipe, RecipeIngredient } from '../types/models'

const props = defineProps<{
  recipe: Recipe
}>()

interface IngredientGroup {
  name: string | null
  items: RecipeIngredient[]
}

// Les ingrédients sont ordonnés côté backend (RecipeIngredient.order) : on regroupe donc les
// group_name identiques et consécutifs sous un même intertitre plutôt que de le répéter en
// texte entre parenthèses sur chaque ligne.
const ingredientGroups = computed<IngredientGroup[]>(() => {
  const groups: IngredientGroup[] = []
  for (const item of props.recipe.ingredients) {
    const name = item.group_name || null
    const last = groups[groups.length - 1]
    if (last && last.name === name) {
      last.items.push(item)
    } else {
      groups.push({ name, items: [item] })
    }
  }
  return groups
})

interface StepSegment {
  text: string
  ingredientId?: number
  timerSeconds?: number
  timerLabel?: string
}

// Découpe le texte d'une étape en segments pour mettre en évidence les "@mentions"
// d'ingrédients (reliées à l'ingrédient correspondant dans la liste ci-contre) et les
// minuteurs "~{quantité%unité}" (voir frontend/src/utils/cooklangMentions.ts et
// cooklangTimers.ts pour la syntaxe).
function stepSegments(instruction: string): StepSegment[] {
  const mentions = parseIngredientMentions(instruction).map((mention) => ({ kind: 'mention' as const, ...mention }))
  const timers = parseTimerMentions(instruction)
    .filter((timer) => timer.totalSeconds !== null)
    .map((timer) => ({ kind: 'timer' as const, ...timer }))
  const ranges = [...mentions, ...timers].sort((a, b) => a.start - b.start)
  if (!ranges.length) return [{ text: instruction }]

  const segments: StepSegment[] = []
  let cursor = 0
  for (const range of ranges) {
    if (range.start > cursor) {
      segments.push({ text: instruction.slice(cursor, range.start) })
    }
    if (range.kind === 'mention') {
      const match = props.recipe.ingredients.find(
        (item) => item.ingredient.name.toLowerCase() === range.displayName.toLowerCase(),
      )
      segments.push({ text: range.displayName, ingredientId: match?.ingredient.id })
    } else {
      segments.push({
        text: instruction.slice(range.start, range.end),
        timerSeconds: range.totalSeconds ?? undefined,
        timerLabel: range.displayName || undefined,
      })
    }
    cursor = range.end
  }
  if (cursor < instruction.length) {
    segments.push({ text: instruction.slice(cursor) })
  }
  return segments
}

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

    <div class="row ingredients-steps-row">
      <div class="card" style="flex: 1; min-width: 260px">
        <h2>{{ $t('recipes.ingredients') }}</h2>
        <template v-for="(group, index) in ingredientGroups" :key="index">
          <h3 v-if="group.name" class="ingredient-group-label">{{ group.name }}</h3>
          <ul class="ingredient-list">
            <li v-for="item in group.items" :key="item.id" :id="`ingredient-${item.ingredient.id}`" class="ingredient-row">
              <span class="ingredient-qty">{{ item.quantity }} {{ item.unit }}</span>
              <RouterLink
                :to="{ name: 'recipes', query: { ingredients: item.ingredient.name } }"
                class="ingredient-name"
              >
                {{ item.ingredient.name }}
              </RouterLink>
            </li>
          </ul>
        </template>
      </div>

      <div class="card" style="flex: 2; min-width: 260px">
        <h2>{{ $t('recipes.steps') }}</h2>
        <ol>
          <li v-for="step in recipe.steps" :key="step.id">
            <template v-for="(segment, index) in stepSegments(step.instruction)" :key="index">
              <a v-if="segment.ingredientId" :href="`#ingredient-${segment.ingredientId}`" class="ingredient-mention">{{
                segment.text
              }}</a>
              <StepTimerButton
                v-else-if="segment.timerSeconds !== undefined"
                :seconds="segment.timerSeconds"
                :label="segment.timerLabel"
              />
              <template v-else>{{ segment.text }}</template>
            </template>
          </li>
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

.ingredients-steps-row {
  align-items: stretch;
}

.ingredients-steps-row > .card {
  display: flex;
  flex-direction: column;
}

.source-line {
  margin-top: 0.75rem;
  word-break: break-all;
}

.ingredient-group-label {
  margin: 1.1rem 0 0.4rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-muted);
}

.ingredient-group-label:first-of-type {
  margin-top: 0.5rem;
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
  color: var(--color-text);
  font-weight: 500;
  text-decoration: none;
}

.ingredient-name:hover {
  color: var(--color-primary-dark);
  text-decoration: underline;
}

.ingredient-mention {
  color: var(--color-primary-dark);
  font-weight: 600;
  text-decoration: none;
}

.ingredient-mention:hover {
  text-decoration: underline;
}
</style>
