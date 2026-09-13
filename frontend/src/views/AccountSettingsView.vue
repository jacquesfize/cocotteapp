<script setup lang="ts">
import { Download, Save, Trash2 } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { changePassword, exportMyData } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import { downloadBlob } from '../utils/download'
import type { ActivityLevel, DietType } from '../types/models'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const profile = ref<{
  username: string
  email: string
  diet_type: DietType
  activity_level: ActivityLevel
}>({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
  diet_type: authStore.user?.diet_type || 'omnivore',
  activity_level: authStore.user?.activity_level || 'moderate',
})
const profileMessage = ref('')
const profileError = ref('')
const isSavingProfile = ref(false)

async function handleProfileSubmit() {
  profileMessage.value = ''
  profileError.value = ''
  isSavingProfile.value = true
  try {
    await authStore.updateProfile(profile.value)
    profileMessage.value = t('account.profileSuccess')
  } catch (err) {
    const data = (err as { response?: { data?: { username?: string[] } } }).response?.data
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

const deleteError = ref('')

async function handleDeleteAccount() {
  if (!confirm(t('account.deleteAccountConfirm'))) return
  deleteError.value = ''
  try {
    await authStore.deleteAccount()
    router.push({ name: 'home' })
  } catch {
    deleteError.value = t('account.deleteAccountError')
  }
}
</script>

<template>
  <div>
    <h1>{{ $t('account.title') }}</h1>

    <div class="card" style="margin-bottom: 1rem">
      <h2>{{ $t('account.profileTitle') }}</h2>
      <form @submit.prevent="handleProfileSubmit">
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

    <div class="card" style="margin-bottom: 1rem">
      <h2>{{ $t('account.exportTitle') }}</h2>
      <p class="muted">{{ $t('account.exportDescription') }}</p>
      <button class="secondary" :disabled="isExporting" @click="handleExport">
        <Download :size="16" />{{ $t('account.exportButton') }}
      </button>
    </div>

    <div class="card danger-zone">
      <h2>{{ $t('account.dangerZoneTitle') }}</h2>
      <p class="muted">{{ $t('account.deleteAccountDescription') }}</p>
      <p v-if="deleteError" class="error">{{ deleteError }}</p>
      <button class="danger" @click="handleDeleteAccount">
        <Trash2 :size="16" />{{ $t('account.deleteAccountButton') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.danger-zone {
  border: 1.5px solid var(--color-danger-soft);
}
</style>
