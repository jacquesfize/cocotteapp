<script setup lang="ts">
import { Download, Save, Trash2, Upload, User } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { listAllergens } from '../../api/allergens'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import PageHeader from '../../components/shared/PageHeader.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import BaseModal from '../../components/shared/BaseModal.vue'
import { changePassword, exportMyData } from '../../api/auth'
import { getErrorData, getErrorDetail } from '../../utils/apiError'
import { exportRecipeLibrary, importRecipeLibrary, type RecipeArchiveImportResult } from '../../api/recipes'
import { createOrUpdatePlanningShare, deletePlanningShare, listPlanningShares } from '../../api/planning'
import { useAuthStore } from '../../stores/auth'
import { allergenEmoji } from '../../utils/allergens'
import { ACCENT_PRESETS, accentColor, DEFAULT_ACCENT, resetAccentColor, setAccentColor } from '../../utils/theme'
import { downloadBlob } from '../../utils/download'
import type { ActivityLevel, Allergen, DietType, PlanningPermission, PlanningShare, User as UserModel } from '../../types/models'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const appVersion = __APP_VERSION__

const profile = ref<{
  username: string
  email: string
  diet_type: DietType
  activity_level: ActivityLevel
  allergies: string[]
  intolerances: string[]
}>({
  username: '',
  email: '',
  diet_type: 'omnivore',
  activity_level: 'moderate',
  allergies: [],
  intolerances: [],
})

function fillHealthFields(user: UserModel | null) {
  profile.value.diet_type = user?.diet_type || 'omnivore'
  profile.value.activity_level = user?.activity_level || 'moderate'
  profile.value.allergies = [...(user?.allergies || [])]
  profile.value.intolerances = [...(user?.intolerances || [])]
}

// Après un rechargement de page, authStore.user arrive de façon asynchrone (fetchMe()) : on
// remplit le formulaire à son arrivée, mais pas si l'utilisateur a déjà commencé à le modifier.
const profileTouched = ref(false)
watch(
  () => authStore.user?.id,
  () => {
    const user = authStore.user
    if (!user || profileTouched.value) return
    profile.value.username = user.username || ''
    profile.value.email = user.email || ''
    fillHealthFields(user)
  },
  { immediate: true },
)

// Régime, activité et allergies relèvent des données de santé : sans consentement, le serveur
// refuse de les enregistrer, on les verrouille donc dans le formulaire.
const hasHealthConsent = computed(() => !!authStore.user?.health_data_consent_at)

const allergenList = ref<Allergen[]>([])
onMounted(async () => {
  // Liste de référence : sans elle (hors ligne, erreur), la section reste simplement vide.
  allergenList.value = await listAllergens().catch(() => [])
})

// Un allergène est soit une allergie, soit une intolérance : cocher l'un décoche l'autre.
function toggleAllergen(kind: 'allergies' | 'intolerances', slug: string, checked: boolean) {
  const other = kind === 'allergies' ? 'intolerances' : 'allergies'
  const current = profile.value[kind].filter((s) => s !== slug)
  if (checked) {
    current.push(slug)
    profile.value[other] = profile.value[other].filter((s) => s !== slug)
  }
  profile.value[kind] = current
}
const profileMessage = ref('')
const profileError = ref('')
const isSavingProfile = ref(false)

async function handleProfileSubmit() {
  profileMessage.value = ''
  profileError.value = ''
  isSavingProfile.value = true
  try {
    const { diet_type, activity_level, allergies, intolerances, ...identity } = profile.value
    await authStore.updateProfile(
      hasHealthConsent.value ? { ...identity, diet_type, activity_level, allergies, intolerances } : identity,
    )
    profileMessage.value = t('account.profileSuccess')
  } catch (err) {
    const data = getErrorData<{ username?: string[] }>(err)
    profileError.value = data?.username?.[0] || t('account.profileError')
  } finally {
    isSavingProfile.value = false
  }
}

const passwordForm = ref({ old_password: '', new_password: '', confirm_password: '' })
const passwordMessage = ref('')
const passwordError = ref('')
const isChangingPassword = ref(false)

async function handlePasswordSubmit() {
  passwordMessage.value = ''
  passwordError.value = ''
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordError.value = t('account.passwordMismatch')
    return
  }
  isChangingPassword.value = true
  try {
    await changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
    })
    passwordMessage.value = t('account.passwordSuccess')
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    setTimeout(() => {
      authStore.logout()
      router.push({ name: 'login' })
    }, 1500)
  } catch {
    passwordError.value = t('account.passwordError')
  } finally {
    isChangingPassword.value = false
  }
}

const consentError = ref('')
const isUpdatingConsent = ref(false)

async function handleConsent(consent: boolean) {
  if (!consent && !window.confirm(t('account.consentWithdrawConfirm'))) return
  consentError.value = ''
  isUpdatingConsent.value = true
  try {
    await authStore.setHealthConsent(consent)
    // Retirer le consentement efface régime, activité et allergies côté serveur.
    fillHealthFields(authStore.user)
  } catch {
    consentError.value = t('account.consentError')
  } finally {
    isUpdatingConsent.value = false
  }
}

const isExporting = ref(false)

async function handleExport() {
  isExporting.value = true
  try {
    const blob = await exportMyData()
    downloadBlob(blob, `cocotte-donnees-${new Date().toISOString().slice(0, 10)}.zip`)
  } finally {
    isExporting.value = false
  }
}

const isExportingRecipes = ref(false)

async function handleRecipesExport(scope: 'mine' | 'all') {
  isExportingRecipes.value = true
  try {
    const blob = await exportRecipeLibrary(scope)
    const name = scope === 'all' ? 'cocotte-base-recettes' : 'cocotte-recettes'
    downloadBlob(blob, `${name}-${new Date().toISOString().slice(0, 10)}.zip`)
  } finally {
    isExportingRecipes.value = false
  }
}

const recipesFileInput = ref<HTMLInputElement | null>(null)
const isImportingRecipes = ref(false)
const recipesImportResult = ref<RecipeArchiveImportResult | null>(null)
const recipesImportError = ref('')

async function handleRecipesImport(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  recipesImportResult.value = null
  recipesImportError.value = ''
  isImportingRecipes.value = true
  try {
    recipesImportResult.value = await importRecipeLibrary(file)
  } catch (err) {
    recipesImportError.value = getErrorDetail(err, t('account.recipesImportError'))
  } finally {
    isImportingRecipes.value = false
    input.value = ''
  }
}

const shares = ref<PlanningShare[]>([])
const shareForm = ref<{ email: string; permission: PlanningPermission }>({ email: '', permission: 'read' })
const shareMessage = ref('')
const shareError = ref('')
const isSharing = ref(false)

async function loadShares() {
  shares.value = await listPlanningShares()
}

onMounted(loadShares)

async function handleShareSubmit() {
  shareMessage.value = ''
  shareError.value = ''
  isSharing.value = true
  try {
    await createOrUpdatePlanningShare({ email: shareForm.value.email, permission: shareForm.value.permission })
    shareMessage.value = t('account.shareSuccess')
    shareForm.value.email = ''
    await loadShares()
  } catch {
    shareError.value = t('account.shareError')
  } finally {
    isSharing.value = false
  }
}

async function handleRevokeShare(share: PlanningShare) {
  if (!confirm(t('account.shareRevokeConfirm'))) return
  await deletePlanningShare(share.id)
  await loadShares()
}

const deleteError = ref('')
const keepRecipes = ref(false)
const showDeleteConfirm = ref(false)
const isDeletingAccount = ref(false)

async function handleDeleteAccount() {
  deleteError.value = ''
  isDeletingAccount.value = true
  try {
    await authStore.deleteAccount(keepRecipes.value)
    showDeleteConfirm.value = false
    router.push({ name: 'home' })
  } catch {
    deleteError.value = t('account.deleteAccountError')
  } finally {
    isDeletingAccount.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :icon="User" :title="$t('account.title')" />

    <div class="card" style="margin-bottom: 1rem" data-testid="appearance-card">
      <h2>{{ $t('theme.title') }}</h2>
      <p class="muted">{{ $t('theme.accentHelp') }}</p>
      <div class="accent-row" role="group" :aria-label="$t('theme.accent')">
        <button
          v-for="preset in ACCENT_PRESETS"
          :key="preset"
          type="button"
          class="swatch"
          :class="{ 'is-selected': accentColor === preset }"
          :style="{ background: preset }"
          :aria-label="preset"
          :aria-pressed="accentColor === preset"
          @click="setAccentColor(preset)"
        />
        <label class="swatch-custom">
          <input
            type="color"
            :value="accentColor"
            :aria-label="$t('theme.customAccent')"
            data-testid="accent-input"
            @input="setAccentColor(($event.target as HTMLInputElement).value)"
          />
          <span>{{ $t('theme.customAccent') }}</span>
        </label>
        <button
          v-if="accentColor !== DEFAULT_ACCENT"
          type="button"
          class="secondary"
          data-testid="accent-reset"
          @click="resetAccentColor"
        >
          {{ $t('theme.reset') }}
        </button>
      </div>
    </div>

    <div class="card" style="margin-bottom: 1rem">
      <h2>{{ $t('account.profileTitle') }}</h2>
      <form @submit.prevent="handleProfileSubmit" @input="profileTouched = true">
        <div class="row">
          <div class="field" style="flex: 1; min-width: 200px">
            <label for="account-username">{{ $t('auth.username') }}</label>
            <input id="account-username" v-model="profile.username" required autocomplete="username" />
          </div>
          <div class="field" style="flex: 1; min-width: 200px">
            <label for="account-email">{{ $t('auth.email') }}</label>
            <input id="account-email" v-model="profile.email" type="email" required autocomplete="email" />
          </div>
        </div>
        <div v-if="!hasHealthConsent" class="health-locked" data-testid="health-locked">
          <p>{{ $t('account.healthFieldsLocked') }}</p>
          <button type="button" :disabled="isUpdatingConsent" @click="handleConsent(true)">
            {{ $t('account.consentGrant') }}
          </button>
          <p v-if="consentError" class="error">{{ consentError }}</p>
        </div>
        <fieldset class="health-fieldset" :disabled="!hasHealthConsent" data-testid="health-fields">
          <div class="row">
            <div class="field">
              <label for="account-diet">{{ $t('auth.dietType') }}</label>
              <select id="account-diet" v-model="profile.diet_type">
                <option value="omnivore">{{ $t('diet.omnivore') }}</option>
                <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
                <option value="vegan">{{ $t('diet.vegan') }}</option>
              </select>
            </div>
            <div class="field">
              <label for="account-activity">{{ $t('auth.activityLevel') }}</label>
              <select id="account-activity" v-model="profile.activity_level">
                <option value="sedentary">{{ $t('activityLevel.sedentary') }}</option>
                <option value="moderate">{{ $t('activityLevel.moderate') }}</option>
                <option value="athlete">{{ $t('activityLevel.athlete') }}</option>
              </select>
            </div>
          </div>
          <fieldset class="allergen-fieldset">
            <legend>{{ $t('allergens.title') }}</legend>
            <p class="muted">{{ $t('allergens.hint') }}</p>
            <div v-for="kind in (['allergies', 'intolerances'] as const)" :key="kind" class="allergen-group">
              <strong>{{ $t(`allergens.${kind}`) }}</strong>
              <div class="allergen-options">
                <label v-for="allergen in allergenList" :key="allergen.slug" class="allergen-option">
                  <input
                    type="checkbox"
                    :data-testid="`${kind}-${allergen.slug}`"
                    :checked="profile[kind].includes(allergen.slug)"
                    @change="toggleAllergen(kind, allergen.slug, ($event.target as HTMLInputElement).checked)"
                  />
                  <span aria-hidden="true">{{ allergenEmoji(allergen.slug) }}</span>
                  {{ $t(`allergen.${allergen.slug}`) }}
                </label>
              </div>
            </div>
          </fieldset>
        </fieldset>
        <p v-if="profileMessage" class="muted">{{ profileMessage }}</p>
        <p v-if="profileError" class="error">{{ profileError }}</p>
        <button type="submit" :disabled="isSavingProfile"><Save :size="16" />{{ $t('common.save') }}</button>
      </form>
    </div>

    <div class="card" style="margin-bottom: 1rem">
      <h2>{{ $t('account.passwordTitle') }}</h2>
      <form @submit.prevent="handlePasswordSubmit">
        <div class="field">
          <label for="old-password">{{ $t('account.oldPassword') }}</label>
          <input
            id="old-password"
            v-model="passwordForm.old_password"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>
        <div class="row">
          <div class="field" style="flex: 1; min-width: 200px">
            <label for="new-password">{{ $t('account.newPassword') }}</label>
            <input
              id="new-password"
              v-model="passwordForm.new_password"
              type="password"
              minlength="8"
              required
              autocomplete="new-password"
            />
          </div>
          <div class="field" style="flex: 1; min-width: 200px">
            <label for="confirm-password">{{ $t('account.confirmPassword') }}</label>
            <input
              id="confirm-password"
              v-model="passwordForm.confirm_password"
              type="password"
              minlength="8"
              required
              autocomplete="new-password"
            />
          </div>
        </div>
        <p v-if="passwordMessage" class="muted">{{ passwordMessage }}</p>
        <p v-if="passwordError" class="error">{{ passwordError }}</p>
        <button type="submit" :disabled="isChangingPassword">{{ $t('account.changePassword') }}</button>
      </form>
    </div>

    <div class="card" style="margin-bottom: 1rem" data-testid="consent-card">
      <h2>{{ $t('account.consentTitle') }}</h2>
      <p class="muted">
        {{
          authStore.user?.health_data_consent_at
            ? $t('account.consentGranted', {
                date: new Date(authStore.user.health_data_consent_at).toLocaleDateString($i18n.locale),
              })
            : $t('account.consentMissing')
        }}
      </p>
      <p v-if="consentError" class="error">{{ consentError }}</p>
      <div class="row" style="align-items: center">
        <button
          v-if="authStore.user?.health_data_consent_at"
          class="secondary"
          :disabled="isUpdatingConsent"
          @click="handleConsent(false)"
        >
          {{ $t('account.consentWithdraw') }}
        </button>
        <button v-else class="secondary" :disabled="isUpdatingConsent" @click="handleConsent(true)">
          {{ $t('account.consentGrant') }}
        </button>
        <RouterLink :to="{ name: 'privacy' }">{{ $t('account.privacyLink') }}</RouterLink>
      </div>
    </div>

    <div class="card" style="margin-bottom: 1rem">
      <h2>{{ $t('account.exportTitle') }}</h2>
      <p class="muted">{{ $t('account.exportDescription') }}</p>
      <button class="secondary" :disabled="isExporting" @click="handleExport">
        <Download :size="16" />{{ $t('account.exportButton') }}
      </button>
    </div>

    <div class="card" style="margin-bottom: 1rem" data-testid="recipes-transfer-card">
      <h2>{{ $t('account.recipesTransferTitle') }}</h2>
      <p class="muted">{{ $t('account.recipesTransferDescription') }}</p>
      <div class="row">
        <button class="secondary" :disabled="isExportingRecipes" @click="handleRecipesExport('mine')">
          <Download :size="16" />{{ $t('account.recipesExportButton') }}
        </button>
        <button
          v-if="authStore.user?.is_staff"
          class="secondary"
          :disabled="isExportingRecipes"
          data-testid="recipes-export-all"
          @click="handleRecipesExport('all')"
        >
          <Download :size="16" />{{ $t('account.recipesExportAllButton') }}
        </button>
        <button class="secondary" :disabled="isImportingRecipes" @click="recipesFileInput?.click()">
          <Upload :size="16" />{{ $t('account.recipesImportButton') }}
        </button>
        <input
          ref="recipesFileInput"
          type="file"
          accept=".zip,application/zip"
          hidden
          data-testid="recipes-import-input"
          @change="handleRecipesImport"
        />
      </div>
      <p v-if="recipesImportResult" class="muted" data-testid="recipes-import-result">
        {{
          $t('account.recipesImportResult', {
            created: recipesImportResult.created,
            skipped: recipesImportResult.skipped,
            errors: recipesImportResult.errors.length,
          })
        }}
      </p>
      <ul v-if="recipesImportResult?.errors.length" class="error">
        <li v-for="e in recipesImportResult.errors" :key="e.title">{{ e.title }} — {{ e.detail }}</li>
      </ul>
      <p v-if="recipesImportError" class="error">{{ recipesImportError }}</p>
    </div>

    <div class="card" style="margin-bottom: 1rem">
      <h2>{{ $t('account.shareTitle') }}</h2>
      <p class="muted">{{ $t('account.shareDescription') }}</p>
      <form @submit.prevent="handleShareSubmit">
        <div class="row">
          <div class="field" style="flex: 1; min-width: 200px">
            <label for="share-email">{{ $t('account.shareEmailLabel') }}</label>
            <input id="share-email" v-model="shareForm.email" type="email" required />
          </div>
          <div class="field">
            <label for="share-permission">{{ $t('account.sharePermissionLabel') }}</label>
            <select id="share-permission" v-model="shareForm.permission">
              <option value="read">{{ $t('account.sharePermissionRead') }}</option>
              <option value="write">{{ $t('account.sharePermissionWrite') }}</option>
            </select>
          </div>
        </div>
        <p v-if="shareMessage" class="muted">{{ shareMessage }}</p>
        <p v-if="shareError" class="error">{{ shareError }}</p>
        <button type="submit" :disabled="isSharing">{{ $t('account.shareButton') }}</button>
      </form>

      <h3 style="margin-top: 1.25rem">{{ $t('account.shareListTitle') }}</h3>
      <AsyncState v-if="!shares.length" :empty-text="$t('account.shareListEmpty')" />
      <ul v-else class="share-list">
        <li v-for="share in shares" :key="share.id">
          <span>
            {{ share.shared_with_username }} ({{ share.shared_with_email }}) —
            {{
              share.permission === 'read'
                ? $t('account.sharePermissionRead')
                : $t('account.sharePermissionWrite')
            }}
          </span>
          <button type="button" class="secondary" @click="handleRevokeShare(share)">
            {{ $t('account.shareRevoke') }}
          </button>
        </li>
      </ul>
    </div>

    <div class="card danger-zone">
      <h2>{{ $t('account.dangerZoneTitle') }}</h2>
      <p class="muted">{{ $t('account.deleteAccountDescription') }}</p>
      <label class="keep-recipes">
        <input v-model="keepRecipes" type="checkbox" data-testid="keep-recipes" />
        <span>{{ $t('account.keepRecipesLabel') }}</span>
      </label>
      <p v-if="deleteError" class="error">{{ deleteError }}</p>
      <button class="danger" data-testid="delete-account" @click="showDeleteConfirm = true">
        <Trash2 :size="16" />{{ $t('account.deleteAccountButton') }}
      </button>
    </div>

    <BaseModal
      v-if="showDeleteConfirm"
      :title="$t('account.deleteAccountConfirmTitle')"
      @close="showDeleteConfirm = false"
    >
      <p>{{ $t('account.deleteAccountConfirm') }}</p>
      <p v-if="keepRecipes" class="muted">{{ $t('account.keepRecipesLabel') }}</p>
      <p v-if="deleteError" class="error">{{ deleteError }}</p>
      <div class="row" style="margin-top: 1rem; justify-content: flex-end">
        <button type="button" class="secondary" @click="showDeleteConfirm = false">
          {{ $t('common.cancel') }}
        </button>
        <button
          type="button"
          class="danger"
          :disabled="isDeletingAccount"
          data-testid="delete-account-confirm"
          @click="handleDeleteAccount"
        >
          <Trash2 :size="16" />{{ $t('account.deleteAccountConfirmButton') }}
        </button>
      </div>
    </BaseModal>

    <p class="app-version">{{ $t('account.version', { version: appVersion }) }}</p>
  </div>
</template>

<style scoped>
/* Champs santé (régime, activité, allergies) : un fieldset désactivé tant que le consentement
   n'est pas donné, avec l'explication et l'action de consentement juste au-dessus. */
.health-fieldset {
  border: none;
  margin: 0;
  padding: 0;
  min-width: 0;
}

.health-fieldset:disabled .row,
.health-fieldset:disabled .allergen-fieldset {
  opacity: 0.55;
}

.health-locked {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 1rem;
  margin: 0.5rem 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: var(--color-primary-soft);
}

.health-locked p {
  margin: 0;
  flex: 1 1 18rem;
}

.allergen-fieldset {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin: 1rem 0;
  padding: 0.75rem 1rem;
}

.allergen-group {
  margin-top: 0.75rem;
}

.allergen-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1rem;
  margin-top: 0.4rem;
}

.allergen-option {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin: 0;
}

.allergen-option input {
  width: auto;
}

.accent-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.swatch {
  width: 2rem;
  height: 2rem;
  min-height: auto;
  padding: 0;
  border-radius: 999px;
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 1px var(--color-border);
}

.swatch:hover {
  background-blend-mode: normal;
  filter: brightness(0.92);
}

.swatch.is-selected {
  box-shadow: 0 0 0 2px var(--color-text);
}

.swatch-custom {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.swatch-custom input[type='color'] {
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}

.keep-recipes {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
  margin: 0.75rem 0;
  font-size: 0.9rem;
}

.keep-recipes input {
  width: auto;
  margin-top: 0.2rem;
  flex-shrink: 0;
}

.danger-zone {
  border: 1.5px solid var(--color-danger-soft);
}

.app-version {
  margin: 1.5rem 0 0;
  text-align: center;
  font-size: 0.75rem;
  color: var(--color-muted);
}

.share-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.share-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}
</style>
