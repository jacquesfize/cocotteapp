<script setup lang="ts">
import { ChevronLeft, ChevronRight, Download, ShoppingCart } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import MealSlot from '../components/MealSlot.vue'
import { downloadWeekPdf, getNutritionSummary, listMealPlanEntries, listSharedWithMe } from '../api/planning'
import { createShoppingList } from '../api/shopping'
import { addDays, startOfWeek, toISODate } from '../utils/dates'
import { downloadBlob } from '../utils/download'
import { NUTRIENT_LABEL_KEYS } from '../utils/nutrition'
import type { MealPlanEntryListParams } from '../types/api'
import type { MealPlanEntry, MealType, NutrientDeficiency, PlanningShareReceived } from '../types/models'

const { t, locale } = useI18n()
const router = useRouter()

const MEAL_TYPES: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack']

const weekOffset = ref(0)
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

function dayLabel(date: Date) {
  return date.toLocaleDateString(locale.value, { weekday: 'short', day: 'numeric', month: 'short' })
}

function entriesFor(date: Date, mealType: MealType) {
  const iso = toISODate(date)
  return entries.value.filter((e) => e.date === iso && e.meal_type === mealType)
}

function currentParams(): MealPlanEntryListParams {
  const params: MealPlanEntryListParams = {
    date_after: toISODate(weekDays.value[0]),
    date_before: toISODate(weekDays.value[6]),
  }
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

watch(weekOffset, load)
watch(selectedOwner, load)
onMounted(load)
onMounted(loadSharedAgendas)

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
  const fmt = (d: Date) => d.toLocaleDateString(locale.value, { day: 'numeric', month: 'short' })
  return `${fmt(weekDays.value[0])} – ${fmt(weekDays.value[6])}`
})
</script>

<template>
  <div>
    <h1>{{ $t('planning.title') }}</h1>

    <div v-if="sharedAgendas.length" class="field agenda-switcher">
      <label for="agenda-select">{{ $t('planning.agendaSelectorLabel') }}</label>
      <select id="agenda-select" v-model="selectedOwner">
        <option :value="null">{{ $t('planning.myAgenda') }}</option>
        <option v-for="share in sharedAgendas" :key="share.id" :value="share.owner">
          {{ agendaLabel(share) }}
        </option>
      </select>
    </div>

    <div class="week-nav">
      <button
        class="secondary icon-btn"
        type="button"
        :aria-label="$t('planning.previousWeek')"
        @click="weekOffset -= 1"
      >
        <ChevronLeft :size="18" />
      </button>
      <div class="week-range">
        <strong>{{ rangeLabel }}</strong>
        <button v-if="weekOffset !== 0" class="today-btn secondary" type="button" @click="weekOffset = 0">
          {{ $t('planning.today') }}
        </button>
      </div>
      <button
        class="secondary icon-btn"
        type="button"
        :aria-label="$t('planning.nextWeek')"
        @click="weekOffset += 1"
      >
        <ChevronRight :size="18" />
      </button>
    </div>

    <div v-if="deficiencies.length" class="card deficiency-banner">
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

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>

    <div class="week-grid">
      <div v-for="date in weekDays" :key="toISODate(date)" class="card day-col">
        <h3>{{ dayLabel(date) }}</h3>
        <MealSlot
          v-for="mealType in MEAL_TYPES"
          :key="mealType"
          :date="toISODate(date)"
          :meal-type="mealType"
          :entries="entriesFor(date, mealType)"
          :owner="selectedOwner ?? undefined"
          :read-only="isReadOnly"
          @changed="load"
        />
      </div>
    </div>

    <div class="week-footer">
      <button class="secondary" @click="handleDownloadWeekPdf">
        <Download :size="16" />{{ $t('planning.downloadWeekPdf') }}
      </button>
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

.deficiency-banner {
  border: 1.5px solid var(--color-primary-soft);
  margin-bottom: 1rem;
}

.deficiency-banner ul {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
}

.carbon-summary {
  margin: 0 0 1rem;
}

.week-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.75rem;
}

.day-col h3 {
  margin: 0 0 0.25rem;
  font-size: 0.9rem;
  text-transform: capitalize;
}

.week-footer {
  margin-top: 1.25rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .week-grid {
    grid-template-columns: 1fr;
  }
}
</style>
