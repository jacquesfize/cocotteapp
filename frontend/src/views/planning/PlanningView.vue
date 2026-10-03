<script setup lang="ts">
import { Apple, Calendar, ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BaseModal from '../../components/shared/BaseModal.vue'
import CalendarExportMenu from '../../components/planning/CalendarExportMenu.vue'
import MealSlot from '../../components/planning/MealSlot.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import { fetchLegalInfo } from '../../api/auth'
import {
  createMealPlanEntry,
  downloadWeekPdf,
  getNutritionSummary,
  listMealPlanEntries,
  listSharedWithMe,
  updateMealPlanEntry,
} from '../../api/planning'
import { createShoppingList } from '../../api/shopping'
import { addDays, startOfWeek, toISODate } from '../../utils/dates'
import { downloadBlob } from '../../utils/download'
import { NUTRIENT_LABEL_KEYS } from '../../utils/nutrition'
import type { MealPlanEntryListParams } from '../../types/api'
import type { MealPlanEntry, MealType, NutrientDeficiency, PlanningShareReceived } from '../../types/models'

const { t, locale } = useI18n()
const router = useRouter()

// La collation et les alertes nutritionnelles sont des bascules d'instance (désactivées par
// défaut, voir GET /api/auth/legal/) : on ne sait si elles doivent apparaître qu'une fois
// fetchLegalInfo() revenu (onMounted ci-dessous).
const ALL_MEAL_TYPES: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack']
const snackEnabled = ref(false)
const nutritionAlertsEnabled = ref(false)
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
const activeDayIndex = ref((new Date().getDay() + 6) % 7)
const MEAL_ICONS: Record<MealType, string> = { breakfast: '☀️', lunch: '🥗', dinner: '🌙', snack: '🍎' }
const MONTH_MAX_VISIBLE = 3

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

function isToday(date: Date) {
  return toISODate(date) === toISODate(new Date())
}

function goToWeekOf(date: Date) {
  const currentStart = startOfWeek(new Date())
  const diffDays = Math.round((startOfWeek(date).getTime() - currentStart.getTime()) / 86400000)
  weekOffset.value = Math.round(diffDays / 7)
  activeDayIndex.value = (date.getDay() + 6) % 7
  viewMode.value = 'week'
}

function shift(amount: number) {
  if (viewMode.value === 'month') monthOffset.value += amount
  else weekOffset.value += amount
}

function goToToday() {
  weekOffset.value = 0
  monthOffset.value = 0
  activeDayIndex.value = (new Date().getDay() + 6) % 7
}

const isCurrentPeriod = computed(() =>
  viewMode.value === 'month' ? monthOffset.value === 0 : weekOffset.value === 0,
)

function dayLongLabel(date: Date) {
  return date.toLocaleDateString(locale.value, { weekday: 'long', day: 'numeric', month: 'long' })
}

function entriesFor(date: Date, mealType: MealType) {
  const iso = toISODate(date)
  return entries.value.filter((e) => e.date === iso && e.meal_type === mealType)
}

function cellKey(dateIso: string, mealType: MealType) {
  return `${dateIso}|${mealType}`
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
    nutritionAlertsEnabled.value = info.nutrition_alerts_enabled
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

const periodText = computed(() =>
  viewMode.value === 'month' ? t('planning.periodMonth') : t('planning.periodWeek'),
)
const plannedCountLabel = computed(() => {
  const n = entries.value.length
  return n === 1 ? t('planning.plannedCountSingular') : t('planning.plannedCountPlural', { n })
})

/* ---------- Glisser-déposer entre créneaux (déplacer, Alt = copier) ---------- */
const dragEntry = ref<MealPlanEntry | null>(null)
const overKey = ref<string | null>(null)

function handleDragStart(entry: MealPlanEntry) {
  dragEntry.value = entry
}
function handleDragEnd() {
  dragEntry.value = null
  overKey.value = null
}
function handleDragOver(key: string) {
  if (dragEntry.value) overKey.value = key
}
function handleDragLeave(key: string) {
  if (overKey.value === key) overKey.value = null
}
async function handleDrop(dateIso: string, mealType: MealType, altKey: boolean) {
  const entry = dragEntry.value
  overKey.value = null
  dragEntry.value = null
  if (!entry || isReadOnly.value) return
  if (altKey) {
    await createMealPlanEntry(
      { recipe: entry.recipe, date: dateIso, meal_type: mealType, servings: entry.servings },
      selectedOwner.value ?? undefined,
    )
    load()
    return
  }
  if (entry.date === dateIso && entry.meal_type === mealType) return
  await updateMealPlanEntry(entry.id, { date: dateIso, meal_type: mealType }, selectedOwner.value ?? undefined)
  load()
}
function handleMonthDrop(dateIso: string, altKey: boolean) {
  if (!dragEntry.value) return
  handleDrop(dateIso, dragEntry.value.meal_type, altKey)
}

/* ---------- Suppression avec annulation ---------- */
const toast = ref<{ entry: MealPlanEntry } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | undefined

function handleEntryRemoved(entry: MealPlanEntry) {
  toast.value = { entry }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = null), 6000)
}
async function undoRemove() {
  if (!toast.value) return
  const { entry } = toast.value
  toast.value = null
  clearTimeout(toastTimer)
  await createMealPlanEntry(
    { recipe: entry.recipe, date: entry.date, meal_type: entry.meal_type, servings: entry.servings },
    selectedOwner.value ?? undefined,
  )
  load()
}
onBeforeUnmount(() => clearTimeout(toastTimer))
</script>

<template>
  <div class="planner">
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

    <div class="seg" role="group" :aria-label="$t('planning.viewLabel')">
      <button
        v-for="mode in VIEW_MODES"
        :key="mode"
        type="button"
        class="view-btn"
        :class="{ on: viewMode === mode }"
        :data-view="mode"
        :aria-pressed="viewMode === mode"
        @click="viewMode = mode"
      >
        {{ $t(`planning.view.${mode}`) }}
      </button>
    </div>

    <div class="week-nav">
      <button
        class="round"
        type="button"
        :aria-label="viewMode === 'month' ? $t('planning.previousMonth') : $t('planning.previousWeek')"
        @click="shift(-1)"
      >
        <ChevronLeft :size="18" :stroke-width="2.2" />
      </button>
      <div class="week-range">
        <h2>{{ rangeLabel }}</h2>
        <button v-if="!isCurrentPeriod" class="today-btn" type="button" @click="goToToday">
          {{ $t('planning.today') }}
        </button>
      </div>
      <button
        class="round"
        type="button"
        :aria-label="viewMode === 'month' ? $t('planning.nextMonth') : $t('planning.nextWeek')"
        @click="shift(1)"
      >
        <ChevronRight :size="18" :stroke-width="2.2" />
      </button>
    </div>

    <AsyncState v-if="isLoading" loading :loading-text="$t('common.loading')" />

    <template v-if="viewMode === 'week'">
      <!-- La grille n'affiche que le jour choisi ici, quelle que soit la largeur d'écran. -->
      <div class="day-chips">
        <button
          v-for="(date, i) in weekDays"
          :key="'chip' + toISODate(date)"
          type="button"
          class="day-chip"
          :class="{ on: i === activeDayIndex, today: isToday(date), over: overKey === toISODate(date) }"
          :aria-pressed="i === activeDayIndex"
          :aria-label="dayLongLabel(date)"
          @click="activeDayIndex = i"
          @dragover.prevent="handleDragOver(toISODate(date))"
          @dragleave="handleDragLeave(toISODate(date))"
          @drop.prevent="handleMonthDrop(toISODate(date), $event.altKey)"
        >
          <span>{{ weekdayLabel(date) }}</span>
          <strong>{{ date.getDate() }}</strong>
        </button>
      </div>

      <div class="agenda-week">
        <template v-for="mealType in MEAL_TYPES" :key="mealType">
          <div class="agenda-row-head" :title="$t(`mealType.${mealType}`)">
            <span class="slot-icon" aria-hidden="true">{{ MEAL_ICONS[mealType] }}</span>
            <span>{{ $t(`planning.mealShort.${mealType}`) }}</span>
          </div>
          <div
            v-for="(date, i) in weekDays"
            :key="toISODate(date)"
            class="agenda-cell"
            :class="{ 'is-today': isToday(date), 'is-active-day': i === activeDayIndex }"
            :data-meal-type="mealType"
            :data-date="toISODate(date)"
          >
            <MealSlot
              :date="toISODate(date)"
              :meal-type="mealType"
              :entries="entriesFor(date, mealType)"
              :owner="selectedOwner ?? undefined"
              :read-only="isReadOnly"
              :over="overKey === cellKey(toISODate(date), mealType)"
              @changed="load"
              @removed="handleEntryRemoved"
              @drag-start="handleDragStart"
              @drag-end="handleDragEnd"
              @drag-over="handleDragOver(cellKey(toISODate(date), mealType))"
              @drag-leave="handleDragLeave(cellKey(toISODate(date), mealType))"
              @drop="(altKey) => handleDrop(toISODate(date), mealType, altKey)"
            />
          </div>
        </template>
      </div>

      <p v-if="!isReadOnly" class="drag-hint">{{ $t('planning.dragHint') }}</p>
    </template>

    <template v-else-if="viewMode === 'month'">
      <div class="agenda-month">
        <div v-for="date in weekDays" :key="'h' + toISODate(date)" class="month-head">
          {{ weekdayLabel(date) }}
        </div>
        <template v-for="(week, wi) in monthWeeks" :key="wi">
          <div
            v-for="(date, di) in week"
            :key="wi + '-' + di"
            :class="[
              'month-cell',
              { empty: !date, 'is-today': date && isToday(date), over: date && overKey === toISODate(date) },
            ]"
            :data-date="date ? toISODate(date) : undefined"
            @dragover.prevent="date && handleDragOver(toISODate(date))"
            @dragleave="date && handleDragLeave(toISODate(date))"
            @drop.prevent="date && handleMonthDrop(toISODate(date), $event.altKey)"
          >
            <template v-if="date">
              <button
                type="button"
                class="month-day-num"
                :aria-label="dayLongLabel(date)"
                @click="goToWeekOf(date)"
              >
                {{ date.getDate() }}
              </button>
              <ul v-if="entriesForDay(date).length" class="month-entries">
                <li
                  v-for="entry in entriesForDay(date).slice(0, MONTH_MAX_VISIBLE)"
                  :key="entry.id"
                  class="month-item"
                  :draggable="!isReadOnly"
                  @dragstart="handleDragStart(entry)"
                  @dragend="handleDragEnd"
                >
                  <RouterLink
                    :to="{ name: 'recipe-detail', params: { id: entry.recipe } }"
                    :title="`${$t(`mealType.${entry.meal_type}`)} : ${entry.recipe_title}`"
                  >
                    <span class="month-slot" aria-hidden="true">{{ MEAL_ICONS[entry.meal_type] }}</span>
                    <span class="month-title">{{ entry.recipe_title }}</span>
                  </RouterLink>
                </li>
              </ul>
              <button
                v-if="entriesForDay(date).length > MONTH_MAX_VISIBLE"
                type="button"
                class="month-more"
                @click="goToWeekOf(date)"
              >
                {{ $t('planning.moreEntries', { n: entriesForDay(date).length - MONTH_MAX_VISIBLE }) }}
              </button>
              <span v-if="entriesForDay(date).length" class="month-dots" aria-hidden="true">
                <i v-for="n in Math.min(entriesForDay(date).length, 3)" :key="n" />
              </span>
            </template>
          </div>
        </template>
      </div>

      <p class="drag-hint">{{ $t('planning.monthHint') }}</p>
    </template>

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

    <footer class="week-footer">
      <p class="planned-count">
        <strong>{{ entries.length }}</strong> {{ plannedCountLabel }} {{ periodText }}
      </p>
      <div class="week-footer-actions">
        <button v-if="nutritionAlertsEnabled" class="pill-btn nutrition-btn" type="button" @click="showNutrition = true">
          <Apple :size="16" />{{ $t('planning.nutritionIntake') }}
        </button>
        <CalendarExportMenu :params="currentParams()">
          <template #default="{ close }">
            <button
              type="button"
              class="menu-item"
              role="menuitem"
              @click="close(); handleDownloadWeekPdf()"
            >
              {{ viewMode === 'month' ? $t('planning.downloadMonthPdf') : $t('planning.downloadWeekPdf') }}
            </button>
          </template>
        </CalendarExportMenu>
        <button class="pill-btn primary generate-btn" :disabled="!entries.length" @click="handleGenerateShoppingList">
          {{ $t('planning.generateShoppingList') }}
        </button>
      </div>
    </footer>

    <div v-if="toast" class="undo-toast" role="status">
      <span>{{ $t('planning.removedToast', { title: toast.entry.recipe_title }) }}</span>
      <button type="button" @click="undoRemove">{{ $t('common.undo') }}</button>
    </div>
  </div>
</template>

<style scoped>
.planner :focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.agenda-switcher {
  max-width: 320px;
  margin-bottom: 1rem;
}

/* Bascule Semaine / Mois */
.seg {
  display: inline-flex;
  background: var(--color-primary-soft);
  border-radius: 999px;
  padding: 3px;
  margin-bottom: 1rem;
}

.view-btn {
  border: 0;
  background: transparent;
  border-radius: 999px;
  padding: 7px 18px;
  min-height: auto;
  font-weight: 600;
  color: var(--color-primary-dark);
}

.view-btn:hover {
  background: var(--color-primary-soft-hover);
}

.view-btn.on {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

/* Navigation */
.week-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 1rem;
}

.week-range {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.week-range h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.round {
  width: 40px;
  height: 40px;
  min-height: auto;
  flex: none;
  border: 0;
  border-radius: 50%;
  padding: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  display: grid;
  place-items: center;
}

.round:hover {
  background: var(--color-primary-soft-hover);
}

.today-btn {
  min-height: auto;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: 999px;
  padding: 5px 13px;
  font-size: 0.8rem;
  font-weight: 600;
}

.today-btn:hover {
  background: var(--color-primary-soft);
}

/* Sélecteur de jour */
.day-chips {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}

.day-chip {
  flex: 1;
  min-width: 0;
  min-height: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 0;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text);
  text-transform: capitalize;
}

.day-chip strong {
  font-size: 0.95rem;
  color: var(--color-text);
}

.day-chip.today strong {
  color: var(--color-primary-dark);
}

.day-chip.on {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}

.day-chip.on strong {
  color: var(--color-on-primary);
}

.day-chip.over {
  outline: 2px dashed var(--color-primary);
  outline-offset: 2px;
}

/* Grille semaine */
.agenda-week,
.agenda-month {
  display: grid;
  gap: 1px;
  background: var(--color-border);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  overflow: hidden;
}

.agenda-week {
  grid-template-columns: 84px minmax(0, 1fr);
}

.agenda-cell:not(.is-active-day) {
  display: none;
}

.agenda-week > *,
.agenda-month > * {
  background: var(--color-surface);
}

.agenda-row-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 10px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-muted);
}

.slot-icon {
  font-size: 16px;
  line-height: 1;
}

.agenda-cell.is-today {
  background: color-mix(in srgb, var(--color-primary-soft) 55%, var(--color-surface));
}

.drag-hint {
  margin: 10px 2px 0;
  font-size: 0.8rem;
  color: var(--color-muted);
}

/* Vue mois */
.agenda-month {
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.month-head {
  padding: 10px 6px;
  text-align: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: capitalize;
}

.month-cell {
  position: relative;
  min-height: 132px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.agenda-month > .month-cell.empty {
  background: var(--color-bg);
}

.agenda-month > .month-cell.is-today {
  background: color-mix(in srgb, var(--color-primary-soft) 55%, var(--color-surface));
}

.agenda-month > .month-cell.over {
  outline: 2px dashed var(--color-primary);
  outline-offset: -4px;
  background: var(--color-primary-soft);
}

.month-day-num {
  align-self: flex-start;
  min-width: 28px;
  height: 28px;
  min-height: auto;
  padding: 0 4px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text);
  display: grid;
  place-items: center;
  font-size: 0.95rem;
  font-weight: 700;
}

.month-day-num:hover {
  background: var(--color-primary-soft);
}

.month-cell.is-today .month-day-num {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.month-entries {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.month-item {
  background: var(--color-primary-soft);
  border-radius: 8px;
  cursor: grab;
}

.month-item:active {
  cursor: grabbing;
}

.month-item a {
  display: flex;
  gap: 5px;
  align-items: flex-start;
  padding: 3px 6px;
  color: var(--color-primary-dark);
  text-decoration: none;
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.25;
}

.month-item a:hover .month-title {
  text-decoration: underline;
}

.month-slot {
  flex: none;
  font-size: 12px;
  line-height: 1.3;
}

.month-title {
  overflow: hidden;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.month-more {
  align-self: flex-start;
  min-height: auto;
  border: 0;
  background: transparent;
  padding: 2px 6px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-primary-dark);
  text-decoration: underline;
}

.month-dots {
  display: none;
}

/* Pied */
.week-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px 16px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.planned-count {
  margin: 0;
  color: var(--color-muted);
}

.planned-count strong {
  color: var(--color-text);
  font-size: 1.1rem;
}

.week-footer-actions {
  width: 100%;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.generate-btn {
  flex: 1;
  justify-content: center;
}

.pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  border-radius: 999px;
  padding: 0.7rem 1.25rem;
  font-weight: 600;
}

.pill-btn:hover {
  background: var(--color-primary-soft);
}

.pill-btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}

.pill-btn.primary:hover {
  background: var(--color-primary-dark);
}

.pill-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.deficiency-banner ul {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
}

.carbon-summary {
  margin: 1rem 0 0;
}

/* Toast d'annulation */
.undo-toast {
  position: fixed;
  left: 50%;
  bottom: calc(20px + env(safe-area-inset-bottom, 0px));
  transform: translateX(-50%);
  z-index: 60;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  border-radius: 14px;
  background: #2b201e;
  color: #fff;
  box-shadow: 0 10px 28px rgba(60, 20, 15, 0.18);
  max-width: calc(100vw - 32px);
}

.undo-toast button {
  min-height: auto;
  border: 0;
  background: transparent;
  color: #ffb3ae;
  font-weight: 700;
  text-decoration: underline;
  padding: 4px;
}

@media (hover: none) {
  .drag-hint {
    display: none;
  }
}

/* Mobile : un jour à la fois */
@media (max-width: 760px) {
  .agenda-week {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .agenda-row-head {
    padding: 12px 6px 12px 8px;
    font-size: 0.78rem;
  }

  /* Mois : pastilles à la place des titres, un clic sur la case ouvre la semaine */
  .month-head {
    padding: 8px 0;
    font-size: 11px;
  }

  .month-cell {
    min-height: 60px;
    padding: 4px 2px;
    align-items: center;
    gap: 2px;
  }

  .month-entries,
  .month-more {
    display: none;
  }

  .month-day-num {
    align-self: center;
  }

  .month-day-num::after {
    content: '';
    position: absolute;
    inset: 0;
  }

  .month-dots {
    display: flex;
    gap: 3px;
  }

  .month-dots i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-primary);
  }

  .drag-hint {
    display: none;
  }
}
</style>
