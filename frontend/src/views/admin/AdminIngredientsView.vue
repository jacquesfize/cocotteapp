<script setup lang="ts">
import { BadgeCheck, Carrot, GitMerge, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import IngredientEditModal from '../../components/recipes/IngredientEditModal.vue'
import IngredientPicker from '../../components/recipes/IngredientPicker.vue'
import BaseModal from '../../components/shared/BaseModal.vue'
import UnverifiedBadge from '../../components/shared/UnverifiedBadge.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import Pagination from '../../components/shared/Pagination.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import { usePaginatedQuery } from '../../composables/usePaginatedQuery'
import { deleteIngredient, listIngredients, mergeIngredient, updateIngredient } from '../../api/ingredients'
import { getErrorStatus } from '../../utils/apiError'
import type { IngredientListParams } from '../../types/api'
import type { Ingredient } from '../../types/models'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const ingredients = ref<Ingredient[]>([])
const count = ref(0)
const search = ref((route.query.search as string) || '')
const isLoading = ref(false)
const accessDenied = ref(false)
const message = ref('')
// Message de réussite (fusion), distinct des erreurs.
const notice = ref('')
// File de revue : seulement les ingrédients créés par des utilisateurs, pas encore vérifiés.
const unverifiedOnly = ref(route.query.is_verified === 'false')
// Nombre d'ingrédients à vérifier, affiché sur le filtre (`count` d'une requête filtrée).
const unverifiedCount = ref<number | null>(null)

const showModal = ref(false)
const editing = ref<Ingredient | null>(null)

async function load() {
  isLoading.value = true
  try {
    const params: IngredientListParams = {}
    if (search.value) params.search = search.value
    if (page.value > 1) params.page = page.value
    if (unverifiedOnly.value) params.is_verified = false
    const data = await listIngredients(params)
    ingredients.value = data.results
    count.value = data.count
    if (unverifiedOnly.value && !search.value) unverifiedCount.value = data.count
    accessDenied.value = false
    const query: Record<string, string> = {}
    for (const [key, value] of Object.entries(params)) query[key] = String(value)
    router.replace({ query })
  } catch (err) {
    if (getErrorStatus(err) === 403) accessDenied.value = true
  } finally {
    isLoading.value = false
  }
}

const { page, goToPage } = usePaginatedQuery(load, { search })

async function loadUnverifiedCount() {
  try {
    unverifiedCount.value = (await listIngredients({ is_verified: false })).count
  } catch {
    unverifiedCount.value = null
  }
}

onMounted(loadUnverifiedCount)

function toggleUnverified() {
  unverifiedOnly.value = !unverifiedOnly.value
  page.value = 1
  load()
}

async function refresh() {
  await Promise.all([load(), loadUnverifiedCount()])
}

async function handleVerify(ingredient: Ingredient) {
  message.value = ''
  notice.value = ''
  try {
    const updated = await updateIngredient(ingredient.id, { is_verified: true })
    ingredients.value = ingredients.value.map((item) => (item.id === updated.id ? updated : item))
    if (unverifiedCount.value) unverifiedCount.value -= 1
  } catch {
    message.value = t('libraryReview.verifyError')
  }
}

// Fusion d'un doublon dans l'ingrédient à conserver : recettes et listes de courses basculent
// sur la cible, puis le doublon est supprimé (côté API).
const merging = ref<Ingredient | null>(null)
const mergeTarget = ref<Ingredient | null>(null)
const mergeError = ref('')
const isMerging = ref(false)
const mergeTargetIsSource = computed(() => !!mergeTarget.value && mergeTarget.value.id === merging.value?.id)

function openMerge(ingredient: Ingredient) {
  merging.value = ingredient
  mergeTarget.value = null
  mergeError.value = ''
}

async function handleMerge() {
  const source = merging.value
  const target = mergeTarget.value
  if (!source || !target) return
  mergeError.value = ''
  if (mergeTargetIsSource.value) {
    mergeError.value = t('libraryReview.mergeSameItem')
    return
  }
  isMerging.value = true
  try {
    const kept = await mergeIngredient(source.id, target.id)
    merging.value = null
    message.value = ''
    notice.value = t('libraryReview.mergeDone', { name: source.name, target: kept.name })
    if (ingredients.value.length === 1 && page.value > 1) page.value -= 1
    await refresh()
  } catch {
    mergeError.value = t('libraryReview.mergeError')
  } finally {
    isMerging.value = false
  }
}

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
  await refresh()
}

function seasonSummary(ingredient: Ingredient) {
  if (!ingredient.available_months?.length) return t('adminIngredients.allYear')
  // Abréviations de la locale (« juin », « juil. ») : couper les noms à 3 lettres donnait
  // « jui, jui » pour juin et juillet.
  const format = new Intl.DateTimeFormat(locale.value, { month: 'short' })
  return ingredient.available_months.map((m) => format.format(new Date(2000, m - 1, 1))).join(', ')
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
  await refresh()
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
      <div class="row admin-filters">
        <div class="field" style="max-width: 320px; flex: 1; min-width: 200px">
          <label for="admin-ingredient-search">{{ $t('adminIngredients.search') }}</label>
          <input
            id="admin-ingredient-search"
            v-model="search"
            :placeholder="$t('adminIngredients.searchPlaceholder')"
          />
        </div>
        <button
          type="button"
          class="admin-filter-toggle"
          :class="{ 'is-on': unverifiedOnly }"
          :aria-pressed="unverifiedOnly"
          data-testid="filter-unverified"
          @click="toggleUnverified"
        >
          {{ $t('libraryReview.filterUnverified') }}
          <span
            v-if="unverifiedCount !== null"
            class="admin-filter-count"
            :class="{ 'has-items': unverifiedCount }"
            :aria-label="$t('libraryReview.unverifiedCount', { count: unverifiedCount })"
          >{{ unverifiedCount }}</span>
        </button>
      </div>

      <p v-if="message" class="error" role="alert">{{ message }}</p>
      <p v-if="notice" class="muted" role="status">{{ notice }}</p>
      <AsyncState
        v-if="isLoading || !ingredients.length"
        :loading="isLoading"
        :loading-text="$t('common.loading')"
        :empty-text="$t(unverifiedOnly && !search ? 'libraryReview.nothingToReview' : 'adminIngredients.noIngredients')"
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
              <td class="name">
                {{ ingredient.name }}
                <UnverifiedBadge
                  v-if="ingredient.is_verified === false"
                  :created-by="ingredient.created_by_username"
                />
              </td>
              <td :data-label="$t('adminIngredients.colCategory')">{{ $t(`ingredientCategory.${ingredient.category}`) }}</td>
              <td :data-label="$t('adminIngredients.colSeason')">{{ seasonSummary(ingredient) }}</td>
              <td class="actions">
                <div class="row-actions">
                  <button class="secondary btn-sm" @click="openEdit(ingredient)">{{ $t('common.edit') }}</button>
                  <button
                    v-if="ingredient.is_verified === false"
                    class="secondary btn-sm"
                    data-testid="verify"
                    @click="handleVerify(ingredient)"
                  >
                    <BadgeCheck :size="14" />{{ $t('libraryReview.verify') }}
                  </button>
                  <button
                    class="secondary icon-btn btn-sm"
                    data-testid="merge"
                    :aria-label="$t('libraryReview.merge')"
                    :title="$t('libraryReview.merge')"
                    @click="openMerge(ingredient)"
                  >
                    <GitMerge :size="16" />
                  </button>
                  <button
                    class="danger icon-btn btn-sm"
                    :aria-label="$t('adminIngredients.deleteIngredient')"
                    :title="$t('adminIngredients.deleteIngredient')"
                    @click="handleDelete(ingredient)"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
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

    <BaseModal
      v-if="merging"
      :title="$t('libraryReview.mergeTitle', { name: merging.name })"
      @close="merging = null"
    >
      <form novalidate @submit.prevent="handleMerge">
        <div class="field">
          <label for="merge-target">{{ $t('libraryReview.mergeIngredientTarget') }}</label>
          <IngredientPicker id="merge-target" v-model="mergeTarget" select-only />
        </div>
        <p v-if="mergeTargetIsSource" class="error">{{ $t('libraryReview.mergeSameItem') }}</p>
        <p v-else-if="mergeTarget" class="merge-warning" data-testid="merge-confirm">
          {{ $t('libraryReview.mergeIngredientConfirm', { name: merging.name, target: mergeTarget.name }) }}
        </p>
        <p v-if="mergeError" class="error" role="alert">{{ mergeError }}</p>
        <div class="row" style="margin-top: 1rem; justify-content: flex-end">
          <button type="button" class="secondary" @click="merging = null">{{ $t('common.cancel') }}</button>
          <button type="submit" class="danger" :disabled="!mergeTarget || mergeTargetIsSource || isMerging">
            <GitMerge :size="16" />{{ $t('libraryReview.mergeSubmit') }}
          </button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

/* Cellule restée une vraie cellule de tableau (un `display: flex` sur le <td> casse
   l'alignement des bordures) : les boutons vivent dans un conteneur flex, sur une seule ligne. */
.admin-table .actions {
  width: 1%;
  white-space: nowrap;
}

.row-actions {
  display: flex;
  gap: 0.4rem;
  justify-content: flex-end;
  align-items: center;
}

.admin-table .name :deep(.unverified-badge) {
  margin-left: 0.35rem;
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
    width: 100%;
    padding-top: 0.5rem;
  }

  .row-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
