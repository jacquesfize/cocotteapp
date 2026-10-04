<script setup lang="ts">
import { CookingPot, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseModal from '../../components/shared/BaseModal.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import {
  createCookware,
  deleteCookware,
  listCookware,
  removeCookwareImage,
  updateCookware,
  uploadCookwareImage,
} from '../../api/cookware'
import { getErrorStatus } from '../../utils/apiError'
import { IMAGE_LICENSES, defaultLicenseUrl, imageLicenseLabelKey, requiredCreditFields } from '../../utils/imageCredit'
import type { Cookware } from '../../types/models'

const { t } = useI18n()

// Bibliothèque courte (quelques dizaines d'entrées, non paginée côté API) : chargée en entier
// et filtrée côté client.
const cookware = ref<Cookware[]>([])
const search = ref('')
const isLoading = ref(false)
const message = ref('')

const filtered = computed(() => {
  const term = search.value.trim().toLowerCase()
  if (!term) return cookware.value
  return cookware.value.filter((item) =>
    [item.name, item.translations?.en ?? ''].some((name) => name.toLowerCase().includes(term)),
  )
})

async function load() {
  isLoading.value = true
  try {
    cookware.value = await listCookware()
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

const showModal = ref(false)
const editing = ref<Cookware | null>(null)
const form = ref({ name: '', name_en: '', emoji: '' })
const formError = ref('')
const isSubmitting = ref(false)

// Photo : fichier choisi (envoyé après l'enregistrement), aperçu, et retrait demandé — même
// fonctionnement que les pages thématiques (AdminThematicPagesView.vue).
const imageFile = ref<File | null>(null)
const imagePreview = ref<string | null>(null)
const removeImage = ref(false)
// Crédit de la nouvelle photo : mêmes licences et mêmes champs requis que pour une recette.
const credit = ref({ image_license: '', image_credit_author: '', image_credit_source_url: '' })

function creditError(): string {
  if (!imageFile.value) return ''
  if (!credit.value.image_license) return t('imageCredit.licenseRequired')
  const required = requiredCreditFields(credit.value.image_license)
  if (required.includes('creditAuthor') && !credit.value.image_credit_author.trim()) return t('imageCredit.fieldRequired')
  if (required.includes('creditSourceUrl') && !credit.value.image_credit_source_url.trim()) {
    return t('imageCredit.fieldRequired')
  }
  return ''
}

function onImageChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] ?? null
  imageFile.value = file
  removeImage.value = false
  imagePreview.value = file ? URL.createObjectURL(file) : (editing.value?.image ?? null)
}

function clearImage() {
  imageFile.value = null
  imagePreview.value = null
  removeImage.value = true
}

function openForm(item: Cookware | null) {
  editing.value = item
  form.value = { name: item?.name ?? '', name_en: item?.translations?.en ?? '', emoji: item?.emoji ?? '' }
  imageFile.value = null
  removeImage.value = false
  imagePreview.value = item?.image ?? null
  credit.value = { image_license: '', image_credit_author: '', image_credit_source_url: '' }
  formError.value = ''
  showModal.value = true
}

async function handleSubmit() {
  formError.value = ''
  const name = form.value.name.trim()
  if (!name) {
    formError.value = t('adminCookware.nameRequired')
    return
  }
  const missingCredit = creditError()
  if (missingCredit) {
    formError.value = missingCredit
    return
  }
  // On conserve les autres langues déjà présentes ; seul "en" est édité ici.
  const translations = { ...(editing.value?.translations ?? {}) }
  if (form.value.name_en.trim()) translations.en = form.value.name_en.trim()
  else delete translations.en

  isSubmitting.value = true
  try {
    const payload = { name, translations, emoji: form.value.emoji.trim() }
    const saved = editing.value
      ? await updateCookware(editing.value.id, payload)
      : await createCookware(payload)
    if (imageFile.value) {
      await uploadCookwareImage(saved.id, imageFile.value, {
        ...credit.value,
        image_credit_license_url: defaultLicenseUrl(credit.value.image_license),
      })
    }
    else if (removeImage.value && editing.value?.image) await removeCookwareImage(saved.id)
    showModal.value = false
    message.value = ''
    await load()
  } catch (err) {
    formError.value = t(getErrorStatus(err) === 400 ? 'adminCookware.duplicate' : 'adminCookware.saveError')
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete(item: Cookware) {
  message.value = ''
  if (!confirm(t('adminCookware.deleteConfirm', { name: item.name }))) return
  try {
    await deleteCookware(item.id)
  } catch {
    message.value = t('adminCookware.deleteError')
    return
  }
  await load()
}
</script>

<template>
  <div>
    <div class="row page-header">
      <div>
        <PageHeader :icon="CookingPot" :title="$t('adminCookware.title')" />
        <p class="muted">{{ $t('adminCookware.subtitle') }}</p>
      </div>
      <button type="button" @click="openForm(null)">
        <Plus :size="16" />{{ $t('adminCookware.addButton') }}
      </button>
    </div>

    <div class="field" style="max-width: 320px">
      <label for="admin-cookware-search">{{ $t('adminCookware.search') }}</label>
      <input id="admin-cookware-search" v-model="search" :placeholder="$t('adminCookware.searchPlaceholder')" />
    </div>

    <p v-if="message" class="error" role="alert">{{ message }}</p>
    <AsyncState
      v-if="isLoading || !filtered.length"
      :loading="isLoading"
      :loading-text="$t('common.loading')"
      :empty-text="$t('adminCookware.empty')"
    />

    <div v-else class="card admin-table-wrapper">
      <table class="admin-table">
        <thead>
          <tr>
            <th></th>
            <th>{{ $t('adminCookware.colName') }}</th>
            <th>{{ $t('adminCookware.colNameEn') }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td class="visual">
              <img v-if="item.image" :src="item.image" class="image-thumb" alt="" />
              <span v-else-if="item.emoji" class="emoji" aria-hidden="true">{{ item.emoji }}</span>
            </td>
            <td class="name">
              {{ item.name }}
              <small v-if="item.image && item.image_credit_author" class="muted credit">
                {{ $t('imageCredit.photoBy', { author: item.image_credit_author }) }} ·
                {{ $t(imageLicenseLabelKey(item.image_license)) }}
              </small>
            </td>
            <td :data-label="$t('adminCookware.colNameEn')">{{ item.translations?.en ?? '' }}</td>
            <td class="actions">
              <button class="secondary" @click="openForm(item)">{{ $t('common.edit') }}</button>
              <button
                class="danger icon-btn"
                :aria-label="$t('adminCookware.deleteButton')"
                @click="handleDelete(item)"
              >
                <Trash2 :size="16" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal
      v-if="showModal"
      :title="$t(editing ? 'adminCookware.editTitle' : 'adminCookware.newTitle')"
      @close="showModal = false"
    >
      <form novalidate @submit.prevent="handleSubmit">
        <div class="field">
          <label for="cookware-modal-name">{{ $t('adminCookware.colName') }}</label>
          <input id="cookware-modal-name" v-model="form.name" required autofocus />
        </div>
        <div class="field">
          <label for="cookware-modal-name-en">{{ $t('adminCookware.colNameEn') }}</label>
          <input id="cookware-modal-name-en" v-model="form.name_en" />
        </div>
        <div class="field" style="width: 120px">
          <label for="cookware-modal-emoji">{{ $t('adminCookware.emoji') }}</label>
          <input id="cookware-modal-emoji" v-model="form.emoji" placeholder="🍳" maxlength="8" />
        </div>
        <div class="field">
          <label for="cookware-modal-image">{{ $t('adminCookware.image') }}</label>
          <div class="row" style="align-items: center">
            <img v-if="imagePreview" :src="imagePreview" class="image-preview" alt="" />
            <input id="cookware-modal-image" type="file" accept="image/*" @change="onImageChange" />
            <button v-if="imagePreview" type="button" class="secondary" @click="clearImage">
              {{ $t('adminCookware.imageRemove') }}
            </button>
          </div>
        </div>
        <template v-if="imageFile">
          <div class="field">
            <label for="cookware-modal-license">{{ $t('imageCredit.license') }}</label>
            <select id="cookware-modal-license" v-model="credit.image_license">
              <option value="" disabled>{{ $t('imageCredit.selectLicense') }}</option>
              <option v-for="license in IMAGE_LICENSES" :key="license" :value="license">
                {{ $t(imageLicenseLabelKey(license)) }}
              </option>
            </select>
          </div>
          <div class="row">
            <div class="field" style="flex: 1; min-width: 180px">
              <label for="cookware-modal-author">{{ $t('imageCredit.author') }}</label>
              <input id="cookware-modal-author" v-model="credit.image_credit_author" />
            </div>
            <div class="field" style="flex: 1; min-width: 180px">
              <label for="cookware-modal-source">{{ $t('imageCredit.sourceUrl') }}</label>
              <input id="cookware-modal-source" v-model="credit.image_credit_source_url" type="url" placeholder="https://..." />
            </div>
          </div>
        </template>
        <p v-if="formError" class="error">{{ formError }}</p>
        <div class="row" style="margin-top: 1rem; justify-content: flex-end">
          <button type="button" class="secondary" @click="showModal = false">{{ $t('common.cancel') }}</button>
          <button type="submit" :disabled="isSubmitting">{{ $t('common.save') }}</button>
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

.admin-table .visual {
  width: 3.5rem;
}

.image-thumb {
  display: block;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 8px;
  object-fit: cover;
}

.image-preview {
  width: 4rem;
  height: 4rem;
  border-radius: 10px;
  object-fit: cover;
}

.emoji {
  font-size: 1.5rem;
}

.name .credit {
  display: block;
  font-weight: 400;
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
