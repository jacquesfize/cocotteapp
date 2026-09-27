<script setup lang="ts">
import { KeyRound } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import PageHeader from '../components/PageHeader.vue'
import { confirmPasswordReset } from '../api/auth'

const props = defineProps<{
  uid: string
  token: string
}>()

const { t } = useI18n()
const router = useRouter()

const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  error.value = ''
  if (newPassword.value !== confirmPassword.value) {
    error.value = t('account.passwordMismatch')
    return
  }
  isSubmitting.value = true
  try {
    await confirmPasswordReset({ uid: props.uid, token: props.token, new_password: newPassword.value })
    router.push({ name: 'login', query: { resetDone: 'true' } })
  } catch {
    error.value = t('auth.resetPasswordError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="card auth-card">
    <PageHeader :icon="KeyRound" :title="$t('auth.resetPasswordTitle')" />
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="new-password">{{ $t('account.newPassword') }}</label>
        <input
          id="new-password"
          v-model="newPassword"
          type="password"
          minlength="8"
          required
          autocomplete="new-password"
        />
      </div>
      <div class="field">
        <label for="confirm-password">{{ $t('account.confirmPassword') }}</label>
        <input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          minlength="8"
          required
          autocomplete="new-password"
        />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="isSubmitting">{{ $t('auth.resetPasswordButton') }}</button>
    </form>
  </div>
</template>

<style scoped>
.auth-card {
  max-width: 360px;
  margin: 2rem auto;
}
</style>
