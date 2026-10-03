<script setup lang="ts">
import { Leaf, ListFilter, RotateCcw, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, type WritableComputedRef } from 'vue'
import { useI18n } from 'vue-i18n'
import VueMultiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.css'
import { listAllergens } from '../../api/allergens'
import { listIngredients } from '../../api/ingredients'
import { formatDuration } from '../../utils/format'
import type { Allergen } from '../../types/models'

const { t } = useI18n()

export interface RecipeFilterValues {
  search: string
  diet_type: string
  max_prep_time: string | number
  max_cook_time: string | number
  ingredients: string
  in_season: boolean
  carbon_level: string
  // Slugs d'allergènes à exclure, séparés par des virgules (cf. filtre backend).
  exclude_allergens: string
}

// Les filtres sont édités en place (v-model sur les propriétés de l'objet) : la vue parente
// garde la main sur la synchro URL / chargement. Pour ajouter un filtre : une clé dans
// RecipeFilterValues + filtersFromQuery (vue parente), et un bloc .field dans le template.
// Le badge et le bouton "Réinitialiser" sont génériques (ils parcourent les clés).
const filters = defineModel<RecipeFilterValues>({ required: true })

// Slugs du profil (allergies + intolérances) : raccourci "ajouter mes allergènes".
const props = defineProps<{ myAllergens?: string[] }>()

// Sur mobile seulement : le panneau est replié derrière le bouton "Filtres". Sur desktop,
// il est toujours affiché en colonne latérale (cf. CSS) et ce bouton est masqué.
const isOpen = ref(false)

const activeCount = computed(
  () => Object.values(filters.value).filter((value) => value !== '' && value !== false && value != null).length,
)

function reset() {
  const empty = {} as Record<string, unknown>
  for (const [key, value] of Object.entries(filters.value)) {
    empty[key] = typeof value === 'boolean' ? false : ''
  }
  filters.value = empty as unknown as RecipeFilterValues
}

function splitList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

// --- Régime -----------------------------------------------------------------------------
const DIET_OPTIONS = ['', 'omnivore', 'vegetarian', 'vegan'] as const

// --- Ingrédients (multi-select) ----------------------------------------------------------
// La valeur reste une liste de noms séparés par des virgules (contrat backend inchangé :
// filter_ingredients fait un rapprochement approximatif sur les noms). Les options viennent
// de l'API ingrédients, recherchées à la frappe ; un nom libre reste possible (Entrée).
const selectedIngredients = computed<string[]>({
  get: () => splitList(filters.value.ingredients),
  set: (names) => {
    filters.value.ingredients = names.join(',')
  },
})
const ingredientOptions = ref<string[]>([])
const ingredientsLoading = ref(false)
let ingredientTimer: ReturnType<typeof setTimeout> | undefined
let ingredientRequest = 0

function searchIngredients(query: string) {
  clearTimeout(ingredientTimer)
  ingredientTimer = setTimeout(async () => {
    const requestId = ++ingredientRequest
    ingredientsLoading.value = true
    try {
      const data = await listIngredients(query ? { search: query } : {})
      if (requestId === ingredientRequest) ingredientOptions.value = data.results.map((item) => item.name)
    } catch {
      if (requestId === ingredientRequest) ingredientOptions.value = []
    } finally {
      if (requestId === ingredientRequest) ingredientsLoading.value = false
    }
  }, 250)
}

function addIngredient(name: string) {
  const trimmed = name.trim()
  if (trimmed && !selectedIngredients.value.includes(trimmed)) {
    selectedIngredients.value = [...selectedIngredients.value, trimmed]
  }
}

onBeforeUnmount(() => clearTimeout(ingredientTimer))

// --- Allergènes à exclure (multi-select) -------------------------------------------------
const allergenList = ref<Allergen[]>([])
onMounted(async () => {
  allergenList.value = await listAllergens().catch(() => [])
})

const selectedAllergens = computed<Allergen[]>({
  get: () =>
    splitList(filters.value.exclude_allergens).map(
      (slug) => allergenList.value.find((allergen) => allergen.slug === slug) ?? { slug, name: slug },
    ),
  set: (allergens) => {
    filters.value.exclude_allergens = allergens.map((allergen) => allergen.slug).join(',')
  },
})

const missingMyAllergens = computed(() => {
  const selected = new Set(splitList(filters.value.exclude_allergens))
  return (props.myAllergens ?? []).filter((slug) => !selected.has(slug))
})

function addMyAllergens() {
  const slugs = [...splitList(filters.value.exclude_allergens), ...missingMyAllergens.value]
  filters.value.exclude_allergens = slugs.join(',')
}

// --- Temps max (sliders) -----------------------------------------------------------------
// Le cran tout à droite (au-delà de TIME_MAX) signifie "sans limite" (filtre vide).
const TIME_MIN = 5
const TIME_MAX = 180
const TIME_STEP = 5
const TIME_NO_LIMIT = TIME_MAX + TIME_STEP

function timeSlider(key: 'max_prep_time' | 'max_cook_time'): WritableComputedRef<number> {
  return computed({
    get: () => {
      const value = filters.value[key]
      return value === '' || value == null ? TIME_NO_LIMIT : Math.min(Number(value), TIME_NO_LIMIT)
    },
    set: (position) => {
      const minutes = Number(position)
      filters.value[key] = minutes > TIME_MAX ? '' : minutes
    },
  })
}

const prepSlider = timeSlider('max_prep_time')
const cookSlider = timeSlider('max_cook_time')

const timeSliders = [
  { key: 'max_prep_time', id: 'max_prep', label: 'recipes.maxPrepTime', model: prepSlider },
  { key: 'max_cook_time', id: 'max_cook', label: 'recipes.maxCookTime', model: cookSlider },
] as const

function timeLabel(value: string | number) {
  return value === '' || value == null ? null : formatDuration(Number(value))
}

function fillPercent(position: number) {
  return `${((position - TIME_MIN) / (TIME_NO_LIMIT - TIME_MIN)) * 100}%`
}

// --- Impact carbone (slider à 4 crans : tous / faible / moyen / élevé) -------------------
const CARBON_LEVELS = ['', 'low', 'medium', 'high'] as const
const CARBON_LABELS = {
  '': 'recipes.carbonAny',
  low: 'recipes.carbonLow',
  medium: 'recipes.carbonMedium',
  high: 'recipes.carbonHigh',
} as const

const carbonPosition = computed<number>({
  get: () => Math.max(0, CARBON_LEVELS.indexOf(filters.value.carbon_level as (typeof CARBON_LEVELS)[number])),
  set: (position) => {
    filters.value.carbon_level = CARBON_LEVELS[Number(position)] ?? ''
  },
})
const carbonLevel = computed(() => CARBON_LEVELS[carbonPosition.value])

// --- Pilules "filtres actifs" -------------------------------------------------------------
// Résumé compact, affiché à côté du bouton "Filtres" (utile surtout sur mobile, où le panneau
// est replié) : un filtre par pilule, supprimable individuellement sans ouvrir le panneau. Les
// filtres à valeurs multiples (ingrédients, allergènes) donnent une pilule par valeur.
interface FilterChip {
  id: string
  label: string
  remove: () => void
}

const filterChips = computed<FilterChip[]>(() => {
  const chips: FilterChip[] = []

  if (filters.value.search) {
    const value = filters.value.search
    chips.push({ id: 'search', label: value, remove: () => { filters.value.search = '' } })
  }
  if (filters.value.diet_type) {
    chips.push({
      id: 'diet',
      label: t(`diet.${filters.value.diet_type}`),
      remove: () => { filters.value.diet_type = '' },
    })
  }
  if (filters.value.in_season) {
    chips.push({ id: 'season', label: t('recipes.inSeason'), remove: () => { filters.value.in_season = false } })
  }
  for (const name of selectedIngredients.value) {
    chips.push({
      id: `ingredient-${name}`,
      label: name,
      remove: () => { selectedIngredients.value = selectedIngredients.value.filter((n) => n !== name) },
    })
  }
  const prepLabel = timeLabel(filters.value.max_prep_time)
  if (prepLabel) {
    chips.push({
      id: 'prep',
      label: t('recipes.maxPrepTimeChip', { time: prepLabel }),
      remove: () => { filters.value.max_prep_time = '' },
    })
  }
  const cookLabel = timeLabel(filters.value.max_cook_time)
  if (cookLabel) {
    chips.push({
      id: 'cook',
      label: t('recipes.maxCookTimeChip', { time: cookLabel }),
      remove: () => { filters.value.max_cook_time = '' },
    })
  }
  if (filters.value.carbon_level) {
    chips.push({
      id: 'carbon',
      label: t(CARBON_LABELS[filters.value.carbon_level as (typeof CARBON_LEVELS)[number]]),
      remove: () => { filters.value.carbon_level = '' },
    })
  }
  for (const allergen of selectedAllergens.value) {
    chips.push({
      id: `allergen-${allergen.slug}`,
      label: allergen.name,
      remove: () => {
        selectedAllergens.value = selectedAllergens.value.filter((a) => a.slug !== allergen.slug)
      },
    })
  }

  return chips
})
</script>

<template>
  <div class="recipe-filters">
    <button
      type="button"
      class="secondary toggle"
      :aria-expanded="isOpen"
      aria-controls="recipe-filters-panel"
      @click="isOpen = !isOpen"
    >
      <ListFilter :size="16" />{{ $t('recipes.filters') }}
      <span
        v-if="activeCount"
        class="badge"
        data-testid="filters-badge"
        :aria-label="$t('recipes.activeFilters', { count: activeCount })"
      >{{ activeCount }}</span>
    </button>

    <!-- Sur mobile : résumé à côté du bouton "Filtres", visible sans ouvrir le panneau. Sur
         desktop (panneau toujours ouvert, pas de bouton) : même liste, rattachée au panneau
         juste sous l'en-tête "Filtres" (cf. règles --mobile/--desktop plus bas). -->
    <ul
      v-if="filterChips.length"
      class="active-filters active-filters--mobile"
      :aria-label="$t('recipes.activeFiltersList')"
    >
      <li v-for="chip in filterChips" :key="chip.id">
        <button
          type="button"
          class="filter-chip"
          :aria-label="$t('recipes.removeFilterChip', { label: chip.label })"
          @click="chip.remove"
        >
          {{ chip.label }}
          <X :size="12" aria-hidden="true" />
        </button>
      </li>
    </ul>

    <aside
      id="recipe-filters-panel"
      class="card panel"
      :class="{ 'is-open': isOpen }"
      :aria-label="$t('recipes.filters')"
    >
      <div class="panel-header">
        <strong class="panel-title">
          <ListFilter :size="16" aria-hidden="true" />{{ $t('recipes.filters') }}
          <span
            v-if="activeCount"
            class="badge header-badge"
            :aria-label="$t('recipes.activeFilters', { count: activeCount })"
          >{{ activeCount }}</span>
        </strong>
        <button type="button" class="secondary close" :aria-label="$t('common.close')" @click="isOpen = false">
          <X :size="16" />
        </button>
      </div>

      <ul
        v-if="filterChips.length"
        class="active-filters active-filters--desktop"
        :aria-label="$t('recipes.activeFiltersList')"
      >
        <li v-for="chip in filterChips" :key="chip.id">
          <button
            type="button"
            class="filter-chip"
            :aria-label="$t('recipes.removeFilterChip', { label: chip.label })"
            @click="chip.remove"
          >
            {{ chip.label }}
            <X :size="12" aria-hidden="true" />
          </button>
        </li>
      </ul>

      <div class="field">
        <label for="search">{{ $t('recipes.search') }}</label>
        <input id="search" v-model="filters.search" :placeholder="$t('recipes.searchPlaceholder')" />
      </div>

      <div class="field">
        <button
          type="button"
          class="season-toggle"
          :class="{ 'is-active': filters.in_season }"
          :aria-pressed="filters.in_season"
          :title="$t('recipes.inSeasonOnly')"
          :aria-label="$t('recipes.inSeasonOnly')"
          data-testid="in-season-toggle"
          @click="filters.in_season = !filters.in_season"
        >
          <span class="season-icon" aria-hidden="true"><Leaf :size="18" /></span>
          <span>{{ $t('recipes.inSeason') }}</span>
        </button>
      </div>

      <fieldset class="field radio-group">
        <legend>{{ $t('recipes.dietFilter') }}</legend>
        <label v-for="diet in DIET_OPTIONS" :key="diet || 'all'" class="radio-option">
          <input v-model="filters.diet_type" type="radio" name="diet_type" :value="diet" />
          {{ diet ? $t(`diet.${diet}`) : $t('recipes.allDiets') }}
        </label>
      </fieldset>

      <div class="field">
        <label for="ingredients">{{ $t('recipes.ingredientsFilter') }}</label>
        <VueMultiselect
          id="ingredients"
          v-model="selectedIngredients"
          name="ingredients"
          :options="ingredientOptions"
          :multiple="true"
          :taggable="true"
          :searchable="true"
          :internal-search="false"
          :loading="ingredientsLoading"
          :clear-on-select="true"
          :close-on-select="false"
          :show-labels="false"
          :options-limit="50"
          :placeholder="$t('recipes.ingredientsPlaceholder')"
          :tag-placeholder="$t('recipes.addAsIngredient')"
          @search-change="searchIngredients"
          @open="searchIngredients('')"
          @tag="addIngredient"
        >
          <template #noResult>{{ $t('recipes.ingredientsNoResult') }}</template>
          <template #noOptions>{{ $t('recipes.ingredientsNoResult') }}</template>
        </VueMultiselect>
      </div>

      <div v-for="slider in timeSliders" :key="slider.key" class="field">
        <label :for="slider.id" class="slider-label">
          <span>{{ $t(slider.label) }}</span>
          <span class="slider-value">{{ timeLabel(filters[slider.key]) ?? $t('recipes.noTimeLimit') }}</span>
        </label>
        <input
          :id="slider.id"
          v-model.number="slider.model.value"
          class="range time-range"
          type="range"
          :min="TIME_MIN"
          :max="TIME_NO_LIMIT"
          :step="TIME_STEP"
          :style="{ '--fill': fillPercent(slider.model.value) }"
          :aria-valuetext="timeLabel(filters[slider.key]) ?? $t('recipes.noTimeLimit')"
        />
      </div>

      <div class="field">
        <label for="carbon_level" class="slider-label">
          <span>{{ $t('recipes.carbonLevel') }}</span>
        </label>
        <input
          id="carbon_level"
          v-model.number="carbonPosition"
          class="range carbon-range"
          :class="`carbon-${carbonLevel || 'any'}`"
          type="range"
          min="0"
          :max="CARBON_LEVELS.length - 1"
          step="1"
          :aria-valuetext="$t(CARBON_LABELS[carbonLevel])"
        />
        <span class="carbon-value" :class="`carbon-${carbonLevel || 'any'}`">{{ $t(CARBON_LABELS[carbonLevel]) }}</span>
      </div>

      <div class="field">
        <label for="exclude_allergens">{{ $t('recipes.excludeAllergens') }}</label>
        <VueMultiselect
          id="exclude_allergens"
          v-model="selectedAllergens"
          name="exclude_allergens"
          :options="allergenList"
          :multiple="true"
          track-by="slug"
          label="name"
          :close-on-select="false"
          :show-labels="false"
          :placeholder="$t('recipes.excludeAllergensPlaceholder')"
        />
        <button
          v-if="missingMyAllergens.length"
          type="button"
          class="link-btn"
          data-testid="add-my-allergens"
          @click="addMyAllergens"
        >
          {{ $t('recipes.addMyAllergens') }}
        </button>
      </div>

      <div class="panel-footer">
        <button type="button" class="secondary reset" :disabled="!activeCount" @click="reset">
          <RotateCcw :size="16" />{{ $t('recipes.resetFilters') }}
        </button>
        <button type="button" class="apply" @click="isOpen = false">{{ $t('recipes.showResults') }}</button>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.toggle {
  display: none;
  align-items: center;
  gap: 0.4rem;
}
.badge {
  min-width: 1.35rem;
  height: 1.35rem;
  padding: 0 0.35rem;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0;
  list-style: none;
}
.active-filters--mobile {
  display: none;
  margin: 0.6rem 0 0;
}
.active-filters--desktop {
  margin: 0 0 1rem;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: auto;
  padding: 0.3rem 0.6rem;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-size: 0.8rem;
  font-weight: 600;
}
.filter-chip:hover {
  background: var(--color-primary-soft-hover);
}

.panel {
  padding: 1.1rem;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.close,
.apply {
  display: none;
}
.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.25rem;
}
.panel-footer .reset {
  flex: 1;
}

.radio-group legend {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-muted);
}

/* Liste de boutons radio pour le régime. */
.radio-group {
  border: 0;
  padding: 0;
  min-width: 0;
}
.radio-group legend {
  padding: 0;
  margin-bottom: 0.3rem;
}
/* `.field .radio-option` pour passer devant `.field label` (base.css). */
.field .radio-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.15rem 0;
  font-size: 0.92rem;
  font-weight: 500;
  color: var(--color-text);
}
.radio-option input {
  min-height: auto;
  margin: 0;
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-primary);
}

/* "De saison" : pilule cliquable ; la feuille est barrée tant que le filtre est inactif. */
.season-toggle {
  align-self: flex-start;
  min-height: 2.5rem;
  padding: 0.45rem 1rem 0.45rem 0.75rem;
  background: var(--color-surface-muted);
  color: var(--color-muted);
}
.season-toggle:hover {
  background: var(--color-primary-soft-hover);
}
.season-toggle.is-active {
  background: color-mix(in srgb, var(--color-vegetarian) 15%, var(--color-surface));
  color: color-mix(in srgb, var(--color-vegetarian) 80%, var(--color-text));
}
.season-icon {
  position: relative;
  display: inline-flex;
}
.season-toggle:not(.is-active) .season-icon::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 130%;
  height: 2px;
  border-radius: 2px;
  background: currentColor;
  box-shadow: 0 0 0 1.5px var(--color-surface-muted);
  transform: translate(-50%, -50%) rotate(-45deg);
}

/* Sliders : base.css habille tous les <input>, on repart d'une piste nue. */
.slider-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}
.slider-value {
  color: var(--color-primary-dark);
}
.range {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  min-height: auto;
  height: 1.5rem;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  --track: var(--color-primary-soft);
  --thumb: var(--color-primary);
}
.range:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 4px;
}
.range::-webkit-slider-runnable-track {
  height: 0.4rem;
  border-radius: var(--radius-pill);
  background: var(--track);
}
.range::-moz-range-track {
  height: 0.4rem;
  border-radius: var(--radius-pill);
  background: var(--track);
}
.range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 1.15rem;
  height: 1.15rem;
  margin-top: -0.375rem;
  border-radius: 50%;
  background: var(--color-surface);
  border: 3px solid var(--thumb);
  box-shadow: 0 1px 3px rgba(36, 31, 29, 0.25);
}
.range::-moz-range-thumb {
  width: 0.95rem;
  height: 0.95rem;
  border-radius: 50%;
  background: var(--color-surface);
  border: 3px solid var(--thumb);
  box-shadow: 0 1px 3px rgba(36, 31, 29, 0.25);
}
.time-range {
  --track: linear-gradient(
    to right,
    var(--color-primary) 0 var(--fill),
    var(--color-primary-soft) var(--fill) 100%
  );
}

/* Impact carbone : mêmes couleurs que le badge carbone de RecipeCard.vue. Quatre crans
   (0 %, 33 %, 67 %, 100 %) : "Tous" en neutre, puis faible / moyen / élevé. */
.carbon-range {
  --track: linear-gradient(
    to right,
    var(--color-border) 0 16.5%,
    var(--color-vegetarian) 16.5% 50%,
    var(--color-carbon-medium) 50% 83.5%,
    var(--color-danger) 83.5% 100%
  );
}
.carbon-range.carbon-any {
  --thumb: var(--color-muted);
}
.carbon-range.carbon-low {
  --thumb: var(--color-vegetarian);
}
.carbon-range.carbon-medium {
  --thumb: var(--color-carbon-medium);
}
.carbon-range.carbon-high {
  --thumb: var(--color-danger);
}
.carbon-value {
  font-size: 0.85rem;
  font-weight: 600;
}
.carbon-value.carbon-any {
  color: var(--color-muted);
}
.carbon-value.carbon-low {
  color: color-mix(in srgb, var(--color-vegetarian) 80%, var(--color-text));
}
.carbon-value.carbon-medium {
  color: color-mix(in srgb, var(--color-carbon-medium) 85%, var(--color-text));
}
.carbon-value.carbon-high {
  color: var(--color-danger);
}

.link-btn {
  align-self: flex-start;
  min-height: auto;
  padding: 0.2rem 0;
  background: none;
  color: var(--color-primary-dark);
  font-size: 0.85rem;
  text-decoration: underline;
}
.link-btn:hover {
  background: none;
}

/* Mobile : le panneau est replié derrière le bouton "Filtres" et s'ouvre au-dessus de la
   liste (dans le flux, pas en surimpression). Desktop : colonne latérale toujours visible. */
@media (max-width: 600px) {
  .recipe-filters {
    margin-bottom: 1rem;
  }
  .toggle {
    display: inline-flex;
  }
  .active-filters--mobile {
    display: flex;
  }
  .active-filters--desktop {
    display: none;
  }
  .panel {
    display: none;
    margin-top: 0.75rem;
  }
  .panel.is-open {
    display: block;
  }
  .header-badge {
    display: none;
  }
  .close,
  .apply {
    display: inline-flex;
  }
  .panel-footer {
    justify-content: space-between;
  }
  .panel-footer .reset {
    flex: 0 1 auto;
  }
}
</style>

<!-- vue-multiselect, aux couleurs du site : pilules couleur primaire pour les valeurs choisies. -->
<style>
.recipe-filters .multiselect {
  min-height: 2.75rem;
  color: var(--color-text);
  font-size: 0.92rem;
}
.recipe-filters .multiselect__tags {
  min-height: 2.75rem;
  padding: 0.45rem 2.5rem 0 0.6rem;
  border: 1.5px solid var(--color-primary-soft);
  border-radius: 8px;
  background: var(--color-surface);
  font-size: 0.92rem;
}
.recipe-filters .multiselect--active .multiselect__tags {
  border-color: var(--color-primary);
}
.recipe-filters .multiselect__input,
.recipe-filters .multiselect__single,
.recipe-filters .multiselect__placeholder {
  min-height: auto;
  border: 0;
  padding: 0 0 0 0.2rem;
  margin-bottom: 0.45rem;
  background: transparent;
  color: var(--color-text);
  font-size: 0.92rem;
}
.recipe-filters .multiselect__placeholder {
  color: var(--color-muted);
  padding-top: 0.15rem;
}
.recipe-filters .multiselect__tag {
  margin: 0 0.3rem 0.4rem 0;
  padding: 0.25rem 1.7rem 0.25rem 0.65rem;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
  font-size: 0.82rem;
}
.recipe-filters .multiselect__tag-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  width: 1.4rem;
}
.recipe-filters .multiselect__tag-icon::after {
  color: var(--color-on-primary);
  opacity: 0.85;
}
.recipe-filters .multiselect__tag-icon:focus,
.recipe-filters .multiselect__tag-icon:hover {
  background: var(--color-primary-dark);
}
.recipe-filters .multiselect__tag-icon:focus::after,
.recipe-filters .multiselect__tag-icon:hover::after {
  color: var(--color-on-primary);
  opacity: 1;
}
.recipe-filters .multiselect__select {
  height: 2.6rem;
}
.recipe-filters .multiselect__select::before {
  border-color: var(--color-muted) transparent transparent;
}
.recipe-filters .multiselect__spinner {
  background: transparent;
}
.recipe-filters .multiselect__spinner::before,
.recipe-filters .multiselect__spinner::after {
  border-top-color: var(--color-primary);
}
.recipe-filters .multiselect__content-wrapper {
  background: var(--color-surface);
  border-color: var(--color-border);
  border-radius: 0 0 12px 12px;
  box-shadow: var(--shadow-card);
}
.recipe-filters .multiselect--above .multiselect__content-wrapper {
  border-radius: 12px 12px 0 0;
}
.recipe-filters .multiselect__option {
  min-height: 2.4rem;
  padding: 0.6rem 0.75rem;
  font-size: 0.9rem;
}
.recipe-filters .multiselect__option--highlight,
.recipe-filters .multiselect__option--highlight::after {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}
.recipe-filters .multiselect__option--selected {
  background: var(--color-surface-muted);
  color: var(--color-text);
  font-weight: 700;
}
.recipe-filters .multiselect__option--selected.multiselect__option--highlight,
.recipe-filters .multiselect__option--selected.multiselect__option--highlight::after {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}
</style>
