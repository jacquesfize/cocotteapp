<script setup lang="ts">
import { Carrot, Plus, Trash2 } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import IngredientEditModal from '../components/IngredientEditModal.vue'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import AsyncState from '../components/shared/AsyncState.vue'
import { usePaginatedQuery } from '../composables/usePaginatedQuery'
import { deleteIngredient, listIngredients } from '../api/ingredients'
import { getErrorStatus } from '../utils/apiError'
import type { IngredientListParams } from '../types/api'
import type { Ingredient } from '../types/models'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const ingredients = ref<Ingredient[]>([])
const count = ref(0)
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
    if (getErrorStatus(err) === 403) accessDenied.value = true
  } finally {
    isLoading.value = false
  }
}

const { page, goToPage } = usePaginatedQuery(load, { search })

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
    const status = getErrorStatus(err)
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
        <PageHeader :icon="Carrot" :title="$t('adminIngredients.title')" />
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
      <AsyncState
        v-if="isLoading || !ingredients.length"
        :loading="isLoading"
        :loading-text="$t('common.loading')"
        :empty-text="$t('adminIngredients.noIngredients')"
      />

      <div v-else class="card admin-table-wrapper">
        <table class="admin-table">
          <thead>
            <tr>
              <th>{{ $t('adminIngredients.colName') }}</th>
              <th>{{ $t('adminIngredients.colCategory') }}</th>
              <th>{{ $t('adminIngredients.colSeason') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ingredient in ingredients" :key="ingredient.id">
              <td class="name">{{ ingredient.name }}</td>
              <td :data-label="$t('adminIngredients.colCategory')">{{ $t(`ingredientCategory.${ingredient.category}`) }}</td>
              <td :data-label="$t('adminIngredients.colSeason')">{{ seasonSummary(ingredient) }}</td>
              <td class="actions">
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

.admin-table .actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

@media (max-width: 600px) {
  .admin-table thead {
    display: none;
  }

  .admin-table,
  .admin-table tbody,
  .admin-table tr,
  .admin-table td {
    display: block;
    width: 100%;
  }

  .admin-table tbody tr {
    padding: 0.75rem 1rem;
  }

  .admin-table tbody tr:not(:last-child) {
    border-bottom: 1px solid var(--color-border);
  }

  .admin-table th,
  .admin-table td {
    padding: 0.2rem 0;
  }

  .admin-table tbody tr:not(:last-child) td {
    border-bottom: none;
  }

  .admin-table .name {
    font-weight: 600;
  }

  .admin-table td[data-label]::before {
    content: attr(data-label) ' : ';
    color: var(--color-muted);
  }

  .admin-table .actions {
    justify-content: flex-start;
    padding-top: 0.5rem;
  }
}
</style>
