<script setup lang="ts">
import { Trash2 } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseModal from '../shared/BaseModal.vue'
import UnverifiedBadge from '../shared/UnverifiedBadge.vue'
import { deleteCookware, updateCookware } from '../../api/cookware'
import { getErrorStatus } from '../../utils/apiError'
import type { Cookware } from '../../types/models'

// Correction d'un matériel depuis le formulaire de recette, par son auteur tant qu'il n'est pas
// vérifié (ou par un admin) — `can_edit` de l'API. Nom, nom anglais et emoji seulement : la photo
// et son crédit restent gérés dans l'administration (AdminCookwareView.vue).
const props = defineProps<{
  cookware: Cookware
}>()
const emit = defineEmits<{
  updated: [cookware: Cookware]
  deleted: [id: number]
  close: []
}>()

const { t } = useI18n()

const form = ref({
  name: props.cookware.name,
  name_en: props.cookware.translations?.en ?? '',
  emoji: props.cookware.emoji ?? '',
})
const error = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  error.value = ''
  const name = form.value.name.trim()
  if (!name) {
    error.value = t('adminCookware.nameRequired')
    return
  }
  // On conserve les autres langues déjà présentes ; seul "en" est édité ici.
  const translations = { ...(props.cookware.translations ?? {}) }
  if (form.value.name_en.trim()) translations.en = form.value.name_en.trim()
  else delete translations.en
  isSubmitting.value = true
  try {
    emit('updated', await updateCookware(props.cookware.id, { name, translations, emoji: form.value.emoji.trim() }))
  } catch (err) {
    error.value = t(getErrorStatus(err) === 400 ? 'adminCookware.duplicate' : 'adminCookware.saveError')
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete() {
  error.value = ''
  if (!confirm(t('cookware.deleteConfirm', { name: props.cookware.name }))) return
  isSubmitting.value = true
  try {
    await deleteCookware(props.cookware.id)
    emit('deleted', props.cookware.id)
  } catch {
    error.value = t('adminCookware.deleteError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <BaseModal :title="t('adminCookware.editTitle')" @close="emit('close')">
    <form novalidate @submit.prevent="handleSubmit">
      <p v-if="cookware.is_verified === false" class="review-status">
        <UnverifiedBadge />
        <span class="muted">{{ t('libraryReview.unverifiedTooltip') }}</span>
      </p>
      <div class="field">
        <label for="cookware-edit-name">{{ t('adminCookware.colName') }}</label>
        <input id="cookware-edit-name" v-model="form.name" required autofocus />
      </div>
      <div class="field">
        <label for="cookware-edit-name-en">{{ t('adminCookware.colNameEn') }}</label>
        <input id="cookware-edit-name-en" v-model="form.name_en" />
      </div>
      <div class="field" style="width: 120px">
        <label for="cookware-edit-emoji">{{ t('adminCookware.emoji') }}</label>
        <input id="cookware-edit-emoji" v-model="form.emoji" placeholder="🍳" maxlength="8" />
      </div>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="row" style="margin-top: 1rem; justify-content: flex-end">
        <button
          type="button"
          class="danger modal-delete"
          data-testid="cookware-edit-delete"
          :disabled="isSubmitting"
          @click="handleDelete"
        >
          <Trash2 :size="16" />{{ t('cookware.delete') }}
        </button>
        <button type="button" class="secondary" @click="emit('close')">{{ t('common.cancel') }}</button>
        <button type="submit" :disabled="isSubmitting">{{ t('common.save') }}</button>
      </div>
    </form>
  </BaseModal>
</template>

<style scoped>
.review-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem;
  font-size: 0.85rem;
}

.review-status .muted {
  margin: 0;
}

.modal-delete {
  margin-right: auto;
}
</style>
