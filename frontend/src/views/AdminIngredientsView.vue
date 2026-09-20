<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import IngredientEditModal from '../components/IngredientEditModal.vue'
import Pagination from '../components/Pagination.vue'
import { deleteIngredient, listIngredients } from '../api/ingredients'
import type { IngredientListParams } from '../types/api'
import type { Ingredient } from '../types/models'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const ingredients = ref<Ingredient[]>([])
const count = ref(0)
const page = ref(Number(route.query.page) || 1)
const search = ref((route.query.search as string) || '')
const isLoading = ref(false)
const accessDenied = ref(false)
const message = ref('')

const showModal = ref(false)
const editing = ref<Ingredient | null>(null)

async function load() {
  isLoading.value = true
  try {
    const params: IngredientListParams = {}
    if (search.value) params.search = search.value
    if (page.value > 1) params.page = page.value
    const data = await listIngredients(params)
    ingredients.value = data.results
    count.value = data.count
    accessDenied.value = false
    router.replace({ query: params as Record<string, string> })
  } catch (err) {
    if ((err as { response?: { status?: number } }).response?.status === 403) accessDenied.value = true
  } finally {
    isLoading.value = false
  }
}

function goToPage(newPage: number) {
  page.value = newPage
  load()
}

let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  page.value = 1
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 300)
})

onMounted(load)

function openCreate() {
  editing.value = null
  showModal.value = true
}

function openEdit(ingredient: Ingredient) {
  editing.value = ingredient
  showModal.value = true
}

async function handleSaved() {
  showModal.value = false
  message.value = ''
  await load()
}

function seasonSummary(ingredient: Ingredient) {
  if (!ingredient.available_months?.length) return t('adminIngredients.allYear')
  return ingredient.available_months.map((m) => t(`ingredientModal.months.${m}`).slice(0, 3)).join(', ')
}

async function handleDelete(ingredient: Ingredient) {
  message.value = ''
  if (!confirm(t('adminIngredients.deleteConfirm', { name: ingredient.name }))) return
  try {
    await deleteIngredient(ingredient.id)
  } catch (err) {
    const status = (err as { response?: { status?: number } }).response?.status
    message.value =
      status === 409
        ? t('adminIngredients.deleteInUse', { name: ingredient.name })
        : t('adminIngredients.deleteError')
    return
  }
  // Évite de rester sur une page devenue vide après suppression du dernier élément.
  if (ingredients.value.length === 1 && page.value > 1) page.value -= 1
  await load()
}
</script>

<template>
  <div>
    <div class="row page-header">
      <div>
        <h1>{{ $t('adminIngredients.title') }}</h1>
        <p class="muted">{{ $t('adminIngredients.subtitle') }}</p>
      </div>
      <button v-if="!accessDenied" type="button" @click="openCreate">
        <Plus :size="16" />{{ $t('adminIngredients.addButton') }}
      </button>
    </div>

    <p v-if="accessDenied" class="error">{{ $t('adminIngredients.accessDenied') }}</p>

    <template v-else>
      <div class="field" style="max-width: 320px">
        <label for="admin-ingredient-search">{{ $t('adminIngredients.search') }}</label>
        <input
          id="admin-ingredient-search"
          v-model="search"
          :placeholder="$t('adminIngredients.searchPlaceholder')"
        />
      </div>

      <p v-if="message" class="error" role="alert">{{ message }}</p>
      <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
      <p v-else-if="!ingredients.length" class="muted">{{ $t('adminIngredients.noIngredients') }}</p>

      <div v-else class="card table-wrapper">
        <table class="admin-table">
          <thead>
            <tr>
              <th>{{ $t('adminIngredients.colName') }}</th>
              <th>{{ $t('adminIngredients.colNameEn') }}</th>
              <th>{{ $t('adminIngredients.colCategory') }}</th>
              <th>{{ $t('adminIngredients.colCalories') }}</th>
              <th>{{ $t('adminIngredients.colCarbon') }}</th>
              <th>{{ $t('adminIngredients.colSeason') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ingredient in ingredients" :key="ingredient.id">
              <td>{{ ingredient.name }}</td>
              <td>{{ ingredient.translations?.en || '—' }}</td>
              <td>{{ $t(`ingredientCategory.${ingredient.category}`) }}</td>
              <td>{{ ingredient.calories_kcal }}</td>
              <td>{{ ingredient.carbon_kg_co2e_per_kg }}</td>
              <td>{{ seasonSummary(ingredient) }}</td>
              <td class="row" style="gap: 0.5rem; flex-wrap: nowrap">
                <button class="secondary" @click="openEdit(ingredient)">{{ $t('common.edit') }}</button>
                <button
                  class="danger icon-btn"
                  :aria-label="$t('adminIngredients.deleteIngredient')"
                  @click="handleDelete(ingredient)"
                >
                  <Trash2 :size="16" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <Pagination :page="page" :count="count" @update:page="goToPage" />
    </template>

    <IngredientEditModal
      v-if="showModal"
      :ingredient="editing"
      advanced
      @created="handleSaved"
      @updated="handleSaved"
      @close="showModal = false"
    />
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.table-wrapper {
  overflow-x: auto;
  padding: 0;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  white-space: nowrap;
}

.admin-table th,
.admin-table td {
  text-align: left;
  padding: 0.85rem 1.25rem;
}

.admin-table thead th {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-muted);
  border-bottom: 1px solid var(--color-border);
}

.admin-table tbody tr:not(:last-child) td {
  border-bottom: 1px solid var(--color-border);
}
</style>
