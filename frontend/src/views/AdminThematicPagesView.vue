<script setup lang="ts">
import { LayoutGrid, Plus, Trash2 } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/PageHeader.vue'
import AsyncState from '../components/shared/AsyncState.vue'
import {
  createThematicPage,
  deleteThematicPage,
  listThematicPages,
  removeThematicPageImage,
  updateThematicPage,
  uploadThematicPageImage,
} from '../api/adminThematicPages'
import { getErrorStatus } from '../utils/apiError'
import type { AdminThematicPageInput } from '../types/api'
import type { AdminThematicPage } from '../types/models'
import type { DietType } from '../types/models'

const { t } = useI18n()

const pages = ref<AdminThematicPage[]>([])
const isLoading = ref(false)
const accessDenied = ref(false)

const showForm = ref(false)
const editingId = ref<number | null>(null)
const error = ref('')
const isSubmitting = ref(false)

interface FormState {
  title: string
  description: string
  icon: string
  order: number
  is_active: boolean
  diet_type: DietType | ''
  in_season: boolean
  ingredients: string
  max_prep_time: string
  max_cook_time: string
  advancedFilters: string
}

function emptyForm(): FormState {
  return {
    title: '',
    description: '',
    icon: '',
    order: 0,
    is_active: true,
    diet_type: '',
    in_season: false,
    ingredients: '',
    max_prep_time: '',
    max_cook_time: '',
    advancedFilters: '',
  }
}

const form = ref<FormState>(emptyForm())

// Image : fichier choisi (envoyé après l'enregistrement de la page), aperçu, et retrait demandé.
const imageFile = ref<File | null>(null)
const imagePreview = ref<string | null>(null)
const removeImage = ref(false)

function onImageChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] ?? null
  imageFile.value = file
  removeImage.value = false
  imagePreview.value = file ? URL.createObjectURL(file) : editingImage.value
}

const editingImage = ref<string | null>(null)

function clearImage() {
  imageFile.value = null
  imagePreview.value = null
  removeImage.value = true
}

function resetImageState(current: string | null) {
  imageFile.value = null
  removeImage.value = false
  editingImage.value = current
  imagePreview.value = current
}

// Clés reconnues par les sélecteurs structurés ci-dessous — si les filtres d'une page en
// contiennent d'autres (saisis via l'admin Django, ou l'éditeur JSON avancé), on les affiche
// telles quelles dans le textarea avancé plutôt que d'en perdre une partie silencieusement.
const KNOWN_FILTER_KEYS = ['diet_type', 'in_season', 'ingredients', 'max_prep_time', 'max_cook_time']

async function load() {
  isLoading.value = true
  try {
    pages.value = await listThematicPages()
    accessDenied.value = false
  } catch (err) {
    if (getErrorStatus(err) === 403) accessDenied.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

function summarizeFilters(filters: Record<string, string>) {
  const entries = Object.entries(filters || {})
  if (!entries.length) return t('adminThematicPages.noFilters')
  return entries.map(([key, value]) => `${key}=${value}`).join(', ')
}

function openCreateForm() {
  editingId.value = null
  form.value = emptyForm()
  resetImageState(null)
  error.value = ''
  showForm.value = true
}

function openEditForm(page: AdminThematicPage) {
  editingId.value = page.id
  resetImageState(page.image)
  error.value = ''
  const filters = page.filters || {}
  const hasUnknownKeys = Object.keys(filters).some((key) => !KNOWN_FILTER_KEYS.includes(key))
  form.value = {
    title: page.title,
    description: page.description,
    icon: page.icon,
    order: page.order,
    is_active: page.is_active,
    diet_type: hasUnknownKeys ? '' : ((filters.diet_type as DietType) || ''),
    in_season: !hasUnknownKeys && filters.in_season === 'true',
    ingredients: hasUnknownKeys ? '' : filters.ingredients || '',
    max_prep_time: hasUnknownKeys ? '' : filters.max_prep_time || '',
    max_cook_time: hasUnknownKeys ? '' : filters.max_cook_time || '',
    advancedFilters: hasUnknownKeys ? JSON.stringify(filters, null, 2) : '',
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  error.value = ''
}

function buildFilters(): Record<string, string> | null {
  if (form.value.advancedFilters.trim()) {
    try {
      return JSON.parse(form.value.advancedFilters)
    } catch {
      return null
    }
  }
  const filters: Record<string, string> = {}
  if (form.value.diet_type) filters.diet_type = form.value.diet_type
  if (form.value.in_season) filters.in_season = 'true'
  if (form.value.ingredients.trim()) filters.ingredients = form.value.ingredients.trim()
  if (form.value.max_prep_time !== '') filters.max_prep_time = String(form.value.max_prep_time)
  if (form.value.max_cook_time !== '') filters.max_cook_time = String(form.value.max_cook_time)
  return filters
}

async function handleSubmit() {
  error.value = ''
  const filters = buildFilters()
  if (filters === null) {
    error.value = t('adminThematicPages.advancedFiltersInvalid')
    return
  }

  const payload: AdminThematicPageInput = {
    title: form.value.title,
    description: form.value.description,
    icon: form.value.icon,
    order: form.value.order,
    is_active: form.value.is_active,
    filters,
  }

  isSubmitting.value = true
  try {
    const saved = editingId.value
      ? await updateThematicPage(editingId.value, payload)
      : await createThematicPage(payload)
    if (imageFile.value) await uploadThematicPageImage(saved.id, imageFile.value)
    else if (removeImage.value) await removeThematicPageImage(saved.id)
    showForm.value = false
    await load()
  } catch {
    error.value = t('adminThematicPages.saveError')
  } finally {
    isSubmitting.value = false
  }
}

async function toggleActive(page: AdminThematicPage) {
  page.is_active = await updateThematicPage(page.id, { is_active: !page.is_active }).then(
    (p) => p.is_active,
  )
}

async function handleDelete(page: AdminThematicPage) {
  if (!confirm(t('adminThematicPages.deleteConfirm', { title: page.title }))) return
  await deleteThematicPage(page.id)
  await load()
}
</script>

<template>
  <div>
    <div class="row page-header">
      <div>
        <PageHeader :icon="LayoutGrid" :title="$t('adminThematicPages.title')" />
        <p class="muted">{{ $t('adminThematicPages.subtitle') }}</p>
      </div>
      <button v-if="!accessDenied" type="button" @click="openCreateForm">
        <Plus :size="16" />{{ $t('adminThematicPages.addButton') }}
      </button>
    </div>

    <p v-if="accessDenied" class="error">{{ $t('adminThematicPages.accessDenied') }}</p>

    <template v-else>
      <div v-if="showForm" class="card" style="margin-bottom: 1rem">
        <h2>{{ editingId ? $t('adminThematicPages.editTitle') : $t('adminThematicPages.newTitle') }}</h2>
        <form @submit.prevent="handleSubmit">
          <div class="row">
            <div class="field" style="flex: 2; min-width: 220px">
              <label for="tp-title">{{ $t('adminThematicPages.formTitle') }}</label>
              <input id="tp-title" v-model="form.title" required />
            </div>
            <div class="field" style="width: 120px">
              <label for="tp-icon">{{ $t('adminThematicPages.formIcon') }}</label>
              <input
                id="tp-icon"
                v-model="form.icon"
                :placeholder="$t('adminThematicPages.formIconPlaceholder')"
                maxlength="8"
              />
            </div>
            <div class="field" style="width: 120px">
              <label for="tp-order">{{ $t('adminThematicPages.formOrder') }}</label>
              <input id="tp-order" v-model.number="form.order" type="number" min="0" />
            </div>
          </div>
          <div class="field">
            <label for="tp-image">{{ $t('adminThematicPages.formImage') }}</label>
            <div class="row" style="align-items: center">
              <img v-if="imagePreview" :src="imagePreview" class="image-preview" alt="" />
              <input id="tp-image" type="file" accept="image/*" @change="onImageChange" />
              <button v-if="imagePreview" type="button" class="secondary" @click="clearImage">
                {{ $t('adminThematicPages.formImageRemove') }}
              </button>
            </div>
          </div>
          <div class="field">
            <label for="tp-description">{{ $t('adminThematicPages.formDescription') }}</label>
            <textarea id="tp-description" v-model="form.description" rows="2" />
          </div>
          <div class="field checkbox-field">
            <input id="tp-active" v-model="form.is_active" type="checkbox" style="width: auto" />
            <label for="tp-active" style="margin: 0">{{ $t('adminThematicPages.formIsActive') }}</label>
          </div>

          <h3>{{ $t('adminThematicPages.filtersSectionTitle') }}</h3>
          <div class="row">
            <div class="field">
              <label for="tp-diet">{{ $t('adminThematicPages.filterDietType') }}</label>
              <select id="tp-diet" v-model="form.diet_type">
                <option value="">{{ $t('adminThematicPages.filterAnyDiet') }}</option>
                <option value="omnivore">{{ $t('diet.omnivore') }}</option>
                <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
                <option value="vegan">{{ $t('diet.vegan') }}</option>
              </select>
            </div>
            <div class="field">
              <label for="tp-max-prep">{{ $t('adminThematicPages.filterMaxPrepTime') }}</label>
              <input id="tp-max-prep" v-model="form.max_prep_time" type="number" min="0" />
            </div>
            <div class="field">
              <label for="tp-max-cook">{{ $t('adminThematicPages.filterMaxCookTime') }}</label>
              <input id="tp-max-cook" v-model="form.max_cook_time" type="number" min="0" />
            </div>
            <div class="field checkbox-field">
              <input id="tp-in-season" v-model="form.in_season" type="checkbox" style="width: auto" />
              <label for="tp-in-season" style="margin: 0">{{ $t('adminThematicPages.filterInSeason') }}</label>
            </div>
          </div>
          <div class="field">
            <label for="tp-ingredients">{{ $t('adminThematicPages.filterIngredients') }}</label>
            <input
              id="tp-ingredients"
              v-model="form.ingredients"
              :placeholder="$t('adminThematicPages.filterIngredientsPlaceholder')"
            />
          </div>
          <div class="field">
            <label for="tp-advanced">{{ $t('adminThematicPages.advancedFilters') }}</label>
            <textarea id="tp-advanced" v-model="form.advancedFilters" rows="3" />
            <p class="muted" style="font-size: 0.8rem">{{ $t('adminThematicPages.advancedFiltersHint') }}</p>
          </div>

          <p v-if="error" class="error">{{ error }}</p>
          <div class="row">
            <button type="submit" :disabled="isSubmitting">{{ $t('common.save') }}</button>
            <button type="button" class="secondary" @click="closeForm">
              {{ $t('adminThematicPages.cancelEdit') }}
            </button>
          </div>
        </form>
      </div>

      <AsyncState
        v-if="isLoading || !pages.length"
        :loading="isLoading"
        :loading-text="$t('common.loading')"
        :empty-text="$t('adminThematicPages.noPages')"
      />

      <div v-else class="card admin-table-wrapper">
        <table class="admin-table admin-table--scroll">
          <thead>
            <tr>
              <th>{{ $t('adminThematicPages.colImage') }}</th>
              <th>{{ $t('adminThematicPages.colTitle') }}</th>
              <th>{{ $t('adminThematicPages.colOrder') }}</th>
              <th>{{ $t('adminThematicPages.colFilters') }}</th>
              <th>{{ $t('adminThematicPages.colActive') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="page in pages" :key="page.id">
              <td>
                <img v-if="page.image" :src="page.image" class="image-thumb" alt="" />
                <span v-else>{{ page.icon }}</span>
              </td>
              <td>{{ page.title }}</td>
              <td>{{ page.order }}</td>
              <td>{{ summarizeFilters(page.filters) }}</td>
              <td>
                <button class="secondary" @click="toggleActive(page)">
                  {{ page.is_active ? $t('adminThematicPages.active') : $t('adminThematicPages.inactive') }}
                </button>
              </td>
              <td class="row" style="gap: 0.5rem; flex-wrap: nowrap">
                <button class="secondary" @click="openEditForm(page)">
                  {{ $t('common.edit') }}
                </button>
                <button
                  class="danger icon-btn"
                  :aria-label="$t('adminThematicPages.deletePage')"
                  @click="handleDelete(page)"
                >
                  <Trash2 :size="16" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.image-preview,
.image-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 10px;
}

.checkbox-field {
  align-self: center;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.admin-table-wrapper {
  overflow-x: auto;
}

.admin-table--scroll {
  white-space: nowrap;
}
</style>
