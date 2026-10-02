<script setup lang="ts">
import { Calendar, ShoppingCart, TriangleAlert } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getNutritionSummary, listMealPlanEntries } from '../api/planning'
import { listShoppingLists } from '../api/shopping'
import type { MealPlanEntry, MealType, ShoppingList } from '../types/models'

const { t } = useI18n()

const MEAL_ORDER: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack']

function isoDate(offsetDays: number) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const today = isoDate(0)
const tomorrow = isoDate(1)

const entries = ref<MealPlanEntry[]>([])
const latestList = ref<ShoppingList | null>(null)
const deficiencyCount = ref(0)
const isLoading = ref(true)

onMounted(async () => {
  const [entriesRes, listsRes, nutritionRes] = await Promise.allSettled([
    listMealPlanEntries({ date_after: today, date_before: tomorrow }),
    listShoppingLists(),
    getNutritionSummary({ date_after: today, date_before: isoDate(6) }),
  ])
  if (entriesRes.status === 'fulfilled') entries.value = entriesRes.value
  if (listsRes.status === 'fulfilled') latestList.value = listsRes.value.results[0] ?? null
  if (nutritionRes.status === 'fulfilled') deficiencyCount.value = nutritionRes.value.deficiencies.length
  isLoading.value = false
})

const listOwnedCount = computed(() => latestList.value?.items.filter((item) => item.is_owned).length ?? 0)
const listTotalCount = computed(() => latestList.value?.items.length ?? 0)
const listProgressPercent = computed(() => (listTotalCount.value ? Math.round((listOwnedCount.value / listTotalCount.value) * 100) : 0))

const days = computed(() =>
  [
    { key: today, label: t('home.today') },
    { key: tomorrow, label: t('home.tomorrow') },
  ].map((day) => ({
    ...day,
    entries: entries.value
      .filter((entry) => entry.date === day.key)
      .sort((a, b) => MEAL_ORDER.indexOf(a.meal_type) - MEAL_ORDER.indexOf(b.meal_type)),
  })),
)
</script>

<template>
  <section class="card week-strip">
    <div class="row week-header">
      <h2><Calendar :size="20" class="week-heading-icon" aria-hidden="true" />{{ $t('home.thisWeek') }}</h2>
      <RouterLink v-if="deficiencyCount" :to="{ name: 'planning' }" class="week-pill alert-badge">
        <TriangleAlert :size="14" />{{ $t('home.nutritionAlerts', deficiencyCount) }}
      </RouterLink>
    </div>

    <div v-if="isLoading" class="week-layout" aria-hidden="true">
      <div class="skeleton skeleton-action" />
      <div class="skeleton" />
      <div class="skeleton" />
    </div>
    <div v-else class="week-layout">
      <RouterLink
        v-if="latestList"
        :to="{ name: 'shopping-list-detail', params: { id: latestList.id } }"
        class="week-action"
      >
        <ShoppingCart :size="26" />
        <span class="week-action-title">{{ $t('home.openShoppingList') }}</span>
        <template v-if="listTotalCount">
          <span class="week-action-progress">{{ $t('shopping.progressCount', { owned: listOwnedCount, total: listTotalCount }) }}</span>
          <div class="week-action-track">
            <div class="week-action-fill" :style="{ width: `${listProgressPercent}%` }" />
          </div>
        </template>
      </RouterLink>

      <div v-for="day in days" :key="day.key" class="week-day">
        <h3>{{ day.label }}</h3>
        <div v-if="day.entries.length" class="week-tiles">
          <RouterLink
            v-for="entry in day.entries"
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
        </div>
        <RouterLink v-else :to="{ name: 'planning' }" class="week-day-empty">
          {{ $t('home.planMeal') }}
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.week-strip {
  /* Floats up over the hero card's bottom edge instead of sitting in its own separate block —
     the hero reserves extra bottom padding (see .hero-card) so this only overlaps empty
     background, never the carousel itself. Less than the hero's own reserved padding, so a
     visible gap remains above this card instead of the two butting up against each other. */
  position: relative;
  z-index: 2;
  margin-top: -1.25rem;
  margin-bottom: 1.5rem;
  padding-top: 1.75rem;
}

@media (max-width: 600px) {
  .week-strip {
    margin-top: -0.75rem;
  }
}

.week-header {
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
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
  border-radius: 999px;
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

/* A quarter for the shopping-list action, the rest split evenly between Today and Tomorrow.
   align-items: start keeps the action column at its own height instead of stretching to match
   whichever day column has the most meals planned. */
.week-layout {
  display: grid;
  grid-template-columns: 25% 1fr 1fr;
  align-items: start;
  gap: 1.25rem;
}

@media (max-width: 760px) {
  .week-layout {
    grid-template-columns: 1fr;
  }
}

.week-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  align-self: center;
  gap: 0.5rem;
  width: 100%;
  min-height: 7rem;
  padding: 1.25rem 1rem;
  border-radius: 16px;
  background: var(--color-surface);
  border: 1.5px solid var(--color-primary-soft-hover);
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

.week-action-track {
  width: 100%;
  height: 0.35rem;
  border-radius: 999px;
  background: var(--color-primary-soft);
  overflow: hidden;
}

.week-action-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 999px;
  transition: width 0.2s ease;
}

.week-day h3 {
  margin: 0 0 0.6rem;
}

.week-tiles {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.week-day-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 4.5rem;
  border-radius: 12px;
  border: 1.5px dashed var(--color-border);
  background: var(--color-surface-muted);
  color: var(--color-primary-dark);
  text-decoration: none;
  font-weight: 700;
  font-size: 0.9rem;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.week-day-empty:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.week-tile {
  position: relative;
  display: block;
  height: 4.5rem;
  border-radius: 12px;
  overflow: hidden;
  text-decoration: none;
  color: #fff;
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

.skeleton {
  height: 10rem;
  border-radius: 14px;
  background: var(--color-surface-muted);
}

.skeleton-action {
  height: 7rem;
}
</style>
