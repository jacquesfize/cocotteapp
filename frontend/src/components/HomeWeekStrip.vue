<script setup lang="ts">
import { ShoppingCart, TriangleAlert } from '@lucide/vue'
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
      <h2>{{ $t('home.thisWeek') }}</h2>
      <div class="row week-links">
        <RouterLink v-if="deficiencyCount" :to="{ name: 'planning' }" class="week-pill alert-badge">
          <TriangleAlert :size="14" />{{ $t('home.nutritionAlerts', deficiencyCount) }}
        </RouterLink>
        <RouterLink
          v-if="latestList"
          :to="{ name: 'shopping-list-detail', params: { id: latestList.id } }"
          class="week-pill shopping-link"
        >
          <ShoppingCart :size="14" />{{ $t('home.openShoppingList') }}
        </RouterLink>
      </div>
    </div>

    <div v-if="isLoading" class="week-days" aria-hidden="true">
      <div class="skeleton" />
      <div class="skeleton" />
    </div>
    <div v-else class="week-days">
      <div v-for="day in days" :key="day.key" class="week-day">
        <h3>{{ day.label }}</h3>
        <ul v-if="day.entries.length">
          <li v-for="entry in day.entries" :key="entry.id">
            <span class="muted">{{ $t(`mealType.${entry.meal_type}`) }}</span>
            <RouterLink :to="{ name: 'recipe-detail', params: { id: entry.recipe } }">{{ entry.recipe_title }}</RouterLink>
          </li>
        </ul>
        <RouterLink v-else :to="{ name: 'planning' }">
          <button class="secondary" type="button">{{ $t('home.planMeal') }}</button>
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.week-strip {
  /* Floats up over the hero card's bottom edge instead of sitting in its own separate block —
     the hero reserves extra bottom padding (see .hero-card) so this only overlaps empty
     background, never the carousel itself. */
  position: relative;
  z-index: 2;
  margin-top: -2rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 600px) {
  .week-strip {
    margin-top: -1.5rem;
  }
}

.week-header {
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.week-header h2 {
  margin: 0;
}

.week-links {
  gap: 0.6rem;
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

.shopping-link {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.shopping-link:hover {
  background: var(--color-primary-soft-hover);
}

.week-days {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.week-day h3 {
  margin: 0 0 0.5rem;
}

.week-day ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.week-day li {
  display: flex;
  gap: 0.75rem;
  padding: 0.25rem 0;
}

.week-day li .muted {
  min-width: 5.5rem;
}

.skeleton {
  height: 4.5rem;
  border-radius: 14px;
  background: var(--color-surface-muted);
}
</style>
