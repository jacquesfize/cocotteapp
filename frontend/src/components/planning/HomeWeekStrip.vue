<script setup lang="ts">
import { Calendar, Link2, Pencil, Plus, ShoppingCart, TriangleAlert } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useClickOutside } from '../../composables/useClickOutside'
import AddMealModal from './AddMealModal.vue'
import ProgressBar from '../shared/ProgressBar.vue'
import { fetchLegalInfo } from '../../api/auth'
import { getNutritionSummary, listMealPlanEntries } from '../../api/planning'
import { listShoppingLists } from '../../api/shopping'
import { addDays, toISODate } from '../../utils/dates'
import { shoppingListProgress } from '../../utils/shoppingListProgress'
import type { MealPlanEntry, MealType, ShoppingList } from '../../types/models'

const emit = defineEmits<{ (e: 'open-import'): void }>()

const { t } = useI18n()

const ALL_MEAL_TYPES: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack']

function isoDate(offsetDays: number) {
  return toISODate(addDays(new Date(), offsetDays))
}

const today = isoDate(0)
const tomorrow = isoDate(1)

const entries = ref<MealPlanEntry[]>([])
const latestList = ref<ShoppingList | null>(null)
const deficiencyCount = ref(0)
const snackEnabled = ref(false)
const isLoading = ref(true)

async function loadEntries() {
  try {
    entries.value = await listMealPlanEntries({ date_after: today, date_before: tomorrow })
  } catch {
    // Keep showing what we had; the next full load will catch up.
  }
}

onMounted(async () => {
  const [entriesRes, listsRes, nutritionRes, legalRes] = await Promise.allSettled([
    listMealPlanEntries({ date_after: today, date_before: tomorrow }),
    listShoppingLists(),
    getNutritionSummary({ date_after: today, date_before: isoDate(6) }),
    fetchLegalInfo(),
  ])
  if (entriesRes.status === 'fulfilled') entries.value = entriesRes.value
  if (listsRes.status === 'fulfilled') latestList.value = listsRes.value.results[0] ?? null
  if (nutritionRes.status === 'fulfilled') deficiencyCount.value = nutritionRes.value.deficiencies.length
  if (legalRes.status === 'fulfilled') snackEnabled.value = legalRes.value.planning_snack_enabled
  isLoading.value = false
})

// Empty slots open the planner's recipe picker for that exact day + meal, in place, instead of
// navigating to the planner.
const addingSlot = ref<{ date: string; mealType: MealType } | null>(null)

function handleSlotAdded() {
  addingSlot.value = null
  loadEntries()
}

defineExpose({ reload: loadEntries })

const listProgress = computed(() => shoppingListProgress(latestList.value))

const mealTypes = computed<MealType[]>(() =>
  snackEnabled.value ? ALL_MEAL_TYPES : ALL_MEAL_TYPES.filter((mealType) => mealType !== 'snack'),
)

const showCreateMenu = ref(false)
const createMenuEl = ref<HTMLElement | null>(null)

function closeCreateMenu() {
  showCreateMenu.value = false
}

function handleImportClick() {
  closeCreateMenu()
  emit('open-import')
}

useClickOutside(createMenuEl, closeCreateMenu)

const days = computed(() =>
  [
    { key: today, label: t('home.today') },
    { key: tomorrow, label: t('home.tomorrow') },
  ].map((day) => {
    const dayEntries = entries.value.filter((entry) => entry.date === day.key)
    const entriesByType: Partial<Record<MealType, MealPlanEntry[]>> = {}
    for (const mealType of mealTypes.value) {
      entriesByType[mealType] = dayEntries.filter((entry) => entry.meal_type === mealType)
    }
    return { ...day, entriesByType }
  }),
)
</script>

<template>
  <div class="week-overview">
    <div class="week-action-col">
      <div ref="createMenuEl" class="create-menu week-create-menu" :aria-label="$t('home.quickActions')">
        <button
          class="create-toggle"
          type="button"
          :aria-expanded="showCreateMenu"
          aria-controls="home-create-panel"
          @click="showCreateMenu = !showCreateMenu"
        >
          <Plus :size="26" />
          <span class="create-toggle-label">{{ $t('recipes.newRecipe') }}</span>
        </button>
        <div id="home-create-panel" class="create-panel" :class="{ 'is-open': showCreateMenu }">
          <RouterLink :to="{ name: 'recipe-new' }" class="create-link" @click="closeCreateMenu">
            <Pencil :size="16" /><span>{{ $t('recipes.createManually') }}</span>
          </RouterLink>
          <button type="button" class="create-link" @click="handleImportClick">
            <Link2 :size="16" /><span>{{ $t('recipes.importFromUrl') }}</span>
          </button>
        </div>
      </div>

      <RouterLink
        v-if="!isLoading && latestList"
        :to="{ name: 'shopping-list-detail', params: { id: latestList.id } }"
        class="week-action"
      >
        <ShoppingCart :size="26" />
        <span class="week-action-title">{{ $t('home.openShoppingList') }}</span>
        <template v-if="listProgress.total">
          <span class="week-action-progress">{{ $t('shopping.progressCount', { owned: listProgress.owned, total: listProgress.total }) }}</span>
          <ProgressBar :percent="listProgress.percent" height="0.35rem" track-color="var(--color-primary-soft)" />
        </template>
      </RouterLink>
      <div v-else-if="isLoading" class="skeleton skeleton-action" aria-hidden="true" />
    </div>

    <section class="card week-strip">
      <div class="row week-header">
        <h2><Calendar :size="20" class="week-heading-icon" aria-hidden="true" />{{ $t('home.thisWeek') }}</h2>
        <RouterLink v-if="deficiencyCount" :to="{ name: 'planning' }" class="week-pill alert-badge">
          <TriangleAlert :size="14" />{{ $t('home.nutritionAlerts', deficiencyCount) }}
        </RouterLink>
      </div>

      <div v-if="isLoading" class="week-days" aria-hidden="true">
        <div class="skeleton" />
        <div class="skeleton" />
      </div>
      <div v-else class="week-days">
        <div v-for="day in days" :key="day.key" class="week-day">
          <h3>{{ day.label }}</h3>
          <div class="week-tiles">
            <template v-for="mealType in mealTypes" :key="mealType">
              <RouterLink
                v-for="entry in day.entriesByType[mealType]"
                :key="entry.id"
                :to="{ name: 'recipe-detail', params: { id: entry.recipe } }"
                class="week-tile"
              >
                <img v-if="entry.recipe_image || entry.recipe_image_url" :src="entry.recipe_image || entry.recipe_image_url" alt="" />
                <div v-else class="week-tile-placeholder" aria-hidden="true">🍲</div>
                <div class="week-tile-scrim" />
                <span class="week-tile-meal">{{ $t(`mealType.${entry.meal_type}`) }}</span>
                <span class="week-tile-title">{{ entry.recipe_title }}</span>
              </RouterLink>
              <button
                v-if="!day.entriesByType[mealType]?.length"
                type="button"
                class="week-tile week-slot-empty"
                :aria-label="`${$t('planning.addEntry')} — ${day.label}, ${$t(`mealType.${mealType}`)}`"
                @click="addingSlot = { date: day.key, mealType }"
              >
                <Plus :size="16" />
                {{ $t(`mealType.${mealType}`) }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </section>

    <AddMealModal
      v-if="addingSlot"
      :date="addingSlot.date"
      :meal-type="addingSlot.mealType"
      @close="addingSlot = null"
      @added="handleSlotAdded"
    />
  </div>
</template>

<style scoped>
.week-overview {
  /* Floats up over the hero card's bottom edge instead of sitting in its own separate block —
     the hero reserves extra bottom padding (see .hero-card) so this only overlaps empty
     background, never the carousel itself. Less than the hero's own reserved padding, so a
     visible gap remains above this card instead of the two butting up against each other. */
  position: relative;
  z-index: 2;
  display: flex;
  align-items: stretch;
  gap: 1.5rem;
  margin-top: -1.25rem;
  margin-bottom: 1.5rem;
  padding-top: 1.75rem;
}

@media (max-width: 600px) {
  .week-overview {
    margin-top: -0.75rem;
  }
}

@media (max-width: 760px) {
  .week-overview {
    flex-direction: column;
  }
}

.week-strip {
  flex: 1;
  min-width: 0;
}

.week-header {
  position: relative;
  justify-content: center;
  align-items: baseline;
  margin-bottom: 1rem;
}

.week-header .week-pill {
  position: absolute;
  right: 0;
}

.week-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.week-heading-icon {
  color: var(--color-primary);
}

.week-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  border-radius: 0;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  transition: background-color 0.15s ease;
}

.alert-badge {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.alert-badge:hover {
  background: var(--color-danger-soft-hover);
}

/* A dedicated column of its own, a sibling of .week-strip rather than nested inside it —
   stretches to the same height via .week-overview's align-items: stretch, then splits that
   height between the "New recipe" action and the shopping-list card below it. */
.week-action-col {
  flex: 0 0 13rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

@media (min-width: 761px) {
  .week-create-menu,
  .week-action,
  .skeleton-action {
    flex: 1;
  }
}

@media (max-width: 760px) {
  .week-action-col {
    flex-basis: auto;
  }
}

.week-create-menu {
  position: relative;
  display: flex;
}

.week-create-menu .create-toggle {
  flex: 1;
}

/* Matches .week-action's card look (surface, border, icon over label) instead of the default
   pill button, so the two stacked actions in .week-action-col read as one family — the dropdown
   affordance is just the chevron next to the label. */
.create-toggle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1.25rem 1rem;
  border-radius: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  color: var(--color-primary-dark);
  text-align: center;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.create-toggle:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.create-toggle-label {
  font-weight: 700;
  font-size: 0.95rem;
}

.create-panel {
  display: none;
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  min-width: 220px;
  background: var(--color-surface);
  border-radius: 0;
  box-shadow: var(--shadow-card);
  padding: 0.6rem;
  flex-direction: column;
  gap: 0.2rem;
  z-index: 20;
}

.create-panel.is-open {
  display: flex;
}

.create-link {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.6rem;
  margin: 0;
  padding: 0.55rem 0.6rem;
  border-radius: 0;
  color: var(--color-text);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  background: none;
  border: none;
  min-height: auto;
}

.create-link:hover {
  background: var(--color-surface-muted);
}

.week-days {
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: start;
  gap: 1.25rem;
}

@media (max-width: 760px) {
  .week-days {
    grid-template-columns: 1fr;
  }
}

.week-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1.25rem 1rem;
  border-radius: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  color: var(--color-primary-dark);
  text-decoration: none;
  text-align: center;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.week-action:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.week-action-title {
  font-weight: 700;
  font-size: 0.95rem;
}

.week-action-progress {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-muted);
}

.week-day h3 {
  margin: 0 0 0.6rem;
}

.week-tiles {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.week-tile {
  position: relative;
  display: block;
  height: 4.5rem;
  border-radius: 0;
  overflow: hidden;
  text-decoration: none;
  color: var(--color-on-primary);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.week-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(36, 31, 29, 0.08), 0 8px 16px rgba(36, 31, 29, 0.1);
}

.week-tile img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.week-tile-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.week-tile-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0) 65%);
}

.week-tile-meal {
  position: absolute;
  top: 0.4rem;
  left: 0.65rem;
  font-size: 0.68rem;
  font-weight: 600;
  opacity: 0.85;
}

.week-tile-title {
  position: absolute;
  left: 0.65rem;
  right: 0.65rem;
  bottom: 0.4rem;
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Same box as .week-tile (same height/radius so filled and empty slots line up), just the
   visual treatment flipped to a muted "add" affordance instead of a photo. */
.week-slot-empty {
  width: 100%;
  min-height: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: var(--color-surface-muted);
  border: 1.5px dashed var(--color-border);
  color: var(--color-primary-dark);
  font-weight: 600;
  font-size: 0.82rem;
}

.week-slot-empty:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.skeleton {
  height: 10rem;
  border-radius: 0;
  background: var(--color-surface-muted);
}

.skeleton-action {
  height: 7rem;
}
</style>
