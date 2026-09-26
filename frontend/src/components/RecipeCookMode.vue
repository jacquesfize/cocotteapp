<script setup lang="ts">
import { ChevronLeft, ChevronRight, CirclePlay, ListChecks, Pause, Play, RotateCcw, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseModal from './BaseModal.vue'
import StepTimerButton from './StepTimerButton.vue'
import { useStepTimer, type StepTimerHandle } from '../composables/useStepTimer'
import { formatQuantity, formatUnit } from '../utils/format'
import { buildStepSegments, groupIngredients } from '../utils/recipeSteps'
import type { Recipe, RecipeIngredient } from '../types/models'

const props = defineProps<{
  recipe: Recipe
}>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()

const currentIndex = ref(0)
const direction = ref<'next' | 'prev'>('next')
const showIngredients = ref(false)
const activeIngredient = ref<RecipeIngredient | null>(null)

const steps = computed(() => props.recipe.steps)
const currentStep = computed(() => steps.value[currentIndex.value])

// Calculé une seule fois, hors de tout `computed` : les minuteurs doivent survivre à la
// navigation entre étapes (voir timerHandles ci-dessous), donc on ne peut pas se permettre de
// les recréer si cette liste était réévaluée en réaction à un changement réactif quelconque.
const allStepsSegments = props.recipe.steps.map((step) =>
  buildStepSegments(step.instruction, props.recipe.ingredients),
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

function goNext() {
  if (!isLastStep.value) {
    direction.value = 'next'
    currentIndex.value += 1
  }
}

function goToStep(index: number) {
  direction.value = index > currentIndex.value ? 'next' : 'prev'
  currentIndex.value = index
}

function openIngredient(ingredientId: number) {
  activeIngredient.value = props.recipe.ingredients.find((item) => item.ingredient.id === ingredientId) ?? null
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
  if (event.key === 'Escape') {
    if (activeIngredient.value) activeIngredient.value = null
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
})
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleKeydown)
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
        <Transition :name="direction === 'next' ? 'cook-step-next' : 'cook-step-prev'" mode="out-in">
          <p v-if="currentStep" :key="currentStep.id" class="cook-mode-step-text">
            <template v-for="(segment, index) in currentSegments" :key="index">
              <button
                v-if="segment.ingredientId"
                type="button"
                class="ingredient-mention"
                @click="openIngredient(segment.ingredientId)"
              >{{ segment.text }}</button>
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

      <button
        v-if="!isLastStep"
        type="button"
        class="secondary icon-btn cook-mode-nav next"
        :aria-label="t('recipes.cookModeNext')"
        @click="goNext"
      >
        <ChevronRight :size="22" />
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
            <span class="ingredient-qty">{{ formatQuantity(item.quantity, item.unit) }} {{ formatUnit(item.unit, item.quantity) }}</span>
            <span class="ingredient-name">{{ item.ingredient.name }}</span>
          </li>
        </ul>
      </template>
    </aside>

    <BaseModal v-if="activeIngredient" :title="activeIngredient.ingredient.name" @close="activeIngredient = null">
      <p class="cook-mode-ingredient-qty">
        {{ formatQuantity(activeIngredient.quantity, activeIngredient.unit) }}
        {{ formatUnit(activeIngredient.unit, activeIngredient.quantity) }}
      </p>
    </BaseModal>
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

.cook-mode-step-text {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.5;
  text-align: center;
  max-width: 640px;
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

.cook-mode-ingredient-qty {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-primary-dark);
  margin: 0;
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
