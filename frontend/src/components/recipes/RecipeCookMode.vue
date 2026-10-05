<script setup lang="ts">
import { Check, ChevronLeft, ChevronRight, CirclePlay, ListChecks, Pause, Play, RotateCcw, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ImageWithCredit from '../shared/ImageWithCredit.vue'
import CookwareModal from './CookwareModal.vue'
import StepTimerButton from './StepTimerButton.vue'
import { useStepTimer, type StepTimerHandle } from '../../composables/useStepTimer'
import { formatQuantity, formatUnit } from '../../utils/format'
import type { IngredientSwaps } from '../../composables/useIngredientSwaps'
import { buildStepSegments, groupIngredients, ingredientRowsFor } from '../../utils/recipeSteps'
import { recipeImageUrl } from '../../utils/recipeImageUrl'
import type { Cookware, Recipe, RecipeIngredient } from '../../types/models'

const props = defineProps<{
  recipe: Recipe
  // Remplacements choisis sur la page de la recette (voir RecipeSummary.vue) : appliqués à la
  // liste des ingrédients et aux quantités des mentions.
  swaps?: IngredientSwaps
}>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()

const currentIndex = ref(0)
const direction = ref<'next' | 'prev'>('next')
const showIngredients = ref(false)
// Le survol affiche le popover temporairement ; un clic (ou le focus clavier) l'"épingle" pour
// qu'il reste visible le temps de lire la quantité, même une fois la souris repartie.
const hoveredIngredientId = ref<number | null>(null)
const pinnedIngredientId = ref<number | null>(null)

const steps = computed(() => props.recipe.steps)
const currentStep = computed(() => steps.value[currentIndex.value])

// Pilote la mise en page de l'étape : quand il y a une photo, l'image occupe la part dominante
// de la hauteur disponible et le texte est relégué à une bande en bas (qui peut grandir si le
// texte est long) ; sans photo, le texte garde toute la place comme avant.
const hasStepImage = computed(() => Boolean(currentStep.value && recipeImageUrl(currentStep.value)))

// Calculé une seule fois, hors de tout `computed` : les minuteurs doivent survivre à la
// navigation entre étapes (voir timerHandles ci-dessous), donc on ne peut pas se permettre de
// les recréer si cette liste était réévaluée en réaction à un changement réactif quelconque.
const allStepsSegments = props.recipe.steps.map((step) =>
  buildStepSegments(step.instruction, props.recipe.ingredients, props.recipe.cookware ?? []),
)

interface TimerRegistryEntry {
  label?: string
  handle: StepTimerHandle
}

// Un minuteur par segment "timer", tous étapes confondues, créé une fois pour toute la session
// du mode cuisine : la pastille inline (affichée uniquement pour l'étape courante) et le dock
// du bas pilotent la même instance, donc démarrer un minuteur puis changer d'étape ne l'arrête
// plus, et le contrôler depuis le dock se répercute sur la pastille (et inversement).
const timerHandles = new Map<string, TimerRegistryEntry>()
allStepsSegments.forEach((segments, stepIndex) => {
  segments.forEach((segment, segmentIndex) => {
    if (segment.timerSeconds !== undefined) {
      timerHandles.set(`${stepIndex}-${segmentIndex}`, {
        label: segment.timerLabel,
        handle: useStepTimer(segment.timerSeconds, segment.timerLabel),
      })
    }
  })
})

const currentSegments = computed(() => allStepsSegments[currentIndex.value] ?? [])

const activeTimers = computed(() =>
  Array.from(timerHandles.entries())
    .filter(([, entry]) => entry.handle.phase.value !== 'idle')
    .map(([id, entry]) => ({ id, ...entry })),
)

const ingredientGroups = computed(() => groupIngredients(props.recipe.ingredients))

// Emoji propre au matériel s'il en a un, sinon une poêle générique.
const DEFAULT_COOKWARE_EMOJI = '🍳'
// Matériel affiché dans CookwareModal (photo + crédit), ouvert depuis une étape ou le panneau.
const openCookware = ref<Cookware | null>(null)

function openCookwareById(id?: number) {
  openCookware.value = props.recipe.cookware?.find((item) => item.id === id) ?? null
}

function findCookware(id?: number) {
  return props.recipe.cookware?.find((item) => item.id === id)
}

function cookwareEmoji(id?: number) {
  return findCookware(id)?.emoji || DEFAULT_COOKWARE_EMOJI
}

const isFirstStep = computed(() => currentIndex.value === 0)
const isLastStep = computed(() => currentIndex.value === steps.value.length - 1)

const youtubeUrl = computed(() =>
  props.recipe.youtube_id ? `https://www.youtube.com/watch?v=${props.recipe.youtube_id}` : null,
)

function goPrev() {
  if (!isFirstStep.value) {
    direction.value = 'prev'
    currentIndex.value -= 1
  }
}

// Depuis la dernière étape, "passer à la suivante" quitte le mode cuisine plutôt que de rester
// bloqué sans rien faire — cohérent que ce soit déclenché par le bouton, la flèche clavier ou un
// swipe (tous passent par cette fonction).
function goNext() {
  if (isLastStep.value) {
    emit('close')
    return
  }
  direction.value = 'next'
  currentIndex.value += 1
}

function goToStep(index: number) {
  direction.value = index > currentIndex.value ? 'next' : 'prev'
  currentIndex.value = index
}

// Quantité et nom affichés d'une ligne : ceux de l'alternative choisie, sinon ceux de la recette.
function shown(item: RecipeIngredient) {
  return props.swaps
    ? props.swaps.display(item)
    : { name: item.ingredient.name, quantity: item.quantity, unit: item.unit, swapped: null }
}

// Une ligne par partie où l'ingrédient sert (beurre de la pâte, beurre de la garniture...).
function findIngredientRows(ingredientId: number): RecipeIngredient[] {
  return ingredientRowsFor(props.recipe.ingredients, ingredientId)
}

function isIngredientPopoverOpen(ingredientId: number) {
  return pinnedIngredientId.value === ingredientId || hoveredIngredientId.value === ingredientId
}

function toggleIngredientPopover(ingredientId: number) {
  pinnedIngredientId.value = pinnedIngredientId.value === ingredientId ? null : ingredientId
}

function showIngredientPopover(ingredientId: number) {
  hoveredIngredientId.value = ingredientId
}

function hideIngredientPopover(ingredientId: number) {
  if (hoveredIngredientId.value === ingredientId) hoveredIngredientId.value = null
}

function closeIngredientPopover() {
  pinnedIngredientId.value = null
  hoveredIngredientId.value = null
}

// Un clic en dehors du popover épinglé le referme — le survol, lui, se referme déjà tout seul
// via `hideIngredientPopover` au `mouseleave`.
function handleWindowClick(event: MouseEvent) {
  if (pinnedIngredientId.value === null) return
  const target = event.target as HTMLElement | null
  if (!target?.closest('.ingredient-mention-wrap')) {
    pinnedIngredientId.value = null
  }
}

// Seuil en pixels avant de considérer un geste tactile comme un swipe horizontal plutôt qu'un
// simple défilement vertical du texte de l'étape.
const SWIPE_THRESHOLD = 50
let touchStartX = 0
let touchStartY = 0

function onTouchStart(event: TouchEvent) {
  touchStartX = event.touches[0].clientX
  touchStartY = event.touches[0].clientY
}

function onTouchEnd(event: TouchEvent) {
  const touch = event.changedTouches[0]
  const deltaX = touch.clientX - touchStartX
  const deltaY = touch.clientY - touchStartY
  if (Math.abs(deltaX) < SWIPE_THRESHOLD || Math.abs(deltaX) < Math.abs(deltaY)) return
  if (deltaX < 0) goNext()
  else goPrev()
}

function handleKeydown(event: KeyboardEvent) {
  // La fenêtre du matériel gère elle-même Échap (BaseModal) : ne pas fermer le mode cuisine avec.
  if (openCookware.value) return
  if (event.key === 'Escape') {
    if (pinnedIngredientId.value !== null || hoveredIngredientId.value !== null) closeIngredientPopover()
    else if (showIngredients.value) showIngredients.value = false
    else emit('close')
  } else if (event.key === 'ArrowRight') {
    goNext()
  } else if (event.key === 'ArrowLeft') {
    goPrev()
  }
}

// Prise de contrôle complète de l'écran : on bloque le défilement de la page en dessous
// pendant que le mode cuisine est ouvert.
onMounted(() => {
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('click', handleWindowClick)
})
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('click', handleWindowClick)
})
</script>

<template>
  <div class="cook-mode" role="dialog" aria-modal="true" :aria-label="recipe.title">
    <header class="cook-mode-header">
      <button type="button" class="secondary icon-btn" :aria-label="t('common.close')" @click="emit('close')">
        <X :size="18" />
      </button>
      <div class="cook-mode-progress-group">
        <span class="cook-mode-progress">{{ t('recipes.cookModeStep', { current: currentIndex + 1, total: steps.length }) }}</span>
        <a
          v-if="youtubeUrl"
          :href="youtubeUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="cook-mode-video-link"
          :aria-label="t('recipes.cookModeWatchVideo')"
        >
          <CirclePlay :size="16" />
        </a>
      </div>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ active: showIngredients }"
        :aria-label="t('recipes.cookModeIngredients')"
        :aria-pressed="showIngredients"
        @click="showIngredients = !showIngredients"
      >
        <ListChecks :size="18" />
      </button>
    </header>

    <div class="cook-mode-body" @touchstart="onTouchStart" @touchend="onTouchEnd">
      <button
        v-if="!isFirstStep"
        type="button"
        class="secondary icon-btn cook-mode-nav prev"
        :aria-label="t('recipes.cookModePrev')"
        @click="goPrev"
      >
        <ChevronLeft :size="22" />
      </button>

      <div class="cook-mode-step">
        <div class="cook-mode-step-content" :class="{ 'has-image': hasStepImage }">
          <ImageWithCredit
            v-if="hasStepImage"
            :key="`img-${currentStep.id}`"
            class="cook-mode-step-photo"
            :image-url="recipeImageUrl(currentStep)"
            :license="currentStep.image_license"
            :credit-author="currentStep.image_credit_author"
            :credit-source-url="currentStep.image_credit_source_url"
            :credit-license-url="currentStep.image_credit_license_url"
            :credit-note="currentStep.image_credit_note"
            compact
          />
          <Transition :name="direction === 'next' ? 'cook-step-next' : 'cook-step-prev'" mode="out-in">
          <p v-if="currentStep" :key="currentStep.id" class="cook-mode-step-text">
            <template v-for="(segment, index) in currentSegments" :key="index">
              <span
                v-if="segment.ingredientId"
                class="ingredient-mention-wrap"
                @mouseenter="showIngredientPopover(segment.ingredientId)"
                @mouseleave="hideIngredientPopover(segment.ingredientId)"
              >
                <button
                  type="button"
                  class="ingredient-mention"
                  :aria-describedby="`cook-mode-ingredient-popover-${currentIndex}-${index}`"
                  :aria-expanded="isIngredientPopoverOpen(segment.ingredientId)"
                  @click.stop="toggleIngredientPopover(segment.ingredientId)"
                  @focus="showIngredientPopover(segment.ingredientId)"
                  @blur="hideIngredientPopover(segment.ingredientId)"
                >{{ segment.text }}</button>
                <div
                  v-if="isIngredientPopoverOpen(segment.ingredientId)"
                  :id="`cook-mode-ingredient-popover-${currentIndex}-${index}`"
                  class="ingredient-popover"
                  role="tooltip"
                >
                  <p v-for="row in findIngredientRows(segment.ingredientId)" :key="row.id" class="ingredient-popover-qty">
                    {{ formatQuantity(shown(row).quantity, shown(row).unit) }}
                    {{ formatUnit(shown(row).unit, shown(row).quantity) }}
                    <template v-if="row.group_name">({{ row.group_name }})</template>
                  </p>
                </div>
              </span>
              <!-- Le matériel ressort dans le texte (pastille + emoji) : c'est au moment de l'étape qu'on
                   doit l'avoir sous la main. -->
              <button
                v-else-if="segment.cookware?.id"
                type="button"
                class="cookware-mention"
                @click.stop="openCookwareById(segment.cookware.id)"
              ><img
                  v-if="findCookware(segment.cookware.id)?.image"
                  :src="findCookware(segment.cookware.id)?.image ?? undefined"
                  class="cookware-pill-image"
                  alt=""
                /><span v-else class="cookware-emoji" aria-hidden="true">{{ cookwareEmoji(segment.cookware.id) }}</span>{{ segment.text }}</button>
              <span v-else-if="segment.cookware" class="cookware-mention"
                ><span class="cookware-emoji" aria-hidden="true">{{ cookwareEmoji() }}</span>{{ segment.text }}</span
              >
              <StepTimerButton
                v-else-if="segment.timerSeconds !== undefined"
                :handle="timerHandles.get(`${currentIndex}-${index}`)?.handle"
                :label="segment.timerLabel"
              />
              <template v-else>{{ segment.text }}</template>
            </template>
          </p>
          </Transition>
        </div>
      </div>

      <button
        type="button"
        class="secondary icon-btn cook-mode-nav next"
        :aria-label="isLastStep ? t('recipes.cookModeFinish') : t('recipes.cookModeNext')"
        @click="goNext"
      >
        <Check v-if="isLastStep" :size="22" />
        <ChevronRight v-else :size="22" />
      </button>
    </div>

    <div v-if="activeTimers.length" class="cook-mode-timer-dock">
      <div
        v-for="entry in activeTimers"
        :key="entry.id"
        class="cook-mode-timer-dock-row"
        :class="{ finished: entry.handle.phase.value === 'finished' }"
      >
        <span class="cook-mode-timer-dock-label">{{ entry.label || t('recipes.cookModeTimerDefaultLabel') }}</span>
        <span class="cook-mode-timer-dock-clock">
          {{ entry.handle.phase.value === 'finished' ? t('timer.finished') : entry.handle.clockLabel.value }}
        </span>
        <button
          v-if="entry.handle.phase.value === 'running'"
          type="button"
          class="cook-mode-timer-dock-control"
          :aria-label="t('timer.pause')"
          @click="entry.handle.pause()"
        >
          <Pause :size="14" />
        </button>
        <button
          v-else-if="entry.handle.phase.value === 'paused'"
          type="button"
          class="cook-mode-timer-dock-control"
          :aria-label="t('timer.resume')"
          @click="entry.handle.start()"
        >
          <Play :size="14" />
        </button>
        <button
          type="button"
          class="cook-mode-timer-dock-control"
          :aria-label="t('timer.reset')"
          @click="entry.handle.reset()"
        >
          <RotateCcw :size="14" />
        </button>
      </div>
    </div>

    <div class="cook-mode-dots">
      <button
        v-for="(step, index) in steps"
        :key="step.id"
        type="button"
        class="cook-mode-dot"
        :class="{ active: index === currentIndex }"
        :aria-label="t('recipes.cookModeGoToStep', { n: index + 1 })"
        :aria-current="index === currentIndex"
        @click="goToStep(index)"
      />
    </div>

    <div v-if="showIngredients" class="cook-mode-backdrop" @click="showIngredients = false"></div>

    <aside class="cook-mode-ingredients" :class="{ open: showIngredients }">
      <h2>{{ t('recipes.ingredients') }}</h2>
      <template v-for="(group, index) in ingredientGroups" :key="index">
        <h3 v-if="group.name" class="ingredient-group-label">{{ group.name }}</h3>
        <ul class="ingredient-list">
          <li v-for="item in group.items" :key="item.id" class="ingredient-row">
            <span class="ingredient-qty">{{ formatQuantity(shown(item).quantity, shown(item).unit) }} {{ formatUnit(shown(item).unit, shown(item).quantity) }}</span>
            <span class="ingredient-name">{{ shown(item).name }}</span>
          </li>
        </ul>
      </template>
      <template v-if="recipe.cookware?.length">
        <h2 class="cookware-title">{{ t('cookware.title') }}</h2>
        <ul class="ingredient-list">
          <li v-for="item in recipe.cookware" :key="item.id" class="ingredient-row">
            <button type="button" class="ingredient-name cookware-open" @click="openCookware = item">
              <img v-if="item.image" :src="item.image" class="cookware-image" alt="" />
              <span v-else class="cookware-emoji" aria-hidden="true">{{ item.emoji || DEFAULT_COOKWARE_EMOJI }}</span>{{ item.name }}
            </button>
          </li>
        </ul>
      </template>
    </aside>

    <CookwareModal v-if="openCookware" :cookware="openCookware" @close="openCookware = null" />
  </div>
</template>

<style scoped>
.cook-mode {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.cook-mode-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  flex-shrink: 0;
}

.cook-mode-header .icon-btn.active {
  background: var(--color-primary-soft-hover);
}

.cook-mode-progress-group {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
}

.cook-mode-progress {
  font-weight: 700;
  color: var(--color-muted);
}

.cook-mode-video-link {
  display: inline-flex;
  align-items: center;
  color: var(--color-muted);
}

.cook-mode-video-link:hover {
  color: var(--color-primary-dark);
}

.cook-mode-body {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 0;
}

.cook-mode-step {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem 3.5rem;
}

.cook-mode-step-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

/* With a step photo, the content column fills the full available height so the photo (flex-grow)
   and the text band (flex-basis anchored to min-height) can split it — see .cook-mode-step-photo
   and .has-image .cook-mode-step-text below. Without a photo, the column keeps its old behaviour:
   sized to its content and centered by .cook-mode-step. */
.cook-mode-step-content.has-image {
  height: 100%;
}

/* The image is the dominant element: it grows to fill whatever height the text band (fixed
   flex-shrink: 0, see below) doesn't need, and shrinks first — down to nothing — rather than ever
   clipping the instruction text. object-fit: contain (not cover) keeps the whole photo visible at
   whatever size it ends up with instead of cropping it. */
.cook-mode-step-photo {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  max-width: 640px;
  display: flex;
  flex-direction: column;
}

.cook-mode-step-photo :deep(.image-with-credit-frame) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  border-radius: 16px;
  background: var(--color-surface-muted);
}

.cook-mode-step-photo :deep(img) {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.cook-mode-step-photo :deep(.image-credit-line) {
  flex-shrink: 0;
}

.cook-mode-step-text {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.5;
  text-align: center;
  max-width: 640px;
  width: 100%;
}

/* The instruction band defaults to ~20% of the step's height (min-height) but never shrinks below
   its own content size (flex-shrink: 0) and never grows to steal space the photo could use
   (flex-grow: 0) — so a long instruction simply grows past 20%, eating into the photo's share
   instead of ever being clipped. */
/* Minuteurs du texte de l'étape à la même taille que les pastilles de matériel (un peu plus
   petits que le texte de l'étape) plutôt qu'à leur petite taille par défaut (StepTimerButton). */
.cook-mode-step-text :deep(.timer-chip) {
  font-size: 0.85em;
  font-weight: 700;
  padding: 0.1rem 0.6rem;
}

.cook-mode-step-text :deep(.timer-chip svg) {
  width: 0.85em;
  height: 0.85em;
}

.cook-mode-step-text :deep(.timer-control) {
  width: 1.3em;
  min-height: 1.3em;
}

.cook-mode-step-content.has-image .cook-mode-step-text {
  flex: 0 0 auto;
  min-height: 20%;
}

.cook-step-next-enter-active,
.cook-step-next-leave-active,
.cook-step-prev-enter-active,
.cook-step-prev-leave-active {
  transition: transform 0.22s ease, opacity 0.22s ease;
}

.cook-step-next-enter-from {
  transform: translateX(24px);
  opacity: 0;
}

.cook-step-next-leave-to {
  transform: translateX(-24px);
  opacity: 0;
}

.cook-step-prev-enter-from {
  transform: translateX(-24px);
  opacity: 0;
}

.cook-step-prev-leave-to {
  transform: translateX(24px);
  opacity: 0;
}

.cook-mode-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.cook-mode-nav.prev {
  left: 0.5rem;
}

.cook-mode-nav.next {
  right: 0.5rem;
}

.cook-mode-timer-dock {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 30vh;
  overflow-y: auto;
  padding: 0 1rem 0.5rem;
}

.cook-mode-timer-dock-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.9rem;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.cook-mode-timer-dock-row.finished {
  background: var(--color-primary);
  color: var(--color-on-primary);
  animation: timer-dock-pulse 1s ease-in-out infinite;
}

.cook-mode-timer-dock-label {
  flex: 1;
  min-width: 0;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cook-mode-timer-dock-clock {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.cook-mode-timer-dock-control {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  min-height: auto;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  flex-shrink: 0;
}

.cook-mode-timer-dock-control:hover {
  background: rgba(0, 0, 0, 0.08);
}

@keyframes timer-dock-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.cook-mode-dots {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem 1rem;
  flex-shrink: 0;
}

.cook-mode-dot {
  width: 0.55rem;
  height: 0.55rem;
  min-height: auto;
  padding: 0;
  border-radius: 999px;
  background: var(--color-surface-muted);
}

.cook-mode-dot.active {
  background: var(--color-primary);
  width: 1.5rem;
}

.ingredient-mention-wrap {
  position: relative;
  display: inline-block;
}

.ingredient-mention {
  background: none;
  padding: 0;
  min-height: auto;
  border-radius: 4px;
  color: var(--color-primary-dark);
  font-weight: 700;
  text-decoration: underline;
  text-decoration-style: dotted;
}

.ingredient-mention:hover {
  background: var(--color-primary-soft);
}

.ingredient-popover {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  min-width: max-content;
  max-width: 220px;
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: 10px;
  box-shadow: var(--shadow-card);
  padding: 0.6rem 0.8rem;
  text-align: center;
  white-space: normal;
  pointer-events: none;
}

.ingredient-popover::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: var(--color-surface);
}

.ingredient-popover-qty {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.cook-mode-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1;
  background: var(--color-overlay);
}

.cook-mode-ingredients {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  max-height: 70vh;
  overflow-y: auto;
  background: var(--color-surface);
  border-radius: 20px 20px 0 0;
  box-shadow: var(--shadow-card);
  padding: 1.25rem;
  padding-bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px));
  transform: translateY(100%);
  transition: transform 0.25s ease;
}

.cook-mode-ingredients.open {
  transform: translateY(0);
}

.cook-mode-ingredients h2 {
  margin-top: 0;
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

.cookware-mention {
  min-height: auto;
  border: none;
  font: inherit;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.1rem 0.6rem 0.1rem 0.5rem;
  font-size: 0.85em;
  border-radius: var(--radius-pill);
  background: var(--color-surface-muted);
  color: var(--color-text);
  font-weight: 700;
  white-space: nowrap;
  /* Avec une photo, l'alignement sur la ligne de base ferait remonter la pastille. */
  vertical-align: middle;
}

.cookware-emoji {
  margin-right: 0.3rem;
}

.cookware-image {
  width: 1.5rem;
  height: 1.5rem;
  margin-right: 0.4rem;
  border-radius: 50%;
  object-fit: cover;
  vertical-align: middle;
}

/* Photo du matériel dans la pastille d'une étape : ronde, à la hauteur du texte. */
.cookware-pill-image {
  width: 1.4em;
  height: 1.4em;
  margin-left: -0.3rem;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.cookware-mention .cookware-emoji {
  margin-right: 0;
  font-size: 0.85em;
}

.cookware-open {
  min-height: auto;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.cookware-title {
  margin-top: 1.5rem;
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
}

@media (max-width: 480px) {
  .cook-mode-step {
    padding: 1rem 3rem;
  }

  .cook-mode-step-text {
    font-size: 1.3rem;
  }
}
</style>
