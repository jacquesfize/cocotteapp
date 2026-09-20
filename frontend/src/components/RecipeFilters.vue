<script setup lang="ts">
import { ListFilter, RotateCcw, X } from '@lucide/vue'
import { computed, ref } from 'vue'

export interface RecipeFilterValues {
  search: string
  diet_type: string
  max_prep_time: string | number
  max_cook_time: string | number
  ingredients: string
  in_season: boolean
}

// Les filtres sont édités en place (v-model sur les propriétés de l'objet) : la vue parente
// garde la main sur la synchro URL / chargement. Pour ajouter un filtre : une clé dans
// RecipeFilterValues + filtersFromQuery (vue parente), et un bloc .field dans le template.
// Le badge et le bouton "Réinitialiser" sont génériques (ils parcourent les clés).
const filters = defineModel<RecipeFilterValues>({ required: true })

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

    <div v-if="isOpen" class="backdrop" @click="isOpen = false" />
    <div
      v-show="isOpen"
      id="recipe-filters-panel"
      class="card panel"
      role="region"
      :aria-label="$t('recipes.filters')"
    >
      <div class="panel-header">
        <strong>{{ $t('recipes.filters') }}</strong>
        <button type="button" class="secondary close" :aria-label="$t('common.close')" @click="isOpen = false">
          <X :size="16" />
        </button>
      </div>

      <div class="row">
        <div class="field" style="flex: 2; min-width: 200px">
          <label for="search">{{ $t('recipes.search') }}</label>
          <input id="search" v-model="filters.search" :placeholder="$t('recipes.searchPlaceholder')" />
        </div>
        <div class="field">
          <label for="diet_type">{{ $t('recipes.dietFilter') }}</label>
          <select id="diet_type" v-model="filters.diet_type">
            <option value="">{{ $t('recipes.allDiets') }}</option>
            <option value="omnivore">{{ $t('diet.omnivore') }}</option>
            <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
            <option value="vegan">{{ $t('diet.vegan') }}</option>
          </select>
        </div>
        <div class="field">
          <label for="ingredients">{{ $t('recipes.ingredientsFilter') }}</label>
          <input id="ingredients" v-model="filters.ingredients" :placeholder="$t('recipes.ingredientsPlaceholder')" />
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label for="max_prep">{{ $t('recipes.maxPrepTime') }}</label>
          <input id="max_prep" v-model.number="filters.max_prep_time" type="number" min="0" />
        </div>
        <div class="field">
          <label for="max_cook">{{ $t('recipes.maxCookTime') }}</label>
          <input id="max_cook" v-model.number="filters.max_cook_time" type="number" min="0" />
        </div>
        <div class="field checkbox-field">
          <input id="in_season" v-model="filters.in_season" type="checkbox" style="width: auto" />
          <label for="in_season" style="margin: 0">{{ $t('recipes.inSeasonOnly') }}</label>
        </div>
      </div>

      <div class="panel-footer">
        <button type="button" class="secondary" :disabled="!activeCount" @click="reset">
          <RotateCcw :size="16" />{{ $t('recipes.resetFilters') }}
        </button>
        <button type="button" class="apply" @click="isOpen = false">{{ $t('recipes.showResults') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recipe-filters {
  margin-bottom: 1rem;
}
.toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.badge {
  min-width: 1.35rem;
  height: 1.35rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.panel {
  margin-top: 0.75rem;
}
.panel-header,
.backdrop,
.apply {
  display: none;
}
.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
.checkbox-field {
  align-self: center;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

/* Mobile : le même panneau devient un bottom-sheet (pouce à portée, la liste reste visible derrière). */
@media (max-width: 600px) {
  .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgb(0 0 0 / 0.4);
    z-index: 90;
  }
  .panel {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    margin: 0;
    z-index: 100;
    max-height: 85vh;
    overflow-y: auto;
    border-radius: 20px 20px 0 0;
    padding-bottom: calc(1.25rem + env(safe-area-inset-bottom, 0px));
  }
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }
  .apply {
    display: inline-flex;
  }
  .panel-footer {
    justify-content: space-between;
  }
}
</style>
