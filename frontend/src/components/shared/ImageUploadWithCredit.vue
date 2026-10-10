<script setup lang="ts">
import { ref, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { defaultLicenseUrl, IMAGE_LICENSES, imageLicenseLabelKey, requiredCreditFields } from '../../utils/imageCredit'

// Formulaire partagé pour (dé)poser une image (recette ou étape) avec ses informations de
// crédit/licence. Les 5 champs de crédit ne sont obligatoires que si une licence les requiert
// (voir utils/imageCredit.ts::requiredCreditFields, en miroir de la validation serveur) et
// eux-mêmes ne sont exigés du tout que si l'image change réellement (`originalImageUrl` sert à
// détecter ce changement) — modifier le reste d'une recette existante ne doit jamais réclamer un
// crédit pour une image déjà en place avant cette fonctionnalité (voir CLAUDE.md/spec :
// "grandfathering").
const props = withDefaults(
  defineProps<{
    currentImageUrl?: string | null
    // Valeur de `image_url` telle que chargée depuis l'API, pour détecter un changement.
    originalImageUrl?: string
    compact?: boolean
  }>(),
  { originalImageUrl: '' },
)

const { t } = useI18n()

const file = defineModel<File | null>('file', { default: null })
const imageUrl = defineModel<string>('imageUrl', { default: '' })
const license = defineModel<string>('license', { default: '' })
const creditAuthor = defineModel<string>('creditAuthor', { default: '' })
const creditSourceUrl = defineModel<string>('creditSourceUrl', { default: '' })
const creditLicenseUrl = defineModel<string>('creditLicenseUrl', { default: '' })
const creditNote = defineModel<string>('creditNote', { default: '' })

const errors = ref<Record<string, string>>({})
const uid = useId()

function handleFileChange(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0] || null
}

// Pré-remplissage (éditable) de l'URL de licence pour les licences CC, en miroir du même défaut
// appliqué côté serveur si le champ est laissé vide — pure confort, pas de validation dessus.
watch(license, (value) => {
  if ((value === 'cc_by' || value === 'cc_by_sa') && !creditLicenseUrl.value) {
    creditLicenseUrl.value = defaultLicenseUrl(value)
  }
})

function showAuthor(l: string) {
  return requiredCreditFields(l).includes('creditAuthor')
}
function showSourceUrl(l: string) {
  return requiredCreditFields(l).includes('creditSourceUrl')
}
function showNote(l: string) {
  return requiredCreditFields(l).includes('creditNote') || l === 'unknown'
}
function showLicenseUrl(l: string) {
  return l === 'cc_by' || l === 'cc_by_sa'
}

/** Appelé par le formulaire parent avant soumission ; retourne false et peuple `errors` si la
 * combinaison licence/crédit saisie est invalide. Ne doit rien exiger si l'image n'a pas changé
 * et qu'aucune licence n'a été choisie. */
function validate(): boolean {
  errors.value = {}
  const imageChanged = Boolean(file.value) || imageUrl.value !== props.originalImageUrl
  if (imageChanged && !license.value) {
    errors.value.license = t('imageCredit.licenseRequired')
  }
  if (license.value) {
    if (showAuthor(license.value) && !creditAuthor.value.trim()) {
      errors.value.creditAuthor = t('imageCredit.fieldRequired')
    }
    if (showSourceUrl(license.value) && !creditSourceUrl.value.trim()) {
      errors.value.creditSourceUrl = t('imageCredit.fieldRequired')
    }
    if (requiredCreditFields(license.value).includes('creditNote') && !creditNote.value.trim()) {
      errors.value.creditNote = t('imageCredit.fieldRequired')
    }
  }
  return Object.keys(errors.value).length === 0
}

defineExpose({ validate })
</script>

<template>
  <div class="image-upload-with-credit" :class="{ compact }">
    <div class="row">
      <div class="field" style="flex: 1; min-width: 180px">
        <label :for="`iuwc-url-${uid}`">{{ $t('recipes.imageUrl') }}</label>
        <input :id="`iuwc-url-${uid}`" v-model="imageUrl" type="url" placeholder="https://..." />
      </div>
      <div class="field" style="flex: 1; min-width: 180px">
        <label :for="`iuwc-file-${uid}`">{{ $t('recipes.imageFile') }}</label>
        <input :id="`iuwc-file-${uid}`" type="file" accept="image/*" @change="handleFileChange" />
      </div>
    </div>
    <img v-if="currentImageUrl" :src="currentImageUrl" class="current-image" alt="" />

    <div class="field">
      <label :for="`iuwc-license-${uid}`">{{ $t('imageCredit.license') }}</label>
      <select :id="`iuwc-license-${uid}`" v-model="license">
        <option value="">{{ $t('imageCredit.selectLicense') }}</option>
        <option v-for="l in IMAGE_LICENSES" :key="l" :value="l">{{ $t(imageLicenseLabelKey(l)) }}</option>
      </select>
      <p v-if="errors.license" class="error">{{ errors.license }}</p>
    </div>

    <div v-if="license" class="row">
      <div v-if="showAuthor(license)" class="field" style="flex: 1; min-width: 160px">
        <label :for="`iuwc-author-${uid}`">{{ $t('imageCredit.author') }}</label>
        <input :id="`iuwc-author-${uid}`" v-model="creditAuthor" />
        <p v-if="errors.creditAuthor" class="error">{{ errors.creditAuthor }}</p>
      </div>
      <div v-if="showSourceUrl(license)" class="field" style="flex: 1; min-width: 160px">
        <label :for="`iuwc-source-${uid}`">{{ $t('imageCredit.sourceUrl') }}</label>
        <input :id="`iuwc-source-${uid}`" v-model="creditSourceUrl" type="url" placeholder="https://..." />
        <p v-if="errors.creditSourceUrl" class="error">{{ errors.creditSourceUrl }}</p>
      </div>
    </div>
    <div v-if="license && (showLicenseUrl(license) || showNote(license))" class="row">
      <div v-if="showLicenseUrl(license)" class="field" style="flex: 1; min-width: 160px">
        <label :for="`iuwc-license-url-${uid}`">{{ $t('imageCredit.licenseUrl') }}</label>
        <input :id="`iuwc-license-url-${uid}`" v-model="creditLicenseUrl" type="url" placeholder="https://..." />
      </div>
      <div v-if="showNote(license)" class="field" style="flex: 1; min-width: 160px">
        <label :for="`iuwc-note-${uid}`">{{ $t('imageCredit.note') }}</label>
        <input :id="`iuwc-note-${uid}`" v-model="creditNote" />
        <p v-if="errors.creditNote" class="error">{{ errors.creditNote }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.image-upload-with-credit {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1.5px solid var(--color-border);
  border-radius: 0;
  padding: 1rem;
}

.image-upload-with-credit.compact {
  padding: 0.65rem;
}

.current-image {
  max-width: 220px;
  max-height: 140px;
  object-fit: cover;
  border-radius: 0;
  margin: 0.25rem 0 1rem;
}

.compact .current-image {
  max-width: 120px;
  max-height: 80px;
}
</style>
