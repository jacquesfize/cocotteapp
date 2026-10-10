<script setup lang="ts">
import { ChevronDown } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import type { IngredientSwaps } from '../../composables/useIngredientSwaps'
import { formatQuantity, formatUnit } from '../../utils/format'
import type { IngredientAlternative, RecipeIngredient } from '../../types/models'

// Remplacement d'un ingrédient par l'une de ses alternatives : lien « original » (barré) pour
// revenir en arrière, et pastille qui déplie la liste des options. Partagé entre la page de la
// recette et le mode cuisine, qui utilisent le même état (`swaps`, voir useIngredientSwaps.ts).
const props = defineProps<{
  item: RecipeIngredient
  swaps: IngredientSwaps
}>()
const { t } = useI18n()

function lineText(name: string, quantity: number | string, unit: RecipeIngredient['unit']) {
  return `${formatQuantity(quantity, unit)} ${formatUnit(unit, quantity)} ${name}`.replace(/\s+/g, ' ').trim()
}

function originalText(item: RecipeIngredient) {
  return lineText(item.ingredient.name, item.quantity, item.unit)
}

function alternativeText(item: RecipeIngredient, alternative: IngredientAlternative) {
  return lineText(alternative.ingredient?.name ?? item.ingredient.name, alternative.quantity, alternative.unit)
}

// « 2 alternatives » : texte visible de la pastille, repris dans son nom accessible (avec
// l'ingrédient concerné, pour qu'un lecteur d'écran distingue les lignes).
function alternativesCountText(item: RecipeIngredient) {
  const count = props.swaps.alternativesOf(item).length
  return t('recipes.alternativesCount', { n: count }, count)
}

function swapChipLabel(item: RecipeIngredient) {
  return t('recipes.swapChipLabel', { count: alternativesCountText(item), name: item.ingredient.name })
}

// Choisir une option referme la liste dépliée sous la ligne.
function pickAlternative(item: RecipeIngredient, alternative: IngredientAlternative | null, event: Event) {
  props.swaps.choose(item, alternative)
  ;(event.currentTarget as HTMLElement).closest('details')?.removeAttribute('open')
}
</script>

<template>
  <button
    v-if="swaps.display(item).swapped"
    type="button"
    class="swap-reset"
    :aria-label="$t('recipes.swapBackTo', { text: originalText(item) })"
    @click="swaps.choose(item, null)"
  >
    <s>{{ originalText(item) }}</s>
  </button>
  <details v-if="swaps.alternativesOf(item).length" class="swap">
    <summary class="swap-chip" :aria-label="swapChipLabel(item)">
      {{ alternativesCountText(item) }}
      <ChevronDown :size="14" class="swap-chevron" aria-hidden="true" />
    </summary>
    <ul class="swap-options">
      <li>
        <button
          type="button"
          :aria-pressed="!swaps.display(item).swapped"
          @click="pickAlternative(item, null, $event)"
        >
          <span class="swap-option-text">{{ $t('recipes.swapOriginal') }} · {{ originalText(item) }}</span>
        </button>
      </li>
      <li v-for="alternative in swaps.alternativesOf(item)" :key="alternative.id">
        <button
          type="button"
          :aria-pressed="swaps.display(item).swapped?.id === alternative.id"
          @click="pickAlternative(item, alternative, $event)"
        >
          <span class="swap-option-text">{{ alternativeText(item, alternative) }}</span>
          <span class="swap-option-tag" :data-tag="alternative.tag">{{ $t(`alternativeTag.${alternative.tag}`) }}</span>
          <span v-if="alternative.note" class="swap-option-note">{{ alternative.note }}</span>
        </button>
      </li>
    </ul>
  </details>
</template>

<style scoped>
.swap-reset {
  padding: 0;
  border: 0;
  background: none;
  box-shadow: none;
  color: var(--color-muted);
  font-size: 0.85rem;
  font-weight: 400;
  cursor: pointer;
}

.swap-reset:hover,
.swap-reset:focus-visible {
  color: var(--color-primary-dark);
}

.swap {
  flex-basis: auto;
}

.swap[open] {
  flex-basis: 100%;
}

.swap-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  list-style: none;
}

@media (prefers-reduced-motion: no-preference) {
  .swap-chevron {
    transition: transform 0.15s ease;
  }
}

.swap[open] .swap-chevron {
  transform: rotate(180deg);
}

.swap-chip::-webkit-details-marker {
  display: none;
}

.swap-chip:focus-visible,
.swap-options button:focus-visible {
  outline: 2px solid var(--color-primary-dark);
  outline-offset: 2px;
}

.swap-options {
  list-style: none;
  margin: 0.4rem 0 0;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
}

.swap-options li {
  border-bottom: 1px solid var(--color-border);
}

.swap-options li:last-child {
  border-bottom: 0;
}

.swap-options button {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: baseline;
  gap: 0.1rem 0.6rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: var(--color-text);
  font-weight: 500;
  text-align: left;
  cursor: pointer;
}

.swap-options button[aria-pressed='true'] {
  background: var(--color-primary-soft);
  font-weight: 600;
}

.swap-option-tag {
  font-size: 0.8rem;
  color: var(--color-primary-dark);
}

.swap-option-note {
  flex-basis: 100%;
  font-size: 0.85rem;
  font-weight: 400;
  color: var(--color-muted);
}
</style>
