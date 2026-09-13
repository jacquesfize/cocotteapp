<script setup>
import { ref } from 'vue'
import { requestPasswordReset } from '../api/auth'

const email = ref('')
const isSubmitting = ref(false)
const isDone = ref(false)

async function handleSubmit() {
  isSubmitting.value = true
  try {
    await requestPasswordReset(email.value)
  } finally {
    isSubmitting.value = false
    // Toujours le même message, que l'email corresponde à un compte ou non.
    isDone.value = true
  }
}
</script>

<template>
  <div class="card auth-card">
    <h1>{{ $t('auth.forgotPasswordTitle') }}</h1>

    <p v-if="isDone" class="muted">{{ $t('auth.forgotPasswordSent') }}</p>

    <form v-else @submit.prevent="handleSubmit">
      <p class="muted">{{ $t('auth.forgotPasswordDescription') }}</p>
      <div class="field">
        <label for="email">{{ $t('auth.email') }}</label>
        <input id="email" v-model="email" type="email" required autocomplete="email" />
      </div>
      <button type="submit" :disabled="isSubmitting">{{ $t('auth.forgotPasswordButton') }}</button>
    </form>

    <p class="muted">
      <RouterLink to="/login">{{ $t('auth.backToLogin') }}</RouterLink>
    </p>
  </div>
</template>

<style scoped>
.auth-card {
  max-width: 360px;
  margin: 2rem auto;
}
</style>
