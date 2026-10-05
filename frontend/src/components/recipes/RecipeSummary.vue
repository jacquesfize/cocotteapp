<script setup lang="ts">
import { ChefHat, Clock, CookingPot, Download, Flame, Image as ImageIcon, Link2, Users, Utensils } from '@lucide/vue'
import { computed, ref } from 'vue'
import AllergenBadges from '../nutrition/AllergenBadges.vue'
import CookwareModal from './CookwareModal.vue'
import IngredientSwapControls from './IngredientSwapControls.vue'
import BaseModal from '../shared/BaseModal.vue'
import ImageWithCredit from '../shared/ImageWithCredit.vue'
import NutritionCard from '../nutrition/NutritionCard.vue'
import RecipeCookMode from './RecipeCookMode.vue'
import RecipeRating from './RecipeRating.vue'
import StepTimerButton from './StepTimerButton.vue'
import { downloadRecipePdf } from '../../api/recipes'
import type { RecipeRatingResult } from '../../api/recipes'
import { useIngredientSwaps } from '../../composables/useIngredientSwaps'
import { buildStepSegments, groupIngredients } from '../../utils/recipeSteps'
import { downloadBlob } from '../../utils/download'
import { formatDuration, formatQuantity, formatUnit } from '../../utils/format'
import { recipeImageUrl } from '../../utils/recipeImageUrl'
import type { Cookware, Recipe } from '../../types/models'

const props = defineProps<{
  recipe: Recipe
}>()

const emit = defineEmits<{
  rated: [result: RecipeRatingResult]
}>()

const showCookMode = ref(false)
// Matériel affiché dans CookwareModal (photo + crédit), ouvert depuis la liste ou une étape.
const openCookware = ref<Cookware | null>(null)

function openCookwareById(id?: number) {
  openCookware.value = props.recipe.cookware?.find((item) => item.id === id) ?? null
}
// Id de l'étape dont la photo est actuellement affichée en grand (bouton icône -> BaseModal),
// pour éviter d'afficher l'image en flux dans la liste (casse la numérotation, voir capture
// utilisateur) : au plus une modale ouverte à la fois.
const openStepImageId = ref<number | null>(null)

// Voir frontend/src/utils/recipeSteps.ts (partagé avec le mode cuisine plein écran).
const ingredientGroups = computed(() => groupIngredients(props.recipe.ingredients))

function stepSegments(instruction: string) {
  return buildStepSegments(instruction, props.recipe.ingredients, props.recipe.cookware ?? [])
}

// Remplacement d'un ingrédient par une alternative, le temps de la consultation : partagé avec le
// mode cuisine, non enregistré.
const swaps = useIngredientSwaps()

function rowIndex(item: Recipe['ingredients'][number]) {
  return props.recipe.ingredients.indexOf(item)
}

async function handleDownloadPdf() {
  const blob = await downloadRecipePdf(props.recipe.id)
  downloadBlob(blob, `${props.recipe.slug}.pdf`)
}
</script>

<template>
  <div>
    <div class="row summary-header">
      <div class="row header-actions">
        <button
          v-if="recipe.steps.length"
          class="cook-mode-button"
          :aria-label="$t('recipes.cookMode')"
          @click="showCookMode = true"
        >
          <ChefHat :size="16" /><span class="cook-mode-label">{{ $t('recipes.cookMode') }}</span>
        </button>
        <button class="secondary download-button" :aria-label="$t('recipes.downloadPdf')" @click="handleDownloadPdf">
          <Download :size="16" />
        </button>
      </div>
      <div class="meta-chips">
        <span class="meta-chip"><Utensils :size="14" />{{ $t(`diet.${recipe.diet_type}`) }}</span>
        <span class="meta-chip"><Users :size="14" />{{ recipe.servings }} {{ $t('recipes.servings') }}</span>
        <span v-if="recipe.prep_time_minutes" class="meta-chip"><Clock :size="14" />{{ $t('recipes.prep') }} {{ formatDuration(recipe.prep_time_minutes) }}</span>
        <span v-if="recipe.cook_time_minutes" class="meta-chip"><Flame :size="14" />{{ $t('recipes.cook') }} {{ formatDuration(recipe.cook_time_minutes) }}</span>
      </div>
    </div>

    <AllergenBadges
      :allergens="recipe.allergens ?? []"
      :unverified="recipe.allergens_unverified"
      class="summary-allergens"
    />

    <RecipeRating
      :key="recipe.id"
      :recipe-id="recipe.id"
      :average-rating="recipe.average_rating"
      :ratings-count="recipe.ratings_count"
      :my-rating="recipe.my_rating"
      @rated="emit('rated', $event)"
    />

    <div v-if="recipeImageUrl(recipe) || recipe.youtube_id" class="media-row">
      <div v-if="recipeImageUrl(recipe)" class="recipe-photo-wrapper">
        <!-- Même bouton "Source" centré sur la photo que RecipeRestrictedNotice.vue ; sans photo,
             RecipeDetailView.vue affiche le lien Source au-dessus du contenu. -->
        <ImageWithCredit
          class="recipe-photo-frame"
          :image-url="recipeImageUrl(recipe)"
          :source-url="recipe.image ? null : recipe.source_url"
          :license="recipe.image_license"
          :credit-author="recipe.image_credit_author"
          :credit-source-url="recipe.image_credit_source_url"
          :credit-license-url="recipe.image_credit_license_url"
          :credit-note="recipe.image_credit_note"
        >
          <a
            v-if="recipe.source_url"
            :href="recipe.source_url"
            target="_blank"
            rel="noopener noreferrer"
            class="photo-source-button photo-cta-pill"
          >
            <Link2 :size="18" /><span>{{ $t('recipes.source') }}</span>
          </a>
        </ImageWithCredit>
      </div>

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
            <li
              v-for="item in group.items"
              :key="item.id"
              :id="`ingredient-row-${rowIndex(item)}`"
              class="ingredient-row"
              :class="{ swapped: swaps.display(item).swapped }"
            >
              <span class="ingredient-qty">{{ formatQuantity(swaps.display(item).quantity, swaps.display(item).unit) }} {{ formatUnit(swaps.display(item).unit, swaps.display(item).quantity) }}</span>
              <div class="ingredient-main">
                <RouterLink
                  :to="{ name: 'recipes', query: { ingredients: swaps.display(item).name } }"
                  class="ingredient-name"
                >
                  {{ swaps.display(item).name }}
                </RouterLink>
                <IngredientSwapControls :item="item" :swaps="swaps" />
              </div>
            </li>
          </ul>
        </template>

        <template v-if="recipe.cookware?.length">
          <h2 class="cookware-title">{{ $t('cookware.title') }}</h2>
          <ul class="cookware-list">
            <li v-for="item in recipe.cookware" :id="`cookware-${item.id}`" :key="item.id">
              <button type="button" class="cookware-chip" @click="openCookware = item">
                <img v-if="item.image" :src="item.image" class="cookware-chip-image" alt="" />
                <span v-else-if="item.emoji" aria-hidden="true">{{ item.emoji }}</span>
                <CookingPot v-else :size="14" aria-hidden="true" />{{ item.name }}
              </button>
            </li>
          </ul>
        </template>
      </div>

      <div class="card" style="flex: 2; min-width: 260px">
        <h2>{{ $t('recipes.steps') }}</h2>
        <ol>
          <li v-for="step in recipe.steps" :key="step.id">
            <template v-for="(segment, index) in stepSegments(step.instruction)" :key="index">
              <a v-if="segment.ingredientId" :href="`#ingredient-row-${segment.ingredientIndex}`" class="ingredient-mention">{{
                segment.text
              }}</a>
              <button
                v-else-if="segment.cookware?.id"
                type="button"
                class="cookware-mention"
                @click="openCookwareById(segment.cookware.id)"
              >{{ segment.text }}</button>
              <StepTimerButton
                v-else-if="segment.timerSeconds !== undefined"
                :seconds="segment.timerSeconds"
                :label="segment.timerLabel"
              />
              <template v-else>{{ segment.text }}</template>
            </template>
            <button
              v-if="recipeImageUrl(step)"
              type="button"
              class="step-image-btn"
              :aria-label="$t('recipes.viewStepImage')"
              @click="openStepImageId = step.id"
            >
              <ImageIcon :size="15" />
            </button>

            <BaseModal
              v-if="openStepImageId === step.id"
              :title="$t('recipes.stepImage')"
              @close="openStepImageId = null"
            >
              <ImageWithCredit
                class="step-photo-modal-frame"
                :image-url="recipeImageUrl(step)"
                :license="step.image_license"
                :credit-author="step.image_credit_author"
                :credit-source-url="step.image_credit_source_url"
                :credit-license-url="step.image_credit_license_url"
                :credit-note="step.image_credit_note"
              />
            </BaseModal>
          </li>
        </ol>
      </div>
    </div>

    <NutritionCard :recipe-id="recipe.id" style="margin-top: 1rem" />

    <CookwareModal v-if="openCookware" :cookware="openCookware" show-recipes-link @close="openCookware = null" />

    <RecipeCookMode v-if="showCookMode" :recipe="recipe" :swaps="swaps" @close="showCookMode = false" />
  </div>
</template>

<style scoped>
.summary-allergens {
  margin-bottom: 0.75rem;
}

.summary-header {
  flex-direction: column;
  align-items: stretch;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

@media (min-width: 700px) {
  .summary-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .meta-chips {
    order: 1;
  }

  .header-actions {
    order: 2;
  }
}

.meta-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  min-width: 0;
}

.header-actions {
  justify-content: flex-start;
  flex-shrink: 0;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  border-radius: 999px;
  background: var(--color-surface-muted);
  color: var(--color-text);
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}

.meta-chip svg {
  color: var(--color-primary-dark);
  flex-shrink: 0;
}

.download-button,
.cook-mode-button {
  flex-shrink: 0;
}

.download-button {
  width: 2.75rem;
  height: 2.75rem;
  min-height: auto;
  padding: 0;
  border-radius: 999px;
  justify-content: center;
}

/* Le libellé « Mode cuisine » reste visible sur mobile : une pastille orange sans texte
   n'était pas identifiable (audit UX). */

.media-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.recipe-photo-wrapper {
  flex: 1;
  min-width: 260px;
}

.recipe-photo-frame :deep(img) {
  display: block;
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

.ingredient-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.25rem 0.6rem;
}

/* Ligne dont l'ingrédient a été remplacé : un filet à gauche, couleur de l'application. */
.ingredient-row.swapped {
  padding-left: 0.6rem;
  border-left: 3px solid var(--color-primary);
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

.cookware-title {
  margin-top: 1.5rem;
}

.cookware-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.cookware-chip {
  min-height: auto;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: var(--color-surface-muted);
  color: var(--color-text);
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
}

.cookware-chip-image {
  width: 1.6rem;
  height: 1.6rem;
  margin-left: -0.45rem;
  border-radius: 50%;
  object-fit: cover;
}

.cookware-chip svg {
  color: var(--color-primary-dark);
}

.cookware-chip:hover {
  background: var(--color-primary-soft);
}

.cookware-mention {
  min-height: auto;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
  color: var(--color-text);
  font-weight: 600;
  text-decoration: underline dotted var(--color-primary-dark);
  text-underline-offset: 3px;
}

.step-image-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.7rem;
  height: 1.7rem;
  min-height: 1.7rem;
  padding: 0;
  margin: 0 0 0.1rem 0.4rem;
  border-radius: 999px;
  background: var(--color-surface-muted);
  color: var(--color-primary-dark);
  vertical-align: middle;
}

.step-image-btn:hover {
  background: var(--color-primary-soft);
}

.step-photo-modal-frame :deep(img) {
  display: block;
  width: 100%;
  max-height: 60vh;
  border-radius: 12px;
  object-fit: contain;
}
</style>
