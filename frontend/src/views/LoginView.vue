<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    await authStore.login(email.value, password.value)
    router.push((route.query.redirect as string) || { name: 'recipes' })
  } catch {
    error.value = t('auth.invalidCredentials')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="card auth-card">
    <h1>{{ $t('auth.loginTitle') }}</h1>
    <p v-if="route.query.resetDone === 'true'" class="muted">{{ $t('auth.resetPasswordSuccess') }}</p>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="email">{{ $t('auth.email') }}</label>
        <input id="email" v-model="email" type="email" required autocomplete="email" />
      </div>
      <div class="field">
        <label for="password">{{ $t('auth.password') }}</label>
        <input id="password" v-model="password" type="password" required autocomplete="current-password" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="isSubmitting">{{ $t('auth.loginButton') }}</button>
    </form>
    <p class="muted">
      <RouterLink to="/forgot-password">{{ $t('auth.forgotPassword') }}</RouterLink>
    </p>
    <p class="muted">
      {{ $t('auth.noAccount') }} <RouterLink to="/register">{{ $t('auth.signUp') }}</RouterLink>
    </p>
  </div>
</template>

<style scoped>
.auth-card {
  max-width: 360px;
  margin: 2rem auto;
}
</style>
