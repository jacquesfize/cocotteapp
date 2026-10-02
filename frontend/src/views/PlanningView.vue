<script setup lang="ts">
import { Apple, Calendar, ChevronLeft, ChevronRight, Download, ShoppingCart } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BaseModal from '../components/BaseModal.vue'
import CalendarExportMenu from '../components/CalendarExportMenu.vue'
import MealSlot from '../components/MealSlot.vue'
import PageHeader from '../components/PageHeader.vue'
import { fetchLegalInfo } from '../api/auth'
import { downloadWeekPdf, getNutritionSummary, listMealPlanEntries, listSharedWithMe } from '../api/planning'
import { createShoppingList } from '../api/shopping'
import { addDays, startOfWeek, toISODate } from '../utils/dates'
import { downloadBlob } from '../utils/download'
import { NUTRIENT_LABEL_KEYS } from '../utils/nutrition'
import type { MealPlanEntryListParams } from '../types/api'
import type { MealPlanEntry, MealType, NutrientDeficiency, PlanningShareReceived } from '../types/models'

const { t, locale } = useI18n()
const router = useRouter()

// La collation est une bascule d'instance (désactivée par défaut, voir GET /api/auth/legal/) :
// on ne sait si elle doit apparaître qu'une fois fetchLegalInfo() revenu (onMounted ci-dessous).
const ALL_MEAL_TYPES: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack']
const snackEnabled = ref(false)
const MEAL_TYPES = computed<MealType[]>(() =>
  snackEnabled.value ? ALL_MEAL_TYPES : ALL_MEAL_TYPES.filter((mealType) => mealType !== 'snack'),
)

type ViewMode = 'week' | 'month'
const VIEW_MODES: ViewMode[] = ['week', 'month']
const viewMode = ref<ViewMode>('week')
const showNutrition = ref(false)
const weekOffset = ref(0)
const monthOffset = ref(0)
const entries = ref<MealPlanEntry[]>([])
const deficiencies = ref<NutrientDeficiency[]>([])
const carbonFootprint = ref<number | null>(null)
const isLoading = ref(false)
const sharedAgendas = ref<PlanningShareReceived[]>([])
const selectedOwner = ref<number | null>(null)

const isReadOnly = computed(() => {
  if (selectedOwner.value === null) return false
  const share = sharedAgendas.value.find((s) => s.owner === selectedOwner.value)
  return share?.permission === 'read'
})

function agendaLabel(share: PlanningShareReceived) {
  const who = share.owner_username || share.owner_email
  return share.permission === 'read'
    ? t('planning.sharedAgendaReadLabel', { name: who })
    : t('planning.sharedAgendaWriteLabel', { name: who })
}

const weekDays = computed(() => {
  const start = addDays(startOfWeek(new Date()), weekOffset.value * 7)
  return Array.from({ length: 7 }, (_, i) => addDays(start, i))
})

const monthFirstDay = computed(() => {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth() + monthOffset.value, 1)
})

const monthLastDay = computed(() => {
  const first = monthFirstDay.value
  return new Date(first.getFullYear(), first.getMonth() + 1, 0)
})

// Month grid: weeks starting on Monday, null for days outside the month.
const monthWeeks = computed(() => {
  const start = startOfWeek(monthFirstDay.value)
  const weeks: (Date | null)[][] = []
  let cursor = start
  while (cursor <= monthLastDay.value) {
    weeks.push(
      Array.from({ length: 7 }, (_, i) => {
        const d = addDays(cursor, i)
        return d.getMonth() === monthFirstDay.value.getMonth() ? d : null
      }),
    )
    cursor = addDays(cursor, 7)
  }
  return weeks
})

function entriesForDay(date: Date) {
  const iso = toISODate(date)
  return entries.value.filter((e) => e.date === iso)
}

function weekdayLabel(date: Date) {
  return date.toLocaleDateString(locale.value, { weekday: 'short' })
}

function goToWeekOf(date: Date) {
  const currentStart = startOfWeek(new Date())
  const diffDays = Math.round((startOfWeek(date).getTime() - currentStart.getTime()) / 86400000)
  weekOffset.value = Math.round(diffDays / 7)
  viewMode.value = 'week'
}

function shift(amount: number) {
  if (viewMode.value === 'month') monthOffset.value += amount
  else weekOffset.value += amount
}

function goToToday() {
  weekOffset.value = 0
  monthOffset.value = 0
}

const isCurrentPeriod = computed(() =>
  viewMode.value === 'month' ? monthOffset.value === 0 : weekOffset.value === 0,
)

function dayLabel(date: Date) {
  return date.toLocaleDateString(locale.value, { weekday: 'short', day: 'numeric', month: 'short' })
}

function entriesFor(date: Date, mealType: MealType) {
  const iso = toISODate(date)
  return entries.value.filter((e) => e.date === iso && e.meal_type === mealType)
}

function currentParams(): MealPlanEntryListParams {
  const params: MealPlanEntryListParams =
    viewMode.value === 'month'
      ? { date_after: toISODate(monthFirstDay.value), date_before: toISODate(monthLastDay.value) }
      : { date_after: toISODate(weekDays.value[0]), date_before: toISODate(weekDays.value[6]) }
  if (selectedOwner.value !== null) {
    params.owner = selectedOwner.value
  }
  return params
}

async function load() {
  isLoading.value = true
  try {
    const params = currentParams()
    const [entriesData, summary] = await Promise.all([
      listMealPlanEntries(params),
      getNutritionSummary(params),
    ])
    entries.value = entriesData
    deficiencies.value = summary.deficiencies
    carbonFootprint.value = summary.carbon_footprint_kg_co2e
  } finally {
    isLoading.value = false
  }
}

async function loadSharedAgendas() {
  sharedAgendas.value = await listSharedWithMe()
}

async function loadInstanceSettings() {
  try {
    const info = await fetchLegalInfo()
    snackEnabled.value = info.planning_snack_enabled
  } catch {
    // Reste désactivée (valeur par défaut) si l'appel échoue.
  }
}

watch(weekOffset, load)
watch(monthOffset, load)
watch(viewMode, load)
watch(selectedOwner, load)
onMounted(load)
onMounted(loadSharedAgendas)
onMounted(loadInstanceSettings)

async function handleGenerateShoppingList() {
  if (!entries.value.length) return
  const shoppingList = await createShoppingList(entries.value.map((e) => e.id))
  router.push({ name: 'shopping-list-detail', params: { id: shoppingList.id } })
}

async function handleDownloadWeekPdf() {
  const params = currentParams()
  const blob = await downloadWeekPdf(params)
  downloadBlob(blob, `agenda-${params.date_after}-${params.date_before}.pdf`)
}

const rangeLabel = computed(() => {
  if (viewMode.value === 'month') {
    return monthFirstDay.value.toLocaleDateString(locale.value, { month: 'long', year: 'numeric' })
  }
  const fmt = (d: Date) => d.toLocaleDateString(locale.value, { day: 'numeric', month: 'short' })
  return `${fmt(weekDays.value[0])} – ${fmt(weekDays.value[6])}`
})
</script>

<template>
  <div>
    <PageHeader :icon="Calendar" :title="$t('planning.title')" />

    <div v-if="sharedAgendas.length" class="field agenda-switcher">
      <label for="agenda-select">{{ $t('planning.agendaSelectorLabel') }}</label>
      <select id="agenda-select" v-model="selectedOwner">
        <option :value="null">{{ $t('planning.myAgenda') }}</option>
        <option v-for="share in sharedAgendas" :key="share.id" :value="share.owner">
          {{ agendaLabel(share) }}
        </option>
      </select>
    </div>

    <div class="view-switcher" role="group" :aria-label="$t('planning.viewLabel')">
      <button
        v-for="mode in VIEW_MODES"
        :key="mode"
        type="button"
        :class="['view-btn', { secondary: viewMode !== mode }]"
        :data-view="mode"
        :aria-pressed="viewMode === mode"
        @click="viewMode = mode"
      >
        {{ $t(`planning.view.${mode}`) }}
      </button>
    </div>

    <div class="week-nav">
      <button
        class="secondary icon-btn"
        type="button"
        :aria-label="viewMode === 'month' ? $t('planning.previousMonth') : $t('planning.previousWeek')"
        @click="shift(-1)"
      >
        <ChevronLeft :size="18" />
      </button>
      <div class="week-range">
        <strong>{{ rangeLabel }}</strong>
        <button v-if="!isCurrentPeriod" class="today-btn secondary" type="button" @click="goToToday">
          {{ $t('planning.today') }}
        </button>
      </div>
      <button
        class="secondary icon-btn"
        type="button"
        :aria-label="viewMode === 'month' ? $t('planning.nextMonth') : $t('planning.nextWeek')"
        @click="shift(1)"
      >
        <ChevronRight :size="18" />
      </button>
    </div>

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>

    <div v-if="viewMode === 'week'" class="agenda-week">
      <div class="agenda-corner" />
      <div v-for="date in weekDays" :key="toISODate(date)" class="agenda-day-head">
        {{ dayLabel(date) }}
      </div>
      <template v-for="mealType in MEAL_TYPES" :key="mealType">
        <div class="agenda-row-head">{{ $t(`mealType.${mealType}`) }}</div>
        <div
          v-for="date in weekDays"
          :key="toISODate(date)"
          class="agenda-cell"
          :data-meal-type="mealType"
          :data-date="toISODate(date)"
        >
          <MealSlot
            :date="toISODate(date)"
            :meal-type="mealType"
            :entries="entriesFor(date, mealType)"
            :owner="selectedOwner ?? undefined"
            :read-only="isReadOnly"
            @changed="load"
          />
        </div>
      </template>
    </div>

    <div v-else-if="viewMode === 'month'" class="agenda-month">
      <div v-for="date in weekDays" :key="'h' + toISODate(date)" class="agenda-day-head">
        {{ weekdayLabel(date) }}
      </div>
      <template v-for="(week, wi) in monthWeeks" :key="wi">
        <div
          v-for="(date, di) in week"
          :key="wi + '-' + di"
          :class="['month-cell', { empty: !date }]"
          :data-date="date ? toISODate(date) : undefined"
        >
          <template v-if="date">
            <button type="button" class="month-day-num" @click="goToWeekOf(date)">
              {{ date.getDate() }}
            </button>
            <ul class="month-entries">
              <li v-for="entry in entriesForDay(date)" :key="entry.id">
                <RouterLink :to="{ name: 'recipe-detail', params: { id: entry.recipe } }">
                  {{ entry.recipe_title }}
                </RouterLink>
              </li>
            </ul>
          </template>
        </div>
      </template>
    </div>


    <BaseModal v-if="showNutrition" :title="$t('planning.nutritionIntake')" @close="showNutrition = false">
      <div v-if="deficiencies.length" class="deficiency-banner">
        <strong>{{ $t('nutrition.weeklyAlertTitle') }}</strong>
        <ul>
          <li v-for="d in deficiencies" :key="d.nutrient">
            {{ $t(NUTRIENT_LABEL_KEYS[d.nutrient] || d.nutrient) }} : {{ d.amount.toFixed(1) }} /
            {{ d.minimum.toFixed(1) }} {{ d.unit }}
          </li>
        </ul>
      </div>
      <p v-if="carbonFootprint !== null" class="muted carbon-summary">
        {{ $t('nutrition.carbonWeekly') }} : <strong>{{ carbonFootprint.toFixed(1) }} kg CO2e</strong>
      </p>
    </BaseModal>

    <div class="week-footer">
      <button class="secondary nutrition-btn" type="button" @click="showNutrition = true">
        <Apple :size="16" />{{ $t('planning.nutritionIntake') }}
      </button>
      <button class="secondary" @click="handleDownloadWeekPdf">
        <Download :size="16" />{{ $t('planning.downloadWeekPdf') }}
      </button>
      <CalendarExportMenu :params="currentParams()" />
      <button :disabled="!entries.length" @click="handleGenerateShoppingList">
        <ShoppingCart :size="16" />{{ $t('planning.generateShoppingList', { n: entries.length }) }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.agenda-switcher {
  max-width: 320px;
  margin-bottom: 1rem;
}

.week-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.week-range {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.today-btn {
  min-height: auto;
  padding: 0.25rem 0.7rem;
  font-size: 0.8rem;
}

.deficiency-banner ul {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
}

.carbon-summary {
  margin: 1rem 0 0;
}

.week-footer {
  margin-top: 1.25rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.view-switcher {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.view-btn {
  min-height: auto;
  padding: 0.3rem 0.8rem;
  font-size: 0.85rem;
}

.agenda-week {
  display: grid;
  grid-template-columns: 5.5rem repeat(7, minmax(8rem, 1fr));
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow-x: auto;
  background: var(--color-surface);
}

.agenda-month {
  display: grid;
  grid-template-columns: repeat(7, minmax(5.5rem, 1fr));
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow-x: auto;
  background: var(--color-surface);
}

.agenda-day-head {
  padding: 0.5rem;
  text-align: center;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: capitalize;
  border-bottom: 1px solid var(--color-border);
  border-left: 1px solid var(--color-border);
}

.agenda-corner {
  border-bottom: 1px solid var(--color-border);
}

.agenda-row-head {
  padding: 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-muted);
  border-bottom: 1px solid var(--color-border);
}

.agenda-cell {
  padding: 0.4rem;
  border-left: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.agenda-cell :deep(.meal-label) {
  display: none;
}

.month-cell {
  min-height: 6rem;
  padding: 0.3rem;
  border-left: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.month-cell.empty {
  background: var(--color-border);
  opacity: 0.25;
}

.month-day-num {
  background: transparent;
  border: none;
  min-height: auto;
  padding: 0 0.3rem;
  font-weight: 700;
  color: inherit;
}

.month-entries {
  list-style: none;
  margin: 0.2rem 0 0;
  padding: 0;
  font-size: 0.75rem;
}

.month-entries a {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
